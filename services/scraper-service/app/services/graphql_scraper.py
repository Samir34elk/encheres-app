"""
GraphQL Scraper - Nouveau scraper utilisant l'API GraphQL officielle

Ce module remplace le scraping HTML par des requêtes GraphQL directes vers l'API
officielle de encheres-domaine.gouv.fr. Beaucoup plus rapide et stable que Playwright.

Avantages:
- 60x plus rapide que le scraping HTML
- Données structurées (JSON)
- Plus de champs disponibles
- Pas de dépendance à Playwright
- API officielle stable
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.sale import Sale
from app.models.lot import Lot
from app.models.price_history import PriceHistory
from app.services.notification_service import NotificationService
from app.core.config import settings
from app.services.polite_client import polite_client

logger = logging.getLogger(__name__)


class GraphQLAuctionScraper:
    """
    Scraper GraphQL pour récupérer les ventes aux enchères

    Utilise l'API GraphQL officielle au lieu du scraping HTML.
    Remplace AuctionScraper (Playwright) par une approche API.
    """

    BASE_URL = settings.AUCTION_GRAPHQL_URL
    IMAGE_PREFIX = "https://encheres-domaine.gouv.fr/admin/media/auctions/upload/"

    # Requête GraphQL pour lister les ventes
    AUCTIONS_QUERY = """
    query getAuctions(
      $currentPage: Int
      $filter: AuctionFiltersInput
      $pageSize: Int
      $sort: AuctionSortsInput
    ) {
      auctionsList(
        currentPage: $currentPage
        filter: $filter
        pageSize: $pageSize
        sort: $sort
      ) {
        items {
          auction_auto_status
          auction_documents {
            pdf_specifications {
              label
              url_path
              type
              size
              __typename
            }
            __typename
          }
          auction_number_of_lots
          categories {
            name
            __typename
          }
          description
          dnid_auction_id
          end_date
          image_path
          location
          name
          offers_submission_deadline
          professional_only
          sales_inspector_label
          start_date
          status_text
          type
          type_text
          __typename
        }
        page_info {
          total_pages
          __typename
        }
        total_count
        __typename
      }
    }
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)

    async def close(self):
        """Conservé pour compatibilité : le client HTTP est partagé (polite_client)."""

    async def fetch_auctions(
        self,
        page: int = 1,
        page_size: int = 100,
        filter_status: Optional[List[str]] = None,
        sort_by: str = "start_date",
        sort_order: str = "ASC"
    ) -> Dict[str, Any]:
        """
        Récupère les ventes via l'API GraphQL

        Args:
            page: Numéro de page (commence à 1)
            page_size: Nombre de résultats par page (max 100)
            filter_status: Filtrer par statut (ex: ["2", "3", "7"])
            sort_by: Champ de tri (start_date, end_date, etc.)
            sort_order: Ordre de tri (ASC, DESC)

        Returns:
            Dict contenant items, page_info, total_count
        """
        variables = {
            "currentPage": page,
            "pageSize": page_size,
            "sort": {sort_by: sort_order}
        }

        # Ajouter le filtre de statut si spécifié
        if filter_status:
            variables["filter"] = {
                "auction_auto_status": {"in": filter_status}
            }

        params = {
            "query": self.AUCTIONS_QUERY,
            "operationName": "getAuctions",
            "variables": json.dumps(variables)
        }

        logger.info(f"Fetching auctions page {page} (size: {page_size})")
        data = await polite_client.get_json(self.BASE_URL, params=params)

        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            raise Exception(f"GraphQL errors: {data['errors']}")

        auctions_data = (data.get("data") or {}).get("auctionsList") or {}
        logger.info(
            f"Fetched {len(auctions_data.get('items', []))} auctions "
            f"(total: {auctions_data.get('total_count', 0)})"
        )
        return auctions_data

    async def fetch_all_auctions(
        self,
        filter_status: Optional[List[str]] = None,
        max_pages: Optional[int] = None,
        incremental: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Récupère toutes les ventes (pagination automatique)

        Args:
            filter_status: Filtrer par statut
            max_pages: Nombre maximum de pages (None = toutes)
            incremental: Trie par date de début décroissante et s'arrête dès qu'une
                page ne contient que des ventes clôturées déjà connues en BDD
                (évite de re-télécharger tout l'historique à chaque passage).

        Returns:
            Liste de toutes les ventes
        """
        all_auctions = []
        page = 1
        known_closed = await self._known_closed_sale_numbers() if incremental else set()

        while True:
            data = await self.fetch_auctions(
                page=page,
                page_size=100,
                filter_status=filter_status,
                sort_order="DESC" if incremental else "ASC"
            )

            items = data.get("items", [])
            if not items:
                break

            all_auctions.extend(items)

            if incremental and all(
                self._map_status(item.get("status_text")) == "closed"
                and self._to_int(item.get("dnid_auction_id")) in known_closed
                for item in items
            ):
                logger.info(f"Incremental sync: page {page} only has known closed sales, stopping")
                break

            # Vérifier s'il y a d'autres pages
            page_info = data.get("page_info", {})
            total_pages = page_info.get("total_pages", 1)

            if page >= total_pages or (max_pages and page >= max_pages):
                break

            page += 1

        logger.info(f"Fetched total of {len(all_auctions)} auctions")
        return all_auctions

    async def _known_closed_sale_numbers(self) -> set:
        result = await self.db.execute(
            select(Sale.sale_number).where(Sale.status == "closed")
        )
        return set(result.scalars().all())

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _parse_auction_data(self, auction_raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse les données brutes de l'API en format compatible BDD

        Args:
            auction_raw: Données brutes de l'API GraphQL

        Returns:
            Dict avec les champs pour le modèle Sale
        """
        # Date de fin: priorité à end_date, sinon offers_submission_deadline
        end_date = auction_raw.get("end_date") or auction_raw.get("offers_submission_deadline")

        # Organisateur
        organiser = auction_raw.get("sales_inspector_label") or "Domaine Public"

        # Catégories (array de strings)
        categories = [cat["name"] for cat in auction_raw.get("categories", [])]

        # URL de l'image complète
        image_path = auction_raw.get("image_path")
        image_url = None
        if image_path:
            image_url = self.IMAGE_PREFIX + image_path

        return {
            "sale_number": self._to_int(auction_raw.get("dnid_auction_id")),
            "title": auction_raw.get("name"),
            "description": auction_raw.get("description"),
            "organiser": organiser,
            "type_vente": auction_raw.get("type_text"),
            "categories": categories if categories else None,
            "start_date": self._parse_datetime(auction_raw.get("start_date")),
            "end_date": self._parse_datetime(end_date),
            "status": self._map_status(auction_raw.get("status_text")),
            "total_lots": auction_raw.get("auction_number_of_lots", 0),
            "image_url": image_url,
            "url": f"https://encheres-domaine.gouv.fr/vente/{auction_raw.get('dnid_auction_id')}",
            # is_scraped / last_scraped_at concernent le scraping des LOTS :
            # ils sont mis à jour par le job de scraping, pas ici.
        }

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse une date ISO 8601 en datetime (naive, sans timezone)"""
        if not date_str:
            return None
        try:
            # Format: "2025-01-15 00:00:00"
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # Format ISO: "2025-01-15T00:00:00" - convert to naive datetime
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                # Remove timezone info to make it naive
                return dt.replace(tzinfo=None)
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return None

    def _map_status(self, status_text: Optional[str]) -> str:
        """
        Mappe le statut de l'API vers nos statuts internes

        API: "En cours", "Clôturée", "À venir", etc.
        BDD: "active", "closed", "upcoming"
        """
        if not status_text:
            return "active"

        status_lower = status_text.lower()

        if "en cours" in status_lower or "ouvert" in status_lower:
            return "active"
        elif "clôtur" in status_lower or "termin" in status_lower:
            return "closed"
        elif "venir" in status_lower or "prochaine" in status_lower:
            return "upcoming"
        else:
            return "active"

    async def upsert_auction(self, auction_raw: Dict[str, Any]) -> Sale:
        """
        Crée ou met à jour une vente dans la BDD

        Args:
            auction_raw: Données brutes de l'API GraphQL

        Returns:
            Instance Sale créée ou mise à jour
        """
        parsed = self._parse_auction_data(auction_raw)
        sale_number = parsed["sale_number"]

        # Chercher si la vente existe déjà
        result = await self.db.execute(
            select(Sale).where(Sale.sale_number == sale_number)
        )
        sale = result.scalar_one_or_none()

        if sale:
            # Mise à jour
            for key, value in parsed.items():
                if key != "sale_number":  # Ne pas modifier la PK
                    setattr(sale, key, value)
            logger.info(f"Updated sale #{sale_number}: {parsed['title']}")
        else:
            # Création
            sale = Sale(**parsed, is_scraped=False, last_scraped_at=None)
            self.db.add(sale)
            logger.info(f"Created sale #{sale_number}: {parsed['title']}")

        await self.db.flush()
        return sale

    async def sync_auctions(
        self,
        filter_status: Optional[List[str]] = None,
        max_pages: Optional[int] = None,
        incremental: bool = False
    ) -> Dict[str, int]:
        """
        Synchronise toutes les ventes de l'API vers la BDD

        Args:
            filter_status: Filtrer par statut
            max_pages: Nombre maximum de pages

        Returns:
            Stats: {"created": X, "updated": Y, "total": Z}
        """
        logger.info("Starting auction synchronization via GraphQL API")

        # Récupérer toutes les ventes
        auctions = await self.fetch_all_auctions(
            filter_status=filter_status,
            max_pages=max_pages,
            incremental=incremental
        )

        stats = {"created": 0, "updated": 0, "total": len(auctions), "errors": 0}

        # Synchroniser chaque vente
        for auction_raw in auctions:
            try:
                # Vérifier si existe déjà
                sale_number = self._to_int(auction_raw.get("dnid_auction_id"))
                result = await self.db.execute(
                    select(Sale.id).where(Sale.sale_number == sale_number)
                )
                exists = result.scalar_one_or_none() is not None

                # Upsert
                await self.upsert_auction(auction_raw)

                if exists:
                    stats["updated"] += 1
                else:
                    stats["created"] += 1

            except Exception as e:
                logger.error(f"Error upserting auction {auction_raw.get('dnid_auction_id')}: {e}")
                stats["errors"] += 1

        # Commit en une seule fois pour performance
        await self.db.commit()

        logger.info(f"Auction sync completed: {stats}")
        return stats


# Alias pour compatibilité avec l'ancien scraper
AuctionGraphQLScraper = GraphQLAuctionScraper
