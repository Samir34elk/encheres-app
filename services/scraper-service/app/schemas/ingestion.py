from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator


class IngestLotPayload(BaseModel):
    """Payload représentant un lot à ingérer."""

    lot_number: int
    title: str
    description: Optional[str] = None
    price: Optional[int] = None
    status: Optional[str] = None
    depot_location: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = True

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if isinstance(value, bool):  # bool is subclass of int in Python
            raise ValueError("price must be an integer value")
        return value


class IngestSalePayload(BaseModel):
    """Payload représentant une vente et ses lots associés."""

    sale_number: int
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    deactivate_missing: bool = True
    lots: List[IngestLotPayload]


class IngestionBatchRequest(BaseModel):
    """Payload racine pour ingérer plusieurs ventes."""

    sales: List[IngestSalePayload]


class IngestionResult(BaseModel):
    """Statistiques renvoyées après ingestion."""

    sale_number: int
    total_lots_received: int
    new_lots: int
    updated_lots: int
    price_changes: int
    deactivated_lots: int
    errors: List[Dict[str, Any]]


class SaleMetadataPayload(BaseModel):
    """Payload représentant les métadonnées d'une vente."""

    sale_number: int
    title: str
    status: Optional[str] = None
    total_lots: Optional[int] = None
    url: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SaleMetadataBatchRequest(BaseModel):
    """Payload pour ingérer plusieurs ventes (métadonnées uniquement)."""

    sales: List[SaleMetadataPayload]


class SaleMetadataResult(BaseModel):
    """Résultat de l'ingestion des métadonnées de ventes."""

    created: int
    updated: int
    total: int
