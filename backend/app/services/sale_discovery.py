import re
from dataclasses import dataclass, asdict
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
    location: Optional[str]
    sale_type: Optional[str]

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
                    html = await page.content()
                    tree = HTMLParser(html)
                    items = tree.css("div.fr-list-product__item")

                    if not items:
                        break

                    page_has_sale = False

                    for item in items:
                        link = item.css_first("h3.fr-card-product__title a[href^='/vente/']")
                        if not link:
                            continue

                        href = link.attributes.get("href", "")
                        match = re.search(r"/vente/(\d+)", href)
                        if not match:
                            continue

                        sale_number = int(match.group(1))
                        if sale_number in seen_numbers:
                            continue

                        title = link.text(strip=True)
                        lots_node = item.css_first("p.fr-card-product__desc span")
                        lots_count = self._extract_int(lots_node.text(strip=True)) if lots_node else 0

                        badge = item.css_first(".fr-badge")
                        status_label = badge.text(strip=True) if badge else None

                        sale_type_node = item.css_first(".fr-text-active-blue-france")
                        sale_type = sale_type_node.text(strip=True) if sale_type_node else None

                        location_node = item.css_first("li strong")
                        location = location_node.text(strip=True) if location_node else None

                        sales.append(
                            SaleSummary(
                                sale_number=sale_number,
                                title=title,
                                lots_count=lots_count or 0,
                                status_label=status_label,
                                url=f"{self.base_url}/vente/{sale_number}",
                                location=location,
                                sale_type=sale_type,
                            )
                        )
                        seen_numbers.add(sale_number)
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

            status_value = "cancelled" if sale_summary.status_label and "annul" in sale_summary.status_label.lower() else "active"

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
                if changed:
                    updated += 1
            else:
                sale = Sale(
                    sale_number=sale_summary.sale_number,
                    title=sale_summary.title,
                    description=f"Organisateur: {sale_summary.location}" if sale_summary.location else None,
                    status=status_value,
                    total_lots=sale_summary.lots_count,
                    url=sale_summary.url,
                    is_scraped=False,
                )
                db.add(sale)
                created += 1

        if created or updated:
            await db.commit()

        return created, updated
