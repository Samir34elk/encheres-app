"""
Scheduler endpoints for triggering background jobs externally.
Used by GitHub Actions or external cron services.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.config import settings
from app.db.session import get_db, AsyncSessionLocal
from app.services.graphql_scraper import GraphQLAuctionScraper
from app.services.graphql_lot_scraper import GraphQLLotScraper
from app.scheduler.jobs import SchedulerService

router = APIRouter()
logger = logging.getLogger(__name__)

SCRAPER_DISABLED_MESSAGE = "Internal scraping is disabled. Use the ingestion workflow instead."


def get_scheduler() -> SchedulerService:
    """Expose the running scheduler instance (configured in app.main)."""
    try:
        from app.main import scheduler
        return scheduler
    except Exception as exc:  # pragma: no cover
        logger.error("Scheduler not available: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scheduler not available"
        )


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
    Trigger the GraphQL sales scraping job manually.
    This endpoint is called by GitHub Actions or external cron services.

    Headers:
        X-Cron-Secret: The secret key to authenticate the request

    Returns:
        Status and summary of the scraping job
    """
    if not settings.ENABLE_INTERNAL_SCRAPER:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=SCRAPER_DISABLED_MESSAGE,
        )
    logger.info("GraphQL scraping job triggered via API endpoint")

    async with AsyncSessionLocal() as db:
        try:
            # Étape 1: Scraper les ventes
            auction_scraper = GraphQLAuctionScraper(db)
            stats_ventes = await auction_scraper.sync_auctions(
                filter_status="incoming",
                max_pages=None
            )
            logger.info(f"Ventes synchronisées : {stats_ventes}")

            # Étape 2: Scraper les lots pour les ventes actives
            lot_scraper = GraphQLLotScraper(db)
            from shared.models.sale import Sale

            result = await db.execute(
                select(Sale)
                .where(Sale.status == "active")
                .order_by(Sale.start_date.desc())
                .limit(50)
            )
            sales = result.scalars().all()

            total_lots = 0
            for sale in sales:
                try:
                    stats_lots = await lot_scraper.sync_auction_lots(
                        auction_id=str(sale.sale_number),
                        sale_id=sale.id,
                        fetch_full_details=False
                    )
                    total_lots += stats_lots.get('total_processed', 0)
                except Exception as e:
                    logger.error(f"Error scraping sale #{sale.sale_number}: {e}")

            await auction_scraper.close()
            await lot_scraper.close()

            summary = {
                "ventes": stats_ventes,
                "sales_processed": len(sales),
                "lots_synchronized": total_lots
            }

            logger.info(f"GraphQL scraping completed successfully: {summary}")

            return {
                "status": "success",
                "job": "graphql-scraping",
                "summary": summary,
                "message": f"GraphQL scraping completed: {len(sales)} ventes, {total_lots} lots"
            }
        except Exception as e:
            logger.exception(f"Error during GraphQL scraping job: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"GraphQL scraping job failed: {str(e)}"
            )


@router.post("/trigger-discovery")
async def trigger_discovery(
    _: None = Depends(verify_cron_secret)
):
    """
    Trigger the GraphQL sales discovery job manually.
    This endpoint is called by GitHub Actions or external cron services.

    Headers:
        X-Cron-Secret: The secret key to authenticate the request

    Returns:
        Status and summary of the discovery job
    """
    if not settings.ENABLE_INTERNAL_SCRAPER:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=SCRAPER_DISABLED_MESSAGE,
        )
    logger.info("GraphQL discovery job triggered via API endpoint")

    async with AsyncSessionLocal() as db:
        try:
            scraper = GraphQLAuctionScraper(db)
            stats = await scraper.sync_auctions(
                filter_status=None,  # Toutes les ventes
                max_pages=None
            )
            await scraper.close()

            result = {
                "status": "success",
                "job": "graphql-discovery",
                "stats": stats,
                "message": f"GraphQL discovery completed: {stats}"
            }

            logger.info(f"GraphQL discovery completed successfully: {result}")
            return result

        except Exception as e:
            logger.exception(f"Error during GraphQL discovery job: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"GraphQL discovery job failed: {str(e)}"
            )


