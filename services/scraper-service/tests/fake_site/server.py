"""
Faux encheres-domaine.gouv.fr pour tester le scraper sans toucher au vrai site.

Imite les 3 requêtes GraphQL utilisées (getAuctions, getAuctionLots, getProductPageMain),
compte toutes les requêtes reçues et peut simuler un blocage.

    GET  /__stats              → nombre de requêtes par opération, intervalle minimum observé
    POST /__mode?value=403     → le site répond 403 à tout (IP bloquée)
    POST /__mode?value=429     → le site répond 429 à tout (trop de requêtes)
    POST /__mode?value=challenge → page HTML anti-robot (JS + cookies requis)
    POST /__mode?value=ok      → retour à la normale
    POST /__reset              → remet les compteurs à zéro

Lancement : python server.py [port]   (stdlib uniquement)
"""

import json
import random
import sys
import threading
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

random.seed(42)
NOW = datetime.utcnow()
FMT = "%Y-%m-%d %H:%M:%S"


def _sale(sale_id, status_text, start, end, nb_lots):
    return {
        "dnid_auction_id": str(sale_id),
        "name": f"Vente test #{sale_id}",
        "description": "Vente générée par le faux site",
        "status_text": status_text,
        "auction_auto_status": {"Clôturée": "7", "En cours": "3", "À venir": "2"}[status_text],
        "start_date": start.strftime(FMT),
        "end_date": end.strftime(FMT),
        "offers_submission_deadline": None,
        "auction_number_of_lots": nb_lots,
        "categories": [{"name": "Véhicules", "__typename": "C"}],
        "image_path": None,
        "location": "Paris",
        "professional_only": False,
        "sales_inspector_label": "CAV Test",
        "type": "1",
        "type_text": "Enchères",
        "auction_documents": None,
    }


# 200 ventes clôturées (historique), 25 en cours (dont 5 finissent dans l'heure), 15 à venir
SALES = []
sid = 1000
for i in range(200):
    end = NOW - timedelta(days=5 + i)
    SALES.append(_sale(sid, "Clôturée", end - timedelta(days=10), end, 20)); sid += 1
for i in range(25):
    end = NOW + (timedelta(minutes=50) if i < 5 else timedelta(days=1 + i))
    SALES.append(_sale(sid, "En cours", NOW - timedelta(days=3), end, 30)); sid += 1
for i in range(15):
    start = NOW + timedelta(days=5 + i)
    SALES.append(_sale(sid, "À venir", start, start + timedelta(days=7), 25)); sid += 1

LOTS = {
    s["dnid_auction_id"]: [
        {
            "lot_number": n,
            "name": f"Lot {n} de la vente {s['dnid_auction_id']}",
            "url_key": f"{s['dnid_auction_id']}bi{n:05d}",
            "sku": f"SKU{s['dnid_auction_id']}{n}",
            "last_bid": str(100 + n * 10),
            "price_auction": str(100 + n * 10),
            "reserve_price": None,
            "professional_only": False,
            "lot_status_label": "En cours" if s["status_text"] == "En cours" else s["status_text"],
            "dropoff_location": {"city": "Paris", "postcode": "75001"},
            "small_image": {"url": f"https://example.invalid/{n}.jpg"},
            "description": {"html": "<p>Description</p>"},
            "short_description": {"html": ""},
        }
        for n in range(1, s["auction_number_of_lots"] + 1)
    ]
    for s in SALES
}

lock = threading.Lock()
state = {"mode": "ok", "counts": {}, "times": [], "requested_sales": {}}


def _page(items, page, size):
    total_pages = max(1, -(-len(items) // size))
    return {
        "items": items[(page - 1) * size: page * size],
        "page_info": {"total_pages": total_pages},
        "total_count": len(items),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        url = urlparse(self.path)
        qs = parse_qs(url.query)
        with lock:
            if url.path == "/__mode":
                state["mode"] = qs.get("value", ["ok"])[0]
            elif url.path == "/__reset":
                state.update(counts={}, times=[], requested_sales={})
        self._json(200, {"mode": state["mode"]})

    def do_GET(self):
        url = urlparse(self.path)
        qs = parse_qs(url.query)

        if url.path == "/__stats":
            with lock:
                t = state["times"]
                gaps = [b - a for a, b in zip(t, t[1:])]
                self._json(200, {
                    "mode": state["mode"],
                    "total": len(t),
                    "by_operation": state["counts"],
                    "min_gap_seconds": round(min(gaps), 2) if gaps else None,
                    "lots_requests_by_sale": state["requested_sales"],
                })
            return

        op = qs.get("operationName", ["?"])[0]
        variables = json.loads(qs.get("variables", ["{}"])[0])
        with lock:
            state["times"].append(time.monotonic())
            state["counts"][op] = state["counts"].get(op, 0) + 1
            mode = state["mode"]

        if mode in ("403", "429"):
            self._json(int(mode), {"message": "blocked"})
            return
        if mode == "challenge":
            html = (b"<html><body><script>window.location.href='/redirect_X/'</script>"
                    b"<noscript>This website requires JS enabled and cookies</noscript></body></html>")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if op == "getAuctions":
            desc = "DESC" in json.dumps(variables.get("sort", {}))
            items = sorted(SALES, key=lambda s: s["start_date"], reverse=desc)
            data = {"auctionsList": _page(items, variables.get("currentPage", 1), variables.get("pageSize", 100))}
        elif op == "getAuctionLots":
            auction = variables["filter"]["auction"]["eq"]
            with lock:
                state["requested_sales"][auction] = state["requested_sales"].get(auction, 0) + 1
            lots = LOTS.get(auction, [])
            # Les enchères montent sur les ventes en cours
            for lot in lots:
                if lot["lot_status_label"] == "En cours" and random.random() < 0.3:
                    lot["last_bid"] = str(int(lot["last_bid"]) + 10)
            data = {"products": _page(lots, variables.get("currentPage", 1), variables.get("pageSize", 1000))}
        elif op == "getProductPageMain":
            data = {"products": {"items": []}}
        else:
            self._json(400, {"errors": [{"message": f"unknown operation {op}"}]})
            return

        self._json(200, {"data": data})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    print(f"Faux site sur :{port} — {len(SALES)} ventes", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
