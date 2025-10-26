from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.endpoints.scheduler import verify_cron_secret
from app.db.session import AsyncSessionLocal
from app.schemas.ingestion import (
    IngestSalePayload,
    IngestionBatchRequest,
    IngestionResult,
    SaleMetadataBatchRequest,
    SaleMetadataResult,
)
from app.services.ingestion import AuctionDataIngestionService, SaleMetadataIngestionService

router = APIRouter()


@router.post(
    "/sales",
    response_model=IngestionResult,
    status_code=status.HTTP_200_OK,
    summary="Ingestion d'une vente et de ses lots",
)
async def ingest_sale_endpoint(
    payload: IngestSalePayload,
    _: None = Depends(verify_cron_secret),
):
    """Ingestion de données pour une vente unique."""
    if not payload.lots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must include at least one lot",
        )

    async with AsyncSessionLocal() as db:
        service = AuctionDataIngestionService(db)
        result = await service.ingest_sale(payload)
        return IngestionResult.model_validate(result)


@router.post(
    "/batch",
    response_model=List[IngestionResult],
    status_code=status.HTTP_200_OK,
    summary="Ingestion de plusieurs ventes",
)
async def ingest_batch_endpoint(
    payload: IngestionBatchRequest,
    _: None = Depends(verify_cron_secret),
):
    """Ingestion de plusieurs ventes en une seule requête."""
    if not payload.sales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must include at least one sale",
        )

    async with AsyncSessionLocal() as db:
        service = AuctionDataIngestionService(db)
        results = []
        for sale_payload in payload.sales:
            if not sale_payload.lots:
                continue
            summary = await service.ingest_sale(sale_payload)
            results.append(IngestionResult.model_validate(summary))
        return results


@router.post(
    "/sales-metadata",
    response_model=SaleMetadataResult,
    status_code=status.HTTP_200_OK,
    summary="Ingestion des métadonnées de ventes",
)
async def ingest_sales_metadata_endpoint(
    payload: SaleMetadataBatchRequest,
    _: None = Depends(verify_cron_secret),
):
    """Ingestion des métadonnées (liste des ventes)."""
    if not payload.sales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must include at least one sale",
        )

    async with AsyncSessionLocal() as db:
        service = SaleMetadataIngestionService(db)
        result = await service.ingest(payload)
        return SaleMetadataResult.model_validate(result)
