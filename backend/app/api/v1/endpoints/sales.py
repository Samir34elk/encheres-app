from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
import math

from app.db.session import get_db
from app.core.config import settings
from app.models.sale import Sale
from app.schemas.sale import SaleResponse, SaleListResponse, SaleCreate

router = APIRouter()


@router.get("", response_model=SaleListResponse)
async def get_sales(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of sales"""
    query = select(Sale)

    # Filter by status if provided
    if status:
        query = query.where(Sale.status == status)

    # Order by sale_number descending (newest first)
    query = query.order_by(desc(Sale.sale_number))

    # Total count
    count_query = select(func.count()).select_from(Sale)
    if status:
        count_query = count_query.where(Sale.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    # Execute query
    result = await db.execute(query)
    sales = result.scalars().all()

    # Transform to Pydantic
    items = [SaleResponse.model_validate(sale) for sale in sales]

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific sale by ID"""
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    return SaleResponse.model_validate(sale)


@router.get("/by-number/{sale_number}", response_model=SaleResponse)
async def get_sale_by_number(
    sale_number: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific sale by sale number"""
    result = await db.execute(select(Sale).where(Sale.sale_number == sale_number))
    sale = result.scalar_one_or_none()

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    return SaleResponse.model_validate(sale)


@router.post("", response_model=SaleResponse)
async def create_sale(
    sale_data: SaleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new sale"""
    # Check if sale_number already exists
    existing = await db.execute(
        select(Sale).where(Sale.sale_number == sale_data.sale_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Sale number already exists")

    # Create new sale
    sale = Sale(**sale_data.model_dump())
    db.add(sale)
    await db.commit()
    await db.refresh(sale)

    return SaleResponse.model_validate(sale)
