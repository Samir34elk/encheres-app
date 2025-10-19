#!/usr/bin/env python3
"""
Script to import auction lots from CSV file into database
"""
import asyncio
import csv
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import AsyncSessionLocal
from app.models.lot import Lot
from app.models.sale import Sale
from sqlalchemy import select


async def import_csv(csv_file: str, sale_number: int):
    """Import CSV data into database"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if sale exists, create if not
            result = await db.execute(select(Sale).where(Sale.sale_number == sale_number))
            sale = result.scalar_one_or_none()

            if not sale:
                print(f"Creating sale #{sale_number}...")
                sale = Sale(
                    sale_number=sale_number,
                    title=f"Vente #{sale_number}",
                    status="active",
                    url=f"https://encheres-domaine.gouv.fr/vente/{sale_number}"
                )
                db.add(sale)
                await db.flush()
                print(f"✅ Sale #{sale_number} created with ID: {sale.id}")
            else:
                print(f"✅ Sale #{sale_number} already exists with ID: {sale.id}")

            # Read CSV file
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)  # DictReader reads the header automatically

                imported = 0
                updated = 0

                for row in reader:
                    lot_number = int(row["Lot"]) if row["Lot"] and row["Lot"].isdigit() else None
                    if not lot_number:
                        continue

                    # Check if lot already exists
                    result = await db.execute(
                        select(Lot).where(
                            Lot.sale_id == sale.id,
                            Lot.lot_number == lot_number
                        )
                    )
                    existing_lot = result.scalar_one_or_none()

                    lot_data = {
                        "sale_id": sale.id,
                        "lot_number": lot_number,
                        "title": row["Titre"],
                        "description": row["Description"],
                        "price": int(row["Prix"]) if row["Prix"] and row["Prix"].isdigit() else None,
                        "status": row["Statut"],
                        "depot_location": row["Lieu dépôt"],
                        "url": row["URL Lot"],
                        "image_url": row["URL Image"]
                    }

                    if existing_lot:
                        # Update existing lot
                        for key, value in lot_data.items():
                            setattr(existing_lot, key, value)
                        updated += 1
                    else:
                        # Create new lot
                        lot = Lot(**lot_data)
                        db.add(lot)
                        imported += 1

                await db.commit()
                print(f"\n✅ Import completed!")
                print(f"   - New lots: {imported}")
                print(f"   - Updated lots: {updated}")
                print(f"   - Total: {imported + updated}")

                # Update sale total_lots
                result = await db.execute(
                    select(Lot).where(Lot.sale_id == sale.id)
                )
                total_lots = len(result.scalars().all())
                sale.total_lots = total_lots
                sale.is_scraped = True
                await db.commit()

                print(f"   - Sale #{sale_number} total lots: {total_lots}")

        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_csv.py <csv_file> [sale_number]")
        print("Example: python import_csv.py encheres.csv 42")
        sys.exit(1)

    csv_file = sys.argv[1]
    sale_number = int(sys.argv[2]) if len(sys.argv) > 2 else 42

    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)

    print(f"📥 Importing data from {csv_file} into sale #{sale_number}...")
    asyncio.run(import_csv(csv_file, sale_number))
