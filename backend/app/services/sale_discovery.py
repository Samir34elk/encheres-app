import json
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Optional, Tuple

from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.sale import Sale


@dataclass
class SaleSummary:
    """Résumé d'une vente identifiée sur la liste publique."""

    sale_number: int
    title: str
    lots_count: int
    status_label: Optional[str]
    url: str
    organizer: Optional[str]
    sale_type: Optional[str]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class SaleDiscoveryService:
    """Scraper pour découvrir les ventes et leurs numéros."""

    def __init__(self, base_url: str = settings.AUCTION_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.list_path = "/ventes"

    @staticmethod
    def _extract_int(text: str) -> Optional[int]:
        match = re.search(r"\d+", text.replace(" ", "")) if text else None
        return int(match.group()) if match else None

    @staticmethod
    def _parse_datetime(text: Optional[str]) -> Optional[datetime]:
        if not text:
            return None

        date_match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
        if not date_match:
            return None

        time_match = re.search(r"(\d{1,2})[hH](\d{2})", text)
        if not time_match:
            time_match = re.search(r"(\d{1,2}):(\d{2})", text)
        hours = int(time_match.group(1)) if time_match else 0
        minutes = int(time_match.group(2)) if time_match else 0

        try:
            return datetime.strptime(
                f"{date_match.group(1)} {hours:02d}:{minutes:02d}",
                "%d/%m/%Y %H:%M"
            )
        except ValueError:
            return None

    @staticmethod
    def _map_status(label: Optional[str]) -> str:
        if not label:
            return "active"

        status = label.lower()
        if "annul" in status:
            return "cancelled"
        if "venir" in status or "ouvre" in status or "bientôt" in status:
            return "upcoming"
        if "termin" in status or "clôtur" in status or "fermée" in status:
            return "closed"
        return "active"

    @staticmethod
    def _build_description(summary: SaleSummary) -> Optional[str]:
        metadata = {}

        if summary.organizer:
            metadata["organizer"] = summary.organizer
        if summary.sale_type:
            metadata["sale_type"] = summary.sale_type
        if summary.tags:
            metadata["tags"] = summary.tags
        if summary.status_label:
            metadata["status_label"] = summary.status_label

        return json.dumps(metadata, ensure_ascii=False, sort_keys=True) if metadata else None

    def _parse_sale_item(self, item: HTMLParser) -> Optional[SaleSummary]:
        link = item.css_first("h3.fr-card-product__title a[href^='/vente/']")
        if not link:
            return None

        href = link.attributes.get("href", "")
        match = re.search(r"/vente/(\d+)", href)
        if not match:
            return None

        sale_number = int(match.group(1))
        title = link.text(strip=True)

        lots_node = item.css_first("p.fr-card-product__desc span")
        lots_count = self._extract_int(lots_node.text(strip=True)) if lots_node else 0

        badge = item.css_first(".fr-badge")
        status_label = badge.text(strip=True) if badge else None

        sale_type_node = item.css_first(".fr-text-active-blue-france")
        sale_type = sale_type_node.text(strip=True) if sale_type_node else None

        tags = [
            tag.text(strip=True)
            for tag in item.css("ul.fr-tags-group p.fr-tag")
            if tag.text(strip=True)
        ]

        organizer = None
        start_date = None
        end_date = None

        info_items = item.css("div.fr-card-product__content-last ul.fr-list li")
        for info_item in info_items:
            label_node = info_item.css_first("span.fr-text-mention-grey")
            label_text = label_node.text(strip=True) if label_node else ""
            label_lower = label_text.lower()
            strong_node = info_item.css_first("strong")
            strong_text = strong_node.text(strip=True) if strong_node else None
            raw_text = info_item.text(strip=True)

            if "organisateur" in label_lower or "organisateur" in raw_text.lower():
                organizer = strong_text or raw_text.replace(label_text, "").strip()
            elif any(keyword in label_lower for keyword in ["clôture", "date limite", "fin des offres", "fermeture"]):
                end_date = self._parse_datetime(strong_text or raw_text)
            elif any(keyword in label_lower for keyword in ["débute", "ouvre", "ouverture", "début"]):
                start_date = self._parse_datetime(strong_text or raw_text)

        return SaleSummary(
            sale_number=sale_number,
            title=title,
            lots_count=lots_count or 0,
            status_label=status_label,
            url=f"{self.base_url}/vente/{sale_number}",
            organizer=organizer,
            sale_type=sale_type,
            start_date=start_date,
            end_date=end_date,
            tags=tags,
        )

    async def fetch_sales(self, max_pages: Optional[int] = None) -> List[SaleSummary]:
        """Récupère toutes les ventes listées sur le site."""
        sales: List[SaleSummary] = []
        seen_numbers: set[int] = set()
        page_number = 1

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            try:
                while True:
                    if max_pages and page_number > max_pages:
                        break

                    url = f"{self.base_url}{self.list_path}?page={page_number}"
                    await page.goto(url, wait_until="networkidle", timeout=30000)

                    # Wait for JavaScript to render content
                    # Try to wait for common selectors, with a fallback delay
                    try:
                        # Wait for any of these selectors (whichever appears first)
                        await page.wait_for_selector(
                            "div.fr-list-product__item, div.fr-card, article, div[class*='product'], div[class*='vente']",
                            timeout=10000
                        )
                    except Exception:
                        # If no selector found, wait a bit for JS to finish
                        import asyncio
                        await asyncio.sleep(3)

                    html = await page.content()
                    tree = HTMLParser(html)
                    items = tree.css("div.fr-list-product__item")

                    if not items:
                        break

                    page_has_sale = False

                    for item in items:
                        summary = self._parse_sale_item(item)
                        if not summary:
                            continue

                        if summary.sale_number in seen_numbers:
                            continue

                        sales.append(summary)
                        seen_numbers.add(summary.sale_number)
                        page_has_sale = True

                    if not page_has_sale:
                        break

                    page_number += 1
            finally:
                await browser.close()

        return sales

    async def sync_with_database(
        self,
        db: AsyncSession,
        sales: List[SaleSummary]
    ) -> Tuple[int, int]:
        """Crée ou met à jour les ventes en base de données."""
        created = 0
        updated = 0

        for sale_summary in sales:
            result = await db.execute(
                select(Sale).where(Sale.sale_number == sale_summary.sale_number)
            )
            sale = result.scalar_one_or_none()

            status_value = self._map_status(sale_summary.status_label)
            description_value = self._build_description(sale_summary)

            if sale:
                changed = False
                if sale.title != sale_summary.title:
                    sale.title = sale_summary.title
                    changed = True
                if sale.status != status_value:
                    sale.status = status_value
                    changed = True
                if sale.total_lots != sale_summary.lots_count:
                    sale.total_lots = sale_summary.lots_count
                    changed = True
                if sale.url != sale_summary.url:
                    sale.url = sale_summary.url
                    changed = True
                if sale.start_date != sale_summary.start_date:
                    sale.start_date = sale_summary.start_date
                    changed = True
                if sale.end_date != sale_summary.end_date:
                    sale.end_date = sale_summary.end_date
                    changed = True
                if sale.description != description_value:
                    sale.description = description_value
                    changed = True
                if changed:
                    updated += 1
            else:
                sale = Sale(
                    sale_number=sale_summary.sale_number,
                    title=sale_summary.title,
                    description=description_value,
                    status=status_value,
                    total_lots=sale_summary.lots_count,
                    url=sale_summary.url,
                    start_date=sale_summary.start_date,
                    end_date=sale_summary.end_date,
                    is_scraped=False,
                )
                db.add(sale)
                created += 1

        if created or updated:
            await db.commit()

        return created, updated
