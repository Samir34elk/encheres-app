#!/usr/bin/env python3
"""
Script to update prices for favorited lots.
Runs in GitHub Actions every minute.
Scrapes prices from official URLs and updates via API.
"""

import asyncio
import os
import sys
import re
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
CRON_SECRET = os.getenv("CRON_SECRET")

if not CRON_SECRET:
    print("ERROR: CRON_SECRET environment variable not set")
    sys.exit(1)

HEADERS = {
    "X-Cron-Secret": CRON_SECRET,
    "Content-Type": "application/json"
}


async def get_favorited_lots():
    """Fetch all lots that have been favorited and have URLs"""
    print(f"Fetching favorited lots from {API_BASE_URL}/favorites/lots")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/favorites/lots",
                headers=HEADERS
            )
            response.raise_for_status()
            lots = response.json()

            # Filter lots with valid URLs
            valid_lots = [
                lot for lot in lots
                if lot.get("url") and lot["url"] not in ["", "N/A"]
            ]

            print(f"Found {len(valid_lots)} favorited lots with valid URLs")
            return valid_lots

        except Exception as e:
            print(f"ERROR: Failed to fetch favorited lots: {e}")
            return []


async def scrape_price_from_url(url: str):
    """Scrape the current price from a lot URL using Playwright"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                ignore_https_errors=True
            )
            page = await context.new_page()

            try:
                # Navigate to the lot page
                await page.goto(url, wait_until="networkidle", timeout=15000)

                # Wait for the price element
                await page.wait_for_selector("p.fr-price__price", timeout=5000)

                # Extract price text
                price_text = await page.locator("p.fr-price__price").text_content()
                price_text = price_text.strip() if price_text else None

                # Extract price number
                price = None
                if price_text:
                    # Remove non-numeric characters except spaces
                    clean_price = re.sub(r'[^\d\s]', '', price_text)
                    clean_price = clean_price.replace(' ', '')
                    if clean_price:
                        try:
                            price = int(clean_price)
                        except ValueError:
                            print(f"WARNING: Could not parse price '{price_text}' for {url}")

                # Try to extract status
                status = None
                try:
                    status_elem = await page.locator(".fr-badge, .fr-card-product__status").first.text_content(timeout=2000)
                    status = status_elem.strip() if status_elem else None
                except:
                    pass

                await browser.close()

                return {
                    "price": price,
                    "status": status,
                    "success": True,
                    "error": None
                }

            except PlaywrightTimeoutError:
                await browser.close()
                print(f"WARNING: Timeout while scraping {url}")
                return {"price": None, "status": None, "success": False, "error": "timeout"}

            except Exception as e:
                await browser.close()
                print(f"WARNING: Error scraping {url}: {e}")
                return {"price": None, "status": None, "success": False, "error": str(e)}

    except Exception as e:
        print(f"ERROR: Failed to initialize browser for {url}: {e}")
        return {"price": None, "status": None, "success": False, "error": str(e)}


async def update_lot_price(lot_id: int, price: int, status: str = None):
    """Update a lot's price via API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            payload = {"price": price}
            if status:
                payload["status"] = status

            response = await client.patch(
                f"{API_BASE_URL}/lots/{lot_id}/price",
                headers=HEADERS,
                json=payload
            )
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"ERROR: Failed to update lot {lot_id}: {e}")
            return False


async def main():
    """Main function to update all favorited lots prices"""
    print(f"Starting favorite prices update job at {datetime.utcnow().isoformat()}")

    # Get favorited lots
    lots = await get_favorited_lots()

    if not lots:
        print("No favorited lots to update")
        return

    updated_count = 0
    error_count = 0

    for lot in lots:
        lot_id = lot["id"]
        lot_url = lot["url"]
        current_price = lot.get("price")

        print(f"\nChecking lot {lot_id}: {lot.get('title', 'N/A')[:50]}...")
        print(f"  URL: {lot_url}")
        print(f"  Current price: {current_price}€")

        # Scrape new price
        scraped_data = await scrape_price_from_url(lot_url)

        if not scraped_data["success"]:
            print(f"  ❌ Failed to scrape: {scraped_data.get('error')}")
            error_count += 1
            continue

        new_price = scraped_data["price"]
        new_status = scraped_data["status"]

        if new_price is None:
            print(f"  ⚠️ No price found")
            error_count += 1
            continue

        print(f"  New price: {new_price}€")

        # Check if price changed
        if new_price != current_price:
            print(f"  💰 Price changed: {current_price}€ → {new_price}€")

            # Update via API
            if await update_lot_price(lot_id, new_price, new_status):
                print(f"  ✅ Updated successfully")
                updated_count += 1
            else:
                print(f"  ❌ Failed to update")
                error_count += 1
        else:
            print(f"  ✓ Price unchanged")

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total lots checked: {len(lots)}")
    print(f"  Prices updated: {updated_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