@router.post("/force-scrape-sale/{sale_number}")
async def force_scrape_sale(
    sale_number: int,
    _: None = Depends(verify_cron_secret)
):
    """
    Force scrape a specific sale using GraphQL.
    Useful for testing or manual triggers.

    Headers:
        X-Cron-Secret: The secret key to authenticate the request

    Returns:
        Status and details of the scraping operation
    """
    if not settings.ENABLE_INTERNAL_SCRAPER:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=SCRAPER_DISABLED_MESSAGE,
        )

    logger.info(f"Force scraping sale #{sale_number} via GraphQL API endpoint")

    async with AsyncSessionLocal() as db:
        try:
            from shared.models.sale import Sale

            # Trouver la vente par sale_number
            result = await db.execute(
                select(Sale).where(Sale.sale_number == sale_number)
            )
            sale = result.scalar_one_or_none()

            if not sale:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sale {sale_number} not found in database"
                )

            # Scraper les lots de cette vente via GraphQL
            lot_scraper = GraphQLLotScraper(db)
            stats = await lot_scraper.sync_auction_lots(
                auction_id=str(sale_number),
                sale_id=sale.id,
                fetch_full_details=True  # Détails complets pour force scrape
            )
            await lot_scraper.close()

            result = {
                "status": "success",
                "sale_number": sale_number,
                "stats": stats,
                "message": f"Sale {sale_number} scraped successfully via GraphQL"
            }

            logger.info(f"GraphQL force scrape completed: {result}")
            return result

        except Exception as e:
            logger.exception(f"Error during GraphQL force scrape of sale #{sale_number}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"GraphQL scraping sale {sale_number} failed: {str(e)}"
            )


@router.post("/force-scrape-all")
async def force_scrape_all(
    _: None = Depends(verify_cron_secret)
):
    """
    Force scrape ALL sales using GraphQL.
    Useful after fixing bugs or for bulk updates.

    Headers:
        X-Cron-Secret: The secret key to authenticate the request

    Returns:
        Status and summary of all scraping operations
    """
    if not settings.ENABLE_INTERNAL_SCRAPER:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=SCRAPER_DISABLED_MESSAGE,
        )
    from shared.models.sale import Sale

    logger.info("Force scraping ALL sales via GraphQL API endpoint")

    async with AsyncSessionLocal() as db:
        try:
            # Étape 1: Sync toutes les ventes depuis l'API
            auction_scraper = GraphQLAuctionScraper(db)
            stats_ventes = await auction_scraper.sync_auctions(
                filter_status=None,  # Toutes les ventes
                max_pages=None
            )
            await auction_scraper.close()

            # Étape 2: Get all sales from database
            result = await db.execute(select(Sale))
            sales = result.scalars().all()

            # Étape 3: Scraper les lots pour toutes les ventes
            lot_scraper = GraphQLLotScraper(db)

            summary = {
                "status": "success",
                "ventes_synced": stats_ventes,
                "total_sales": len(sales),
                "processed": 0,
                "success": 0,
                "failed": 0,
                "total_lots": 0,
                "details": []
            }

            for sale in sales:
                summary["processed"] += 1
                logger.info(f"GraphQL scraping sale #{sale.sale_number}")

                try:
                    stats = await lot_scraper.sync_auction_lots(
                        auction_id=str(sale.sale_number),
                        sale_id=sale.id,
                        fetch_full_details=False  # Mode rapide
                    )
                    summary["success"] += 1
                    summary["total_lots"] += stats.get('total_processed', 0)
                    summary["details"].append({
                        "sale_number": sale.sale_number,
                        "stats": stats
                    })
                except Exception as e:
                    logger.exception(f"Error scraping sale #{sale.sale_number}: {e}")
                    summary["failed"] += 1

            await lot_scraper.close()

            logger.info(f"GraphQL force scrape all completed: {summary}")
            return summary

        except Exception as e:
            logger.exception(f"Error during GraphQL force scrape all: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"GraphQL force scrape all failed: {str(e)}"
            )


@router.get("/jobs-status")
async def get_jobs_status(
    _: None = Depends(verify_cron_secret),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """
    Return real-time information about the internal scheduler jobs.
    Includes job id, name, trigger and next run time.
    """
    jobs = [{
        "id": job.id,
        "name": job.name,
        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        "trigger": str(job.trigger)
    } for job in scheduler.get_jobs()]

    return {
        "scheduler": "internal",
        "jobs": jobs
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
