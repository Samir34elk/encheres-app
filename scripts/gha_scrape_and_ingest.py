#!/usr/bin/env python3
"""Scrape auction data with Playwright and ingest it through the backend API."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import httpx
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser


DEFAULT_API_BASE = os.getenv("API_BASE_URL", "https://encheres-backend.onrender.com/api/v1")
DEFAULT_SOURCE_BASE = "https://encheres-domaine.gouv.fr"
MODE_CHOICES = ("discover", "scrape", "both")


@dataclass
class SaleSummary:
    sale_number: int
    title: str
    status: str
    total_lots: int
    url: str
    description: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape auctions and push data to the backend API.")
    parser.add_argument(
        "--mode",
        choices=MODE_CHOICES,
        default="both",
        help="Operation mode: discover (sales list only), scrape (lots only) or both (default).",
    )
    parser.add_argument(
        "--api-base",
        default=DEFAULT_API_BASE,
        help="Backend API base URL (default: %(default)s)",
    )
    parser.add_argument(
        "--cron-secret",
        default=os.getenv("CRON_SECRET"),
        help="Secret header required by ingestion endpoints (fallback to CRON_SECRET env variable).",
    )
    parser.add_argument(
        "--source-base",
        default=DEFAULT_SOURCE_BASE,
        help="Base URL of the government auction website (default: %(default)s)",
    )
    parser.add_argument(
        "--sale",
        dest="sales",
        action="append",
        type=int,
        help="Specific sale number to scrape. Repeat flag to scrape multiple sales."
        " If omitted, sale list will be used to pick active sales.",
    )
    parser.add_argument(
        "--max-sales",
        type=int,
        default=10,
        help="Maximum number of sales to scrape when autodiscovering (default: %(default)s)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum number of listing pages to scan during discovery (default: %(default)s)",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run Chromium in headful mode (debugging).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    parser.add_argument(
        "--export-sales",
        help="Write discovered sale numbers to the specified JSON file.",
    )
    return parser.parse_args()


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def extract_number(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"\d+", text.replace(" ", ""))
    return int(match.group()) if match else None


DATE_PATTERN = re.compile(r"(\d{2}/\d{2}/\d{4})")
TIME_PATTERN = re.compile(r"(\d{1,2})(?:[hH:]?)(\d{2})")


def parse_datetime_field(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    date_match = DATE_PATTERN.search(text)
    if not date_match:
        return None

    hours = 0
    minutes = 0
    time_match = TIME_PATTERN.search(text)
    if time_match:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))

    try:
        dt = datetime.strptime(f"{date_match.group(1)} {hours:02d}:{minutes:02d}", "%d/%m/%Y %H:%M")
        return dt.isoformat()
    except ValueError:
        return None


def map_status(label: Optional[str]) -> str:
    if not label:
        return "active"

    lower = label.lower()
    if "annul" in lower:
        return "cancelled"
    if any(token in lower for token in ("venir", "ouvre", "bientôt")):
        return "upcoming"
    if any(token in lower for token in ("termin", "clôtur", "fermé", "fermée")):
        return "closed"
    return "active"


def parse_sale_directory_item(item: HTMLParser, base_url: str) -> Optional[SaleSummary]:
    link = item.css_first("h3.fr-card-product__title a[href^='/vente/']")
    if not link:
        return None

    href = link.attributes.get("href", "")
    match = re.search(r"/vente/(\d+)", href)
    if not match:
        return None

    sale_number = int(match.group(1))
    title = link.text(strip=True)

    lots_node = item.css_first("p.fr-card-product__desc span")
    lots_count = extract_number(lots_node.text(strip=True) if lots_node else None) or 0

    badge = item.css_first(".fr-badge")
    status_label = badge.text(strip=True) if badge else None
    status = map_status(status_label)

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    info_items = item.css("div.fr-card-product__content-last ul.fr-list li")
    for info in info_items:
        label_node = info.css_first("span.fr-text-mention-grey")
        label = label_node.text(strip=True).lower() if label_node else ""
        raw_text = info.text(strip=True)

        if any(token in label for token in ("débute", "ouvre", "ouverture", "début")):
            start_date = parse_datetime_field(raw_text)
        elif any(token in label for token in ("clôture", "date limite", "fin des offres", "fermeture")):
            end_date = parse_datetime_field(raw_text)

    url = f"{base_url}{href}"

    return SaleSummary(
        sale_number=sale_number,
        title=title,
        status=status,
        total_lots=lots_count,
        url=url,
        description=json.dumps({"status_label": status_label}, ensure_ascii=False) if status_label else None,
        start_date=start_date,
        end_date=end_date,
    )


async def scrape_sale_directory(context, base_url: str, max_pages: int) -> List[SaleSummary]:
    page = await context.new_page()
    results: List[SaleSummary] = []
    try:
        page_number = 1
        while page_number <= max_pages:
            url = f"{base_url}/ventes?page={page_number}"
            logging.info("Discovering sales page %s -> %s", page_number, url)
            await page.goto(url, wait_until="networkidle", timeout=30_000)
            try:
                await page.wait_for_selector(
                    "div.fr-list-product__item, div.fr-card, article",
                    timeout=10_000,
                )
            except Exception:
                await asyncio.sleep(3)

            html = await page.content()
            tree = HTMLParser(html)
            items = tree.css("div.fr-list-product__item")
            if not items:
                break

            page_found = False
            for item in items:
                summary = parse_sale_directory_item(item, base_url)
                if not summary:
                    continue
                results.append(summary)
                page_found = True

            if not page_found:
                break
            page_number += 1
    finally:
        await page.close()

    logging.info("Discovered %s sale(s)", len(results))
    return results


def parse_sale_page(html: str, base_url: str, sale_number: int) -> Dict[str, Any]:
    tree = HTMLParser(html)

    title_node = tree.css_first("h1") or tree.css_first("h2")
    title = title_node.text(strip=True) if title_node else f"Vente {sale_number}"

    status_label = None
    badge = tree.css_first(".fr-badge")
    if badge:
        status_label = badge.text(strip=True)

    status = map_status(status_label)

    lots = []
    container = tree.css_first("ul.fr-list-product")
    if container:
        for item in container.css("div.fr-list-product__item"):
            lot_number_node = item.css_first("p.fr-card-product__desc span")
            lot_number = extract_number(lot_number_node.text(strip=True) if lot_number_node else None)
            if lot_number is None:
                continue

            title_node = item.css_first("h3.fr-card-product__title a")
            href = title_node.attributes.get("href") if title_node else None
            lot_title = title_node.text(strip=True) if title_node else f"Lot {lot_number}"

            price_node = item.css_first("p.fr-price__price")
            price = extract_number(price_node.text(strip=True) if price_node else None)

            status_node = item.css_first("p.fr-price__text")
            lot_status = status_node.text(strip=True) if status_node else None

            depot_node = item.css_first("p.fr-text--xs strong")
            depot = depot_node.text(strip=True) if depot_node else None

            img_node = item.css_first("div.fr-card-product__img img")
            image_url = img_node.attributes.get("src") if img_node else None

            desc_node = item.css_first("div.fr-text--sm.fr-ellipsis--3 p")
            description = desc_node.text(strip=True) if desc_node else None

            lots.append(
                {
                    "lot_number": lot_number,
                    "title": lot_title,
                    "description": description,
                    "price": price,
                    "status": lot_status,
                    "depot_location": depot,
                    "url": f"{base_url}{href}" if href else None,
                    "image_url": image_url,
                    "is_active": True,
                }
            )

    return {
        "metadata": {
            "sale_number": sale_number,
            "title": title,
            "status": status,
            "url": f"{base_url}/vente/{sale_number}",
            "description": json.dumps({"status_label": status_label}, ensure_ascii=False) if status_label else None,
        },
        "lots": lots,
    }


async def scrape_sale(context, base_url: str, sale_number: int) -> Dict[str, Any]:
    page = await context.new_page()
    try:
        page_number = 1
        all_lots: List[Dict[str, Any]] = []
        metadata: Optional[Dict[str, Any]] = None

        while True:
            url = f"{base_url}/vente/{sale_number}?page={page_number}"
            logging.info("Scraping sale #%s page %s -> %s", sale_number, page_number, url)
            await page.goto(url, wait_until="networkidle", timeout=30_000)
            try:
                await page.wait_for_selector(
                    "ul.fr-list-product, div.fr-list-product__item, div.fr-card",
                    timeout=10_000,
                )
            except Exception:
                await asyncio.sleep(3)

            html = await page.content()
            parsed = parse_sale_page(html, base_url, sale_number)

            if metadata is None:
                metadata = parsed["metadata"]

            lots = parsed["lots"]
            if not lots:
                break

            all_lots.extend(lots)
            page_number += 1

        return {"metadata": metadata, "lots": all_lots}
    finally:
        await page.close()


def build_ingestion_payload(scraped_sale: Dict[str, Any]) -> Dict[str, Any]:
    metadata = scraped_sale["metadata"]
    lots = scraped_sale["lots"]
    payload = {
        "sale_number": metadata["sale_number"],
        "title": metadata.get("title"),
        "description": metadata.get("description"),
        "status": metadata.get("status"),
        "url": metadata.get("url"),
        "scraped_at": datetime.utcnow().isoformat(),
        "deactivate_missing": True,
        "lots": lots,
    }

    if metadata.get("start_date"):
        payload["start_date"] = metadata["start_date"]
    if metadata.get("end_date"):
        payload["end_date"] = metadata["end_date"]

    return payload


async def post_sales_metadata(
    client: httpx.AsyncClient,
    api_base: str,
    secret: str,
    summaries: Iterable[SaleSummary],
) -> Optional[Dict[str, Any]]:
    summaries = list(summaries)
    if not summaries:
        return None

    payload = {
        "sales": [
            {
                "sale_number": summary.sale_number,
                "title": summary.title,
                "status": summary.status,
                "total_lots": summary.total_lots,
                "url": summary.url,
                "description": summary.description,
                "start_date": summary.start_date,
                "end_date": summary.end_date,
            }
            for summary in summaries
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "X-Cron-Secret": secret,
    }

    url = f"{api_base}/ingestion/sales-metadata"
    logging.info("Posting %s sale metadata entries", len(summaries))
    response = await client.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


async def post_sale_lots(
    client: httpx.AsyncClient,
    api_base: str,
    secret: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "X-Cron-Secret": secret,
    }
    url = f"{api_base}/ingestion/sales"
    logging.info(
        "Posting %s lots for sale #%s",
        len(payload.get("lots", [])),
        payload.get("sale_number"),
    )
    response = await client.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    return response.json()


async def fetch_active_sale_numbers(client: httpx.AsyncClient, api_base: str, limit: int) -> List[int]:
    url = f"{api_base}/sales?size={limit}"
    logging.info("Fetching existing sales from %s", url)
    response = await client.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()

    sale_numbers: List[int] = []
    for item in payload.get("items", []):
        status = (item.get("status") or "").lower()
        if status not in {"closed", "cancelled"}:
            sale_numbers.append(int(item["sale_number"]))

    return sorted(sale_numbers)


def select_sale_numbers(args, summaries: List[SaleSummary], fallback: List[int]) -> List[int]:
    if args.sales:
        return list(dict.fromkeys(args.sales))  # Remove duplicates, preserve order

    if summaries:
        candidates = [s.sale_number for s in summaries if s.status not in {"closed", "cancelled"}]
        return candidates[: args.max_sales]

    return fallback[: args.max_sales]


def export_sale_numbers(path: str, summaries: Iterable[SaleSummary], limit: Optional[int]) -> None:
    numbers = [summary.sale_number for summary in summaries]
    if limit is not None and limit > 0:
        numbers = numbers[:limit]
    unique_numbers = list(dict.fromkeys(numbers))
    with open(path, "w", encoding="utf-8") as file:
        json.dump(unique_numbers, file)
    logging.info("Exported %s sale number(s) to %s", len(unique_numbers), path)


async def run() -> int:
    args = parse_args()
    setup_logging(args.verbose)

    if not args.cron_secret:
        logging.error("Cron secret missing. Provide it via --cron-secret or CRON_SECRET env variable.")
        return 1

    api_base = args.api_base.rstrip("/")
    source_base = args.source_base.rstrip("/")

    async with httpx.AsyncClient() as client:
        sale_summaries: List[SaleSummary] = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=not args.headful)
            context = await browser.new_context(ignore_https_errors=True)

            try:
                if args.mode in {"discover", "both"}:
                    sale_summaries = await scrape_sale_directory(context, source_base, args.max_pages)
                    if args.export_sales:
                        export_sale_numbers(args.export_sales, sale_summaries, args.max_sales)
                    await post_sales_metadata(client, api_base, args.cron_secret, sale_summaries)

                    if args.mode == "discover":
                        logging.info("Discovery mode complete (%s sales).", len(sale_summaries))
                        return 0

                fallback_sales = await fetch_active_sale_numbers(client, api_base, args.max_sales)
                selected_sales = select_sale_numbers(args, sale_summaries, fallback_sales)

                if args.mode in {"scrape", "both"} and not selected_sales:
                    logging.warning("No sales selected for scraping.")
                    return 0

                if args.mode in {"scrape", "both"}:
                    logging.info("Scraping %s sale(s): %s", len(selected_sales), selected_sales)
                    for sale_number in selected_sales:
                        scraped = await scrape_sale(context, source_base, sale_number)
                        lots = scraped["lots"]
                        if not lots:
                            logging.warning("No lots found for sale #%s; skipping ingestion.", sale_number)
                            continue

                        payload = build_ingestion_payload(scraped)
                        result = await post_sale_lots(client, api_base, args.cron_secret, payload)
                        logging.info("Ingestion result for sale #%s: %s", sale_number, json.dumps(result))
            finally:
                await context.close()
                await browser.close()

    return 0


def main():
    try:
        exit_code = asyncio.run(run())
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("Fatal error during scraping workflow: %s", exc)
        exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
