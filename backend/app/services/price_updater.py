import logging
from typing import List, Dict
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.lot import Lot
from app.models.favorite import Favorite
from app.models.price_history import PriceHistory
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class FavoritePriceUpdater:
    """Service to update prices for favorited lots by scraping their official URLs"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)

    async def get_favorited_lots_with_urls(self) -> List[Lot]:
        """Fetch all lots that have been favorited by at least one user and have a URL"""
        result = await self.db.execute(
            select(Lot)
            .join(Favorite, Favorite.lot_id == Lot.id)
            .where(Lot.url.isnot(None))
            .where(Lot.url != "")
            .where(Lot.url != "N/A")
            .where(Lot.is_active == 1)
            .distinct()
        )
        lots = result.scalars().all()
        logger.info(f"Found {len(lots)} favorited lots with URLs to update")
        return lots

    async def scrape_price_from_url(self, url: str) -> Dict:
        """Scrape the current price and status from a lot URL using Playwright"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    ignore_https_errors=True
                )
                page = await context.new_page()

                try:
                    # Navigate to the lot page
                    await page.goto(url, wait_until="networkidle", timeout=15000)

                    # Wait for the price element to be visible
                    await page.wait_for_selector("p.fr-price__price", timeout=5000)

                    # Extract price text
                    price_text = await page.locator("p.fr-price__price").text_content()
                    price_text = price_text.strip() if price_text else None

                    # Extract price number
                    price = None
                    if price_text:
                        # Remove non-numeric characters except spaces
                        import re
                        clean_price = re.sub(r'[^\d\s]', '', price_text)
                        clean_price = clean_price.replace(' ', '')
                        if clean_price:
                            try:
                                price = int(clean_price)
                            except ValueError:
                                logger.warning(f"Could not parse price '{price_text}' for {url}")

                    # Try to extract status if available
                    status = None
                    try:
                        status_elem = await page.locator(".fr-badge, .fr-card-product__status").first.text_content(timeout=2000)
                        status = status_elem.strip() if status_elem else None
                    except:
                        pass  # Status element might not exist

                    await browser.close()

                    return {
                        "price": price,
                        "status": status,
                        "success": True,
                        "error": None
                    }

                except PlaywrightTimeoutError:
                    await browser.close()
                    logger.warning(f"Timeout while scraping {url}")
                    return {"price": None, "status": None, "success": False, "error": "timeout"}

                except Exception as e:
                    await browser.close()
                    logger.error(f"Error scraping {url}: {e}")
                    return {"price": None, "status": None, "success": False, "error": str(e)}

        except Exception as e:
            logger.error(f"Failed to initialize browser for {url}: {e}")
            return {"price": None, "status": None, "success": False, "error": str(e)}

    async def update_lot_price(self, lot: Lot) -> bool:
        """Update a single lot's price and return True if changed"""
        if not lot.url or lot.url in ["", "N/A"]:
            return False

        logger.info(f"Checking price for lot {lot.id} ({lot.title})")

        scraped_data = await self.scrape_price_from_url(lot.url)

        if not scraped_data["success"]:
            logger.warning(f"Failed to scrape lot {lot.id}: {scraped_data.get('error')}")
            return False

        new_price = scraped_data["price"]
        new_status = scraped_data["status"]

        # Check if price has changed
        price_changed = False
        if new_price is not None and new_price != lot.price:
            old_price = lot.price
            lot.price = new_price
            lot.last_updated = datetime.utcnow()
            price_changed = True

            # Record price history
            price_history = PriceHistory(
                lot_id=lot.id,
                price=new_price,
                status=new_status or lot.status,
                recorded_at=datetime.utcnow()
            )
            self.db.add(price_history)

            logger.info(f"Price changed for lot {lot.id}: {old_price} → {new_price}")

            # Trigger notifications for users who favorited this lot
            try:
                await self.notification_service.notify_price_change(lot, old_price, new_price)
            except Exception as e:
                logger.error(f"Failed to send notifications for lot {lot.id}: {e}")

        # Update status if available and changed
        if new_status and new_status != lot.status:
            lot.status = new_status
            lot.last_updated = datetime.utcnow()
            logger.info(f"Status updated for lot {lot.id}: {lot.status} → {new_status}")

        return price_changed

    async def run(self) -> Dict:
        """Main method to update all favorited lots' prices"""
        logger.info("Starting favorited lots price update job")

        lots = await self.get_favorited_lots_with_urls()

        if not lots:
            logger.info("No favorited lots with URLs found")
            return {"total": 0, "updated": 0, "errors": 0}

        updated_count = 0
        error_count = 0

        for lot in lots:
            try:
                price_changed = await self.update_lot_price(lot)
                if price_changed:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Unexpected error updating lot {lot.id}: {e}")
                error_count += 1

        # Commit all changes
        try:
            await self.db.commit()
            logger.info(f"Price update job completed: {updated_count}/{len(lots)} prices updated")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to commit price updates: {e}")
            error_count += len(lots)

        return {
            "total": len(lots),
            "updated": updated_count,
            "errors": error_count,
            "timestamp": datetime.utcnow().isoformat()
        }
