import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lot import Lot
from app.models.price_history import PriceHistory
from app.models.sale import Sale
from app.services.notification_service import NotificationService
from app.schemas.ingestion import (
    IngestLotPayload,
    IngestSalePayload,
    SaleMetadataBatchRequest,
    SaleMetadataPayload,
)

logger = logging.getLogger(__name__)


class AuctionDataIngestionService:
    """Service dédié à l'ingestion des données de ventes et de lots."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notifications = NotificationService(db)

    async def _get_sale(self, sale_number: int) -> Optional[Sale]:
        result = await self.db.execute(
            select(Sale).where(Sale.sale_number == sale_number)
        )
        return result.scalar_one_or_none()

    async def _upsert_sale(self, payload: IngestSalePayload) -> Sale:
        sale = await self._get_sale(payload.sale_number)
        updated_fields: Dict[str, Any] = {}

        if sale:
            if payload.title and payload.title != sale.title:
                sale.title = payload.title
                updated_fields["title"] = payload.title
            if payload.description is not None and payload.description != sale.description:
                sale.description = payload.description
                updated_fields["description"] = payload.description
            if payload.status and payload.status != sale.status:
                sale.status = payload.status
                updated_fields["status"] = payload.status
            if payload.url and payload.url != sale.url:
                sale.url = payload.url
                updated_fields["url"] = payload.url
            if payload.start_date is not None and payload.start_date != sale.start_date:
                sale.start_date = payload.start_date
                updated_fields["start_date"] = payload.start_date
            if payload.end_date is not None and payload.end_date != sale.end_date:
                sale.end_date = payload.end_date
                updated_fields["end_date"] = payload.end_date
        else:
            sale = Sale(
                sale_number=payload.sale_number,
                title=payload.title or f"Vente {payload.sale_number}",
                description=payload.description,
                status=payload.status or "active",
                url=payload.url,
                start_date=payload.start_date,
                end_date=payload.end_date,
                total_lots=0,
                is_scraped=True,
            )
            self.db.add(sale)
            await self.db.flush()
            logger.info("Created sale #%s during ingestion", payload.sale_number)

        return sale

    async def ingest_sale(self, payload: IngestSalePayload) -> Dict[str, Any]:
        """
        Ingest data for a single sale, updating metadata and associated lots.
        Returns statistics about the operation.
        """
        if not payload.lots:
            logger.warning("Ingestion payload for sale #%s contains no lots", payload.sale_number)

        sale = await self._upsert_sale(payload)
        await self.db.flush()

        # Fetch existing lots for this sale
        existing_lots_by_number: Dict[int, Lot] = {}
        if sale.id:
            result = await self.db.execute(
                select(Lot).where(Lot.sale_id == sale.id)
            )
            for lot in result.scalars().all():
                existing_lots_by_number[lot.lot_number] = lot

        stats: Dict[str, Any] = {
            "sale_number": payload.sale_number,
            "total_lots_received": len(payload.lots),
            "new_lots": 0,
            "updated_lots": 0,
            "price_changes": 0,
            "deactivated_lots": 0,
            "errors": [],
        }

        ingested_numbers = set()

        for lot_payload in payload.lots:
            try:
                lot_stats = await self._upsert_lot(sale, lot_payload, existing_lots_by_number)
                for key, value in lot_stats.items():
                    stats[key] = stats.get(key, 0) + value
                ingested_numbers.add(lot_payload.lot_number)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception(
                    "Error ingesting lot #%s for sale #%s: %s",
                    lot_payload.lot_number,
                    payload.sale_number,
                    exc,
                )
                stats["errors"].append(
                    {"lot_number": lot_payload.lot_number, "error": str(exc)}
                )

        # Deactivate missing lots if requested
        if payload.deactivate_missing:
            stats["deactivated_lots"] = await self._deactivate_missing_lots(
                sale, existing_lots_by_number.keys(), ingested_numbers
            )

        sale.total_lots = len(ingested_numbers)
        sale.is_scraped = True
        sale.last_scraped_at = payload.scraped_at or datetime.utcnow()

        await self.db.commit()
        logger.info("Ingestion completed for sale #%s: %s", payload.sale_number, stats)
        return stats

    async def _upsert_lot(
        self,
        sale: Sale,
        lot_payload: IngestLotPayload,
        existing_lots: Dict[int, Lot],
    ) -> Dict[str, int]:
        stats = {"new_lots": 0, "updated_lots": 0, "price_changes": 0}

        existing = existing_lots.get(lot_payload.lot_number)
        price = lot_payload.price

        if existing:
            previous_price = existing.price
            has_changes = False

            for attr in ("title", "description", "status", "depot_location", "url", "image_url"):
                new_value = getattr(lot_payload, attr)
                if new_value is not None and new_value != getattr(existing, attr):
                    setattr(existing, attr, new_value)
                    has_changes = True

            if price is not None and price != existing.price:
                existing.price = price
                has_changes = True

            if lot_payload.is_active is not None:
                existing.is_active = 1 if lot_payload.is_active else 0
                has_changes = True
            else:
                existing.is_active = 1

            existing.last_updated = datetime.utcnow()

            if has_changes:
                stats["updated_lots"] += 1

            if price is not None and price != previous_price:
                stats["price_changes"] += 1
                await self._record_price_change(existing.id, price, lot_payload.status)
                await self.notifications.trigger_price_alerts(existing, price, previous_price)
        else:
            new_lot = Lot(
                sale_id=sale.id,
                lot_number=lot_payload.lot_number,
                title=lot_payload.title,
                description=lot_payload.description,
                price=price,
                status=lot_payload.status,
                depot_location=lot_payload.depot_location,
                url=lot_payload.url,
                image_url=lot_payload.image_url,
                is_active=1 if lot_payload.is_active is not False else 0,
            )
            self.db.add(new_lot)
            await self.db.flush()
            stats["new_lots"] += 1
            existing_lots[lot_payload.lot_number] = new_lot

            if price is not None:
                await self._record_price_change(new_lot.id, price, lot_payload.status)
            await self.notifications.trigger_new_lot_alerts(new_lot)
            await self.notifications.trigger_price_alerts(new_lot, price, previous_price=None)

        return stats

    async def _record_price_change(self, lot_id: int, price: int, status: Optional[str]):
        history = PriceHistory(
            lot_id=lot_id,
            price=price,
            status=status,
        )
        self.db.add(history)

    async def _deactivate_missing_lots(
        self,
        sale: Sale,
        existing_numbers: Iterable[int],
        ingested_numbers: Iterable[int],
    ) -> int:
        missing = set(existing_numbers) - set(ingested_numbers)
        if not missing:
            return 0

        count = 0
        result = await self.db.execute(
            select(Lot).where(
                Lot.sale_id == sale.id,
                Lot.lot_number.in_(missing),
            )
        )

        for lot in result.scalars().all():
            if lot.is_active != 0:
                lot.is_active = 0
                lot.last_updated = datetime.utcnow()
                count += 1

        return count


class SaleMetadataIngestionService:
    """Service d'ingestion pour les métadonnées de ventes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest(self, payload: SaleMetadataBatchRequest) -> Dict[str, int]:
        created = 0
        updated = 0

        for sale_payload in payload.sales:
            result = await self.db.execute(
                select(Sale).where(Sale.sale_number == sale_payload.sale_number)
            )
            sale = result.scalar_one_or_none()

            if sale:
                changed = False
                if sale_payload.title and sale_payload.title != sale.title:
                    sale.title = sale_payload.title
                    changed = True
                if sale_payload.status and sale_payload.status != sale.status:
                    sale.status = sale_payload.status
                    changed = True
                if sale_payload.total_lots is not None and sale_payload.total_lots != sale.total_lots:
                    sale.total_lots = sale_payload.total_lots or 0
                    changed = True
                if sale_payload.url and sale_payload.url != sale.url:
                    sale.url = sale_payload.url
                    changed = True
                if sale_payload.description is not None and sale_payload.description != sale.description:
                    sale.description = sale_payload.description
                    changed = True
                if sale_payload.start_date != sale.start_date:
                    sale.start_date = sale_payload.start_date
                    changed = True
                if sale_payload.end_date != sale.end_date:
                    sale.end_date = sale_payload.end_date
                    changed = True

                if changed:
                    updated += 1
            else:
                sale = Sale(
                    sale_number=sale_payload.sale_number,
                    title=sale_payload.title,
                    description=sale_payload.description,
                    status=sale_payload.status or "active",
                    total_lots=sale_payload.total_lots or 0,
                    url=sale_payload.url,
                    start_date=sale_payload.start_date,
                    end_date=sale_payload.end_date,
                    is_scraped=False,
                )
                self.db.add(sale)
                created += 1

        if created or updated:
            await self.db.commit()

        return {
            "created": created,
            "updated": updated,
            "total": len(payload.sales),
        }
