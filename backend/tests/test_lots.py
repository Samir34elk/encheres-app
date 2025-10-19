"""Tests for lots endpoints"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lot import Lot
from app.models.sale import Sale


@pytest.fixture
async def test_sale(test_db: AsyncSession) -> Sale:
    """Create a test sale"""
    sale = Sale(
        sale_number=42,
        title="Test Sale",
        description="Test sale description",
        url="https://example.com/sale/42",
        status="active",
    )
    test_db.add(sale)
    await test_db.commit()
    await test_db.refresh(sale)
    return sale


@pytest.fixture
async def test_lots(test_db: AsyncSession, test_sale: Sale):
    """Create test lots"""
    lots = []
    for i in range(5):
        lot = Lot(
            sale_id=test_sale.id,
            lot_number=i + 1,
            title=f"Test Lot {i + 1}",
            description=f"Description for lot {i + 1}",
            price=1000 * (i + 1),
            status="Available",
            depot_location=f"Location {i % 2 + 1}",
            url=f"https://example.com/lot/{i + 1}",
            image_url=f"https://example.com/img/{i + 1}.jpg",
        )
        test_db.add(lot)
        lots.append(lot)

    await test_db.commit()
    for lot in lots:
        await test_db.refresh(lot)

    return lots


@pytest.mark.integration
async def test_get_lots(client: AsyncClient, test_lots: list[Lot]):
    """Test getting list of lots"""
    response = await client.get("/api/v1/lots")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) == 5
    assert data["total"] == 5


@pytest.mark.integration
async def test_get_lots_pagination(client: AsyncClient, test_lots: list[Lot]):
    """Test lots pagination"""
    response = await client.get("/api/v1/lots", params={"page": 1, "size": 2})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["pages"] == 3


@pytest.mark.integration
async def test_get_lots_search(client: AsyncClient, test_lots: list[Lot]):
    """Test lots search"""
    response = await client.get("/api/v1/lots", params={"search": "Lot 1"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert "Lot 1" in data["items"][0]["title"]


@pytest.mark.integration
async def test_get_lots_price_filter(client: AsyncClient, test_lots: list[Lot]):
    """Test lots price filtering"""
    response = await client.get(
        "/api/v1/lots", params={"min_price": 2000, "max_price": 4000}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3  # Lots 2, 3, 4
    for item in data["items"]:
        assert 2000 <= item["price"] <= 4000


@pytest.mark.integration
async def test_get_lots_location_filter(client: AsyncClient, test_lots: list[Lot]):
    """Test lots location filtering"""
    response = await client.get("/api/v1/lots", params={"location": "Location 1"})

    assert response.status_code == 200
    data = response.json()
    assert all("Location 1" in item["depot_location"] for item in data["items"])


@pytest.mark.integration
async def test_get_lots_sorting(client: AsyncClient, test_lots: list[Lot]):
    """Test lots sorting"""
    # Sort by price descending
    response = await client.get(
        "/api/v1/lots", params={"sort_by": "price", "order": "desc"}
    )

    assert response.status_code == 200
    data = response.json()
    prices = [item["price"] for item in data["items"]]
    assert prices == sorted(prices, reverse=True)


@pytest.mark.integration
async def test_get_lot_by_id(client: AsyncClient, test_lots: list[Lot]):
    """Test getting a specific lot"""
    lot = test_lots[0]
    response = await client.get(f"/api/v1/lots/{lot.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == lot.id
    assert data["title"] == lot.title


@pytest.mark.integration
async def test_get_nonexistent_lot(client: AsyncClient):
    """Test getting a non-existent lot"""
    response = await client.get("/api/v1/lots/99999")

    assert response.status_code == 404


@pytest.mark.integration
async def test_lot_view_count_increments(client: AsyncClient, test_lots: list[Lot], test_db: AsyncSession):
    """Test that view count increments when lot is viewed"""
    lot = test_lots[0]
    initial_count = lot.view_count

    response = await client.get(f"/api/v1/lots/{lot.id}")
    assert response.status_code == 200

    # Refresh lot from database
    await test_db.refresh(lot)
    assert lot.view_count == initial_count + 1
