from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.scheduler import jobs
from app.services.polite_client import ScraperPausedError


def sale(number, status, end_in, scraped_ago):
    now = datetime.utcnow()
    return SimpleNamespace(
        id=number, sale_number=number, status=status,
        end_date=now + end_in,
        last_scraped_at=None if scraped_ago is None else now - scraped_ago,
        is_scraped=scraped_ago is not None,
    )


def fake_session(sales):
    db = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = sales
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=db)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=ctx)


async def run_job(sales, **kw):
    lot_scraper = MagicMock()
    lot_scraper.sync_auction_lots = AsyncMock(
        side_effect=kw.get("lot_side_effect"), return_value={"total": 10}
    )
    auction_scraper = MagicMock()
    auction_scraper.sync_auctions = AsyncMock(return_value={"total": len(sales)})
    client = MagicMock()
    client.is_paused.return_value = False
    client.status.return_value = {}
    client.requests_today = 0
    with patch.object(jobs, "AsyncSessionLocal", fake_session(sales)), \
         patch.object(jobs, "GraphQLLotScraper", return_value=lot_scraper), \
         patch.object(jobs, "GraphQLAuctionScraper", return_value=auction_scraper), \
         patch.object(jobs, "polite_client", client), \
         patch.object(jobs.settings, "MAX_SALES_PER_RUN", kw.get("max_sales", 15)):
        service = jobs.SchedulerService()
        summary = await service.scrape_sales_job()
    scraped = [c.kwargs["auction_id"] for c in lot_scraper.sync_auction_lots.call_args_list]
    return summary, scraped, auction_scraper


async def test_only_due_sales_are_scraped_most_urgent_first():
    sales = [
        sale(1, "closed", -timedelta(days=60), timedelta(days=59)),   # finalisée
        sale(2, "active", timedelta(days=5), timedelta(hours=1)),     # pas encore due
        sale(3, "active", timedelta(days=5), timedelta(hours=7)),     # due (6h)
        sale(4, "active", timedelta(hours=1), timedelta(minutes=20)), # finit bientôt
        sale(5, "upcoming", timedelta(days=20), None),                # jamais scrapée
    ]
    summary, scraped, auction_scraper = await run_job(sales)

    assert summary["status"] == "success"
    assert scraped == ["4", "5", "3"]
    auction_scraper.sync_auctions.assert_awaited_once_with(incremental=True)
    assert sales[3].last_scraped_at > datetime.utcnow() - timedelta(minutes=1)


async def test_respects_max_sales_per_run():
    sales = [sale(n, "active", timedelta(days=5), None) for n in range(1, 40)]
    _, scraped, _ = await run_job(sales, max_sales=5)
    assert len(scraped) == 5


async def test_stops_immediately_when_blocked():
    sales = [sale(n, "active", timedelta(days=5), None) for n in range(1, 10)]
    summary, scraped, _ = await run_job(
        sales, lot_side_effect=ScraperPausedError("HTTP 403")
    )
    assert summary["status"] == "paused"
    assert len(scraped) == 1
