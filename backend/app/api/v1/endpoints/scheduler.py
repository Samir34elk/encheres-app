"""
Scheduler endpoints for triggering background jobs externally.
Used by GitHub Actions or external cron services.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings
from app.db.session import get_db, AsyncSessionLocal
from app.services.batch_scraper import BatchAuctionScraper
from app.services.sale_discovery import SaleDiscoveryService

router = APIRouter()
logger = logging.getLogger(__name__)


async def verify_cron_secret(x_cron_secret: str = Header(None)):
    """Verify the cron secret header for security"""
    # Get the secret from settings (should be set via environment variable)
    cron_secret = getattr(settings, 'CRON_SECRET', None)

    if not cron_secret:
        logger.error("CRON_SECRET not configured in settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scheduler not properly configured"
        )

    if not x_cron_secret or x_cron_secret != cron_secret:
        logger.warning(f"Invalid cron secret attempt: {x_cron_secret}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing cron secret"
        )


@router.post("/trigger-scraping")
async def trigger_scraping(
    _: None = Depends(verify_cron_secret)
):
    """
    Trigger the sales scraping job manually.
    This endpoint is called by GitHub Actions or external cron services.

    Headers:
        X-Cron-Secret: The secret key to authenticate the request

    Returns:
        Status and summary of the scraping job
    """
    logger.info("Scraping job triggered via API endpoint")

    async with AsyncSessionLocal() as db:
        try:
            batch = BatchAuctionScraper(db)
            summary = await batch.run()
            logger.info(f"Scraping completed successfully: {summary}")

            return {
                "status": "success",
                "job": "scraping",
                "summary": summary,
                "message": "Sales scraping completed successfully"
            }
        except Exception as e:
            logger.exception(f"Error during scraping job: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Scraping job failed: {str(e)}"
            )


@router.post("/trigger-discovery")
async def trigger_discovery(
    _: None = Depends(verify_cron_secret)
):
    """
    Trigger the sales discovery job manually.
    This endpoint is called by GitHub Actions or external cron services.

    Headers:
        X-Cron-Secret: The secret key to authenticate the request

    Returns:
        Status and summary of the discovery job
    """
    logger.info("Discovery job triggered via API endpoint")

    async with AsyncSessionLocal() as db:
        try:
            service = SaleDiscoveryService()
            sales = await service.fetch_sales()
            created, updated = await service.sync_with_database(db, sales)

            result = {
                "status": "success",
                "job": "discovery",
                "total_sales": len(sales),
                "created": created,
                "updated": updated,
                "message": f"Discovery completed: {created} new, {updated} updated"
            }

            logger.info(f"Discovery completed successfully: {result}")
            return result

        except Exception as e:
            logger.exception(f"Error during discovery job: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Discovery job failed: {str(e)}"
            )


@router.get("/jobs-status")
async def get_jobs_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of scheduled jobs.
    Returns information about last execution times.

    Note: This is a basic implementation. For production, consider storing
    job execution history in the database.
    """
    # TODO: Implement job execution history tracking in database
    # For now, return basic info

    return {
        "scheduler": "external (GitHub Actions)",
        "jobs": [
            {
                "name": "scrape_sales",
                "schedule": f"Every {settings.SCRAPER_INTERVAL_MINUTES} minutes",
                "endpoint": "/api/v1/scheduler/trigger-scraping"
            },
            {
                "name": "discover_sales",
                "schedule": "Daily at 03:00 UTC",
                "endpoint": "/api/v1/scheduler/trigger-discovery"
            }
        ],
        "note": "Job history tracking not yet implemented"
    }


