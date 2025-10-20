import re
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.config import settings
from app.models.lot import Lot
from app.models.sale import Sale
from app.models.price_history import PriceHistory
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class AuctionScraper:
    """Scraper service for fetching auction data"""

    def __init__(self, db: AsyncSession, sale_number: int = None):
        self.db = db
        self.base_url = settings.AUCTION_BASE_URL
        self.sale_number = sale_number or settings.AUCTION_SALE_NUMBER
        self.notification_service = NotificationService(db)
        self.sale_id = None

    @staticmethod
    def extract_number(text: str) -> int:
        """Extract the first integer from text"""
        if not text:
            return None
        match = re.search(r'\d+', text.replace(' ', ''))
        return int(match.group()) if match else None

    async def ensure_sale_exists(self) -> int:
        """Create or get the sale record for this sale_number"""
        # Check if sale exists
        result = await self.db.execute(
            select(Sale).where(Sale.sale_number == self.sale_number)
        )
        sale = result.scalar_one_or_none()

        if not sale:
            # Create new sale record
            sale = Sale(
                sale_number=self.sale_number,
                title=f"Vente {self.sale_number}",
                description=f"Vente aux enchères du domaine n°{self.sale_number}",
                url=f"{self.base_url}/vente/{self.sale_number}",
                status="active"
            )
            self.db.add(sale)
            await self.db.flush()
            logger.info(f"Created new sale record for sale #{self.sale_number}")
        else:
            logger.info(f"Using existing sale record (ID: {sale.id}) for sale #{self.sale_number}")

        self.sale_id = sale.id
        return sale.id

    async def scrape_page(self, page_number: int) -> List[Dict[str, Any]]:
        """Scrape a single page of auction listings"""
        url = f"{self.base_url}/vente/{self.sale_number}?page={page_number}"
        logger.info(f"Scraping page {page_number}: {url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Wait for JavaScript to render content (same fix as sale_discovery)
                try:
                    await page.wait_for_selector(
                        "ul.fr-list-product, div.fr-list-product__item, div.fr-card",
                        timeout=10000
                    )
                except Exception:
                    await asyncio.sleep(3)  # Fallback delay if selectors not found

                html = await page.content()

                tree = HTMLParser(html)
                ul = tree.css_first("ul.fr-list-product")

                if not ul:
                    logger.info(f"No listings found on page {page_number}")
                    return []

                items = []
                for item in ul.css("div.fr-list-product__item"):
                    # Title and URL
                    title_node = item.css_first("h3.fr-card-product__title a")
                    title = title_node.text(strip=True) if title_node else "N/A"
                    lot_url = self.base_url + title_node.attributes.get("href", "") if title_node else "N/A"

                    # Lot number
                    lot_node = item.css_first("p.fr-card-product__desc span")
                    lot_number = self.extract_number(lot_node.text(strip=True)) if lot_node else None

                    # Price and status
                    price_node = item.css_first("p.fr-price__price")
                    price = self.extract_number(price_node.text(strip=True)) if price_node else None
                    status_node = item.css_first("p.fr-price__text")
                    status = status_node.text(strip=True) if status_node else "N/A"

                    # Depot location
                    depot_node = item.css_first("p.fr-text--xs strong")
                    depot = depot_node.text(strip=True) if depot_node else "N/A"

                    # Image
                    img_node = item.css_first("div.fr-card-product__img img")
                    img_url = img_node.attributes.get("src", "") if img_node else "N/A"

                    # Description
                    desc_node = item.css_first("div.fr-text--sm.fr-ellipsis--3 p")
                    description = desc_node.text(strip=True) if desc_node else "N/A"

                    if lot_number:
                        items.append({
                            "lot_number": lot_number,
                            "title": title,
                            "price": price,
                            "status": status,
                            "depot_location": depot,
                            "url": lot_url,
                            "image_url": img_url,
                            "description": description
                        })

                return items

            except Exception as e:
                logger.error(f"Error scraping page {page_number}: {str(e)}")
                return []
            finally:
                await browser.close()

    async def scrape_all_pages(self) -> List[Dict[str, Any]]:
        """Scrape all pages of auction listings"""
        all_items = []
        page_number = 1

        while True:
            items = await self.scrape_page(page_number)
            if not items:
                break
            all_items.extend(items)
            page_number += 1
            await asyncio.sleep(1)  # Be polite to the server

        logger.info(f"Total items scraped: {len(all_items)}")
        return all_items

    async def update_database(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Update database with scraped items"""
        stats = {"new": 0, "updated": 0, "price_changes": 0}

        for item_data in items:
            # Check if lot exists for this sale
            result = await self.db.execute(
                select(Lot).where(
                    Lot.lot_number == item_data["lot_number"],
                    Lot.sale_id == self.sale_id
                )
            )
            existing_lot = result.scalar_one_or_none()

            if existing_lot:
                # Update existing lot
                previous_price = existing_lot.price
                price_changed = previous_price != item_data["price"]

                existing_lot.title = item_data["title"]
                existing_lot.description = item_data["description"]
                existing_lot.price = item_data["price"]
                existing_lot.status = item_data["status"]
                existing_lot.depot_location = item_data["depot_location"]
                existing_lot.url = item_data["url"]
                existing_lot.image_url = item_data["image_url"]
                existing_lot.last_updated = datetime.utcnow()
                existing_lot.is_active = 1

                stats["updated"] += 1

                # Track price change
                if price_changed and item_data["price"] is not None:
                    price_history = PriceHistory(
                        lot_id=existing_lot.id,
                        price=item_data["price"],
                        status=item_data["status"]
                    )
                    self.db.add(price_history)
                    stats["price_changes"] += 1

                    # Trigger price alerts
                    await self.notification_service.trigger_price_alerts(
                        existing_lot,
                        item_data["price"],
                        previous_price=previous_price
                    )
            else:
                # Create new lot
                new_lot = Lot(**item_data, sale_id=self.sale_id)
                self.db.add(new_lot)
                await self.db.flush()  # Get the ID

                # Add initial price history
                if item_data.get("price"):
                    price_history = PriceHistory(
                        lot_id=new_lot.id,
                        price=item_data["price"],
                        status=item_data["status"]
                    )
                    self.db.add(price_history)

                stats["new"] += 1

                # Trigger new lot alerts
                await self.notification_service.trigger_new_lot_alerts(new_lot)
                await self.notification_service.trigger_price_alerts(
                    new_lot,
                    item_data.get("price"),
                    previous_price=None
                )

        await self.db.commit()
        logger.info(f"Database update stats: {stats}")
        return stats

    async def run(self) -> Dict[str, int]:
        """Main scraper execution"""
        logger.info(f"Starting auction scraper for sale #{self.sale_number}")

        # Ensure sale exists
        await self.ensure_sale_exists()

        # Scrape all pages
        items = await self.scrape_all_pages()

        # Update database
        stats = await self.update_database(items)

        # Update sale metadata
        result = await self.db.execute(
            select(Sale).where(Sale.id == self.sale_id)
        )
        sale = result.scalar_one_or_none()
        if sale:
            sale.total_lots = len(items)
            sale.is_scraped = True
            sale.last_scraped_at = datetime.utcnow()
            await self.db.commit()

        logger.info(f"Scraper completed for sale #{self.sale_number}: {stats}")
        return stats