@router.get("/diagnostic")
async def diagnostic(
    db: AsyncSession = Depends(get_db)
):
    """
    Diagnostic endpoint to check scraper configuration and environment.
    Returns information about the system, Playwright, and site accessibility.
    """
    import sys
    import platform
    from sqlalchemy import select, func
    from app.models.sale import Sale

    diagnostic_info = {
        "system": {
            "platform": platform.platform(),
            "python_version": sys.version,
        },
        "configuration": {
            "auction_base_url": settings.AUCTION_BASE_URL,
            "scraper_interval_minutes": settings.SCRAPER_INTERVAL_MINUTES,
            "sale_refresh_hours": settings.SALE_REFRESH_HOURS,
        },
        "database": {},
        "playwright": {},
        "recommendations": []
    }

    # Check database sales count
    try:
        result = await db.execute(select(func.count(Sale.id)))
        sales_count = result.scalar_one()
        diagnostic_info["database"]["sales_count"] = sales_count
        diagnostic_info["database"]["status"] = "connected"
    except Exception as e:
        diagnostic_info["database"]["status"] = "error"
        diagnostic_info["database"]["error"] = str(e)

    # Check Playwright installation
    try:
        from playwright.async_api import async_playwright
        diagnostic_info["playwright"]["installed"] = True

        # Try to get browser info
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                version = browser.version
                await browser.close()
                diagnostic_info["playwright"]["chromium_version"] = version
                diagnostic_info["playwright"]["status"] = "available"
        except Exception as e:
            diagnostic_info["playwright"]["status"] = "installed_but_not_functional"
            diagnostic_info["playwright"]["error"] = str(e)
            diagnostic_info["recommendations"].append(
                "Playwright is installed but cannot launch browser. "
                "On Render, you may need to install system dependencies. "
                "Add 'playwright install-deps chromium' to your build script."
            )
    except ImportError:
        diagnostic_info["playwright"]["installed"] = False
        diagnostic_info["playwright"]["status"] = "not_installed"
        diagnostic_info["recommendations"].append(
            "Playwright is not installed. Install it with: pip install playwright"
        )

    # Recommendations based on findings
    if diagnostic_info["database"].get("sales_count", 0) == 0:
        diagnostic_info["recommendations"].append(
            "Database has 0 sales. Run the discovery job first to populate sales."
        )

    return diagnostic_info


@router.get("/debug-scraper")
async def debug_scraper():
    """
    Debug endpoint to test the scraper and see what it finds.
    Returns detailed information about the scraping process.
    """
    from playwright.async_api import async_playwright
    from selectolax.parser import HTMLParser

    debug_info = {
        "url": f"{settings.AUCTION_BASE_URL}/ventes?page=1",
        "status": "unknown",
        "html_length": 0,
        "found_items": 0,
        "sample_items": [],
        "selectors_tried": {},
        "error": None
    }

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            # Navigate to the page
            await page.goto(debug_info["url"], wait_until="networkidle", timeout=30000)

            # Wait for JavaScript to render content
            try:
                await page.wait_for_selector(
                    "div.fr-list-product__item, div.fr-card, article, div[class*='product'], div[class*='vente']",
                    timeout=10000
                )
            except Exception:
                import asyncio
                await asyncio.sleep(3)  # Fallback delay if selectors not found

            html = await page.content()
            await browser.close()

            debug_info["html_length"] = len(html)
            debug_info["status"] = "page_loaded"

            # Parse HTML
            tree = HTMLParser(html)

            # Try the current selector
            items = tree.css("div.fr-list-product__item")
            debug_info["found_items"] = len(items)
            debug_info["selectors_tried"]["div.fr-list-product__item"] = len(items)

            # Try alternative selectors
            alt_selectors = [
                "div.fr-card",
                "div.product-item",
                "article",
                "div[class*='product']",
                "div[class*='sale']",
                "div[class*='vente']"
            ]

            for selector in alt_selectors:
                found = tree.css(selector)
                debug_info["selectors_tried"][selector] = len(found)

            # Get sample of first 3 items if any found
            if items:
                for idx, item in enumerate(items[:3]):
                    # Try to extract link
                    link = item.css_first("h3.fr-card-product__title a[href^='/vente/']")
                    title = link.text(strip=True) if link else "No title found"
                    href = link.attributes.get("href", "No href") if link else "No link"

                    debug_info["sample_items"].append({
                        "index": idx,
                        "title": title,
                        "href": href,
                        "html_snippet": str(item)[:500]  # First 500 chars
                    })
            else:
                # If no items found, get a sample of the HTML
                debug_info["html_sample"] = html[:2000]  # First 2000 chars

    except Exception as e:
        debug_info["status"] = "error"
        debug_info["error"] = str(e)
        logger.exception("Error in debug scraper: %s", e)

    return debug_info
