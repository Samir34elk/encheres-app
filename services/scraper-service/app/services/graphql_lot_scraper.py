"""
GraphQL Lot Scraper - Récupération des détails des lots via GraphQL

Ce module récupère les informations détaillées de chaque lot via l'API GraphQL.
Complète le GraphQLAuctionScraper en ajoutant les détails des lots.
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.lot import Lot
from app.models.sale import Sale
from app.models.price_history import PriceHistory
from app.services.notification_service import NotificationService
from app.core.config import settings
from app.services.polite_client import ScraperPausedError, polite_client

logger = logging.getLogger(__name__)


class GraphQLLotScraper:
    """
    Scraper GraphQL pour récupérer les détails des lots

    Utilise l'API GraphQL getProductPageMain pour chaque lot.
    """

    BASE_URL = settings.AUCTION_GRAPHQL_URL
    IMAGE_PREFIX = "https://encheres-domaine.gouv.fr/admin/media/products/"

    # Requête GraphQL pour lister les lots d'une vente (NOUVELLE!)
    AUCTION_LOTS_QUERY = """
    query getAuctionLots(
      $currentPage: Int
      $filter: ProductAttributeFilterInput
      $pageSize: Int
      $sort: ProductAttributeSortInput
    ) {
      products(
        currentPage: $currentPage
        filter: $filter
        pageSize: $pageSize
        sort: $sort
      ) {
        items {
          __typename
          auction
          lot_number
          name
          url_key
          sku
          auction_type
          auction_auto_status
          lot_status
          lot_status_label
          price_auction
          reserve_price
          last_bid
          bid_winner_amount
          has_won
          has_lost
          professional_only
          luxury
          luxury_label
          start_date
          end_date
          start_auction_lot_at
          end_auction_lot_at
          offers_submission_deadline
          location
          dropoff_location {
            city
            postcode
            __typename
          }
          small_image {
            url
            __typename
          }
          sales_inspector_data {
            cav_name
            __typename
          }
          description {
            html
            __typename
          }
          short_description {
            html
            __typename
          }
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

    # Template d'URL pour getProductPageMain (optimisé)
    URL_TEMPLATE = (
        settings.AUCTION_GRAPHQL_URL +
        "?query=query+getProductPageMain%28%24urlKey%3AString%21%29%7B"
        "products%28filter%3A%7Burl_key%3A%7Beq%3A%24urlKey%7D%7D%29%7B"
        "items%7Buid+__typename+auction_type+categories%7Buid+name+url_key+url_path+__typename%7D"
        "custom_attributes%7Battribute_metadata%7Buid+code+label+data_type+__typename%7D"
        "entered_attribute_value%7Bvalue+__typename%7D"
        "selected_attribute_options%7Battribute_option%7Buid+label+__typename%7D__typename%7D__typename%7D"
        "description%7Bhtml+__typename%7D"
        "dropoff_location_fo%7Baddress+city+name+postcode+__typename%7D"
        "id+lot_number+media_gallery_entries%7Bfile+label+position+__typename%7D"
        "name+professional_only+short_description%7Bhtml+__typename%7D"
        "sku+state_property_tax+url_key%7D__typename%7D%7D"
        "&operationName=getProductPageMain"
        "&variables=%7B%22urlKey%22%3A%22{urlKey}%22%7D"
    )

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)

    async def close(self):
        """Conservé pour compatibilité : le client HTTP est partagé (polite_client)."""

    async def fetch_lots_from_auction(
        self,
        auction_id: str,
        page: int = 1,
        page_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Récupère tous les lots d'une vente via GraphQL (NOUVELLE MÉTHODE!)

        Cette méthode utilise la requête getAuctionLots découverte qui permet
        de lister TOUS les lots d'une vente sans scraping HTML!

        Args:
            auction_id: ID de la vente (ex: "152")
            page: Numéro de page
            page_size: Nombre de lots par page (max 1000)

        Returns:
            Dict avec items, page_info, total_count
        """
        variables = {
            "currentPage": page,
            "pageSize": page_size,
            "sort": {"lot_number": "ASC"},
            "filter": {
                "auction": {"eq": str(auction_id)}
            }
        }

        params = {
            "query": self.AUCTION_LOTS_QUERY,
            "operationName": "getAuctionLots",
            "variables": json.dumps(variables)
        }

        logger.info(f"Fetching lots for auction {auction_id} (page {page}, size {page_size})")
        data = await polite_client.get_json(self.BASE_URL, params=params)

        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            raise Exception(f"GraphQL errors: {data['errors']}")

        products_data = (data.get("data") or {}).get("products") or {}
        logger.info(
            f"Fetched {len(products_data.get('items', []))} lots "
            f"(total: {products_data.get('total_count', 0)})"
        )
        return products_data

    async def fetch_all_lots_from_auction(
        self,
        auction_id: str,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère TOUS les lots d'une vente (pagination automatique)

        Args:
            auction_id: ID de la vente (ex: "152")
            max_pages: Nombre maximum de pages (None = toutes)

        Returns:
            Liste complète de tous les lots
        """
        all_lots = []
        page = 1

        while True:
            data = await self.fetch_lots_from_auction(
                auction_id=auction_id,
                page=page,
                page_size=1000
            )

            items = data.get("items", [])
            if not items:
                break

            all_lots.extend(items)

            # Vérifier s'il y a d'autres pages
            page_info = data.get("page_info", {})
            total_pages = page_info.get("total_pages", 1)

            if page >= total_pages or (max_pages and page >= max_pages):
                break

            page += 1

        logger.info(f"Fetched total of {len(all_lots)} lots for auction {auction_id}")
        return all_lots

    async def fetch_lot_details(self, url_key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un lot via GraphQL

        Args:
            url_key: Clé URL du lot (ex: "250769bi02400")

        Returns:
            Dict avec les détails du lot, ou None si erreur
        """
        url = self.URL_TEMPLATE.format(urlKey=url_key)

        try:
            logger.info(f"Fetching lot details for url_key: {url_key}")
            data = await polite_client.get_json(url)

            if "errors" in data:
                logger.error(f"GraphQL errors for {url_key}: {data['errors']}")
                return None

            items = data.get("data", {}).get("products", {}).get("items", [])
            if not items:
                logger.warning(f"No product found for url_key: {url_key}")
                return None

            product = items[0]
            logger.info(f"Successfully fetched lot: {product.get('name')}")
            return product

        except ScraperPausedError:
            raise
        except Exception as e:
            logger.error(f"Error fetching lot {url_key}: {e}")
            return None

    def _extract_lot_number(self, url_key: str, sku: Optional[str] = None) -> Optional[int]:
        """
        Extrait le numéro de lot depuis url_key ou SKU

        Args:
            url_key: Clé URL (ex: "250769bi02400")
            sku: SKU optionnel

        Returns:
            Numéro de lot (int) ou None
        """
        # Essayer d'extraire depuis url_key (format: {sale_number}bi{lot_number})
        # Exemple: "250769bi02400" -> lot_number = 2400
        import re
        if url_key:
            match = re.search(r'bi(\d+)', url_key)
            if match:
                return int(match.group(1))

        # Fallback: essayer depuis SKU
        if sku:
            match = re.search(r'\d+', sku)
            if match:
                return int(match.group())

        return None

    def _parse_custom_attributes(self, custom_attrs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse les custom_attributes de l'API en dict clé-valeur

        Args:
            custom_attrs: Liste des custom_attributes de l'API

        Returns:
            Dict clé-valeur (ex: {"marque": "Renault", "annee": "2015"})
        """
        result = {}

        for attr in custom_attrs:
            meta = attr.get("attribute_metadata") or {}
            code = meta.get("code")

            if not code:
                continue

            value = ""

            # Valeur entrée directement
            entered = attr.get("entered_attribute_value")
            if entered and isinstance(entered, dict):
                val = entered.get("value")
                if val is not None:
                    value = val

            # Ou valeur depuis options sélectionnées
            if not value:
                selected = attr.get("selected_attribute_options")
                if selected and isinstance(selected, dict):
                    opts = selected.get("attribute_option")
                    if isinstance(opts, list):
                        labels = [opt.get("label") for opt in opts if opt.get("label")]
                        if labels:
                            value = " | ".join(labels)

            # Ajouter au résultat
            if value:
                result[code] = value
                # Aussi ajouter le label si disponible
                label = meta.get("label")
                if label:
                    result[f"{code}_label"] = label

        return result

    def _parse_price_value(self, value: Optional[Any]) -> Optional[int]:
        """
        Convertit un prix GraphQL en entier (euros).

        Args:
            value: Valeur retournée par GraphQL (str, float, int)

        Returns:
            Montant en euros (int) ou None si invalide.
        """
        if value in (None, ""):
            return None

        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None

        integral_value = decimal_value.to_integral_value(rounding=ROUND_HALF_UP)
        return int(integral_value)

    def _parse_categories(self, categories: List[Dict[str, Any]]) -> List[str]:
        """Parse les catégories en liste de noms"""
        return [cat.get("name") for cat in categories if cat.get("name")]

    def _parse_images(self, media_entries: List[Dict[str, Any]]) -> List[str]:
        """
        Parse les images en liste d'URLs complètes

        Args:
            media_entries: media_gallery_entries de l'API

        Returns:
            Liste d'URLs complètes
        """
        images = []
        for entry in media_entries:
            file_path = entry.get("file")
            if file_path:
                # Note: Le préfixe peut varier, vérifier sur le site réel
                full_url = self.IMAGE_PREFIX + file_path
                images.append(full_url)

        return images

    def _parse_dropoff_location(self, dropoff_fo: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Parse la localisation du dépôt

        Args:
            dropoff_fo: dropoff_location_fo de l'API

        Returns:
            String formaté (ex: "Paris 75001") ou None
        """
        if not dropoff_fo:
            return None

        city = dropoff_fo.get("city", "")
        postcode = dropoff_fo.get("postcode", "")
        name = dropoff_fo.get("name", "")

        if city and postcode:
            return f"{city} {postcode}"
        elif city:
            return city
        elif name:
            return name

        return None

    def _parse_lot_data(self, product: Dict[str, Any], sale_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Parse les données brutes de l'API en format compatible BDD

        Args:
            product: Données brutes de l'API GraphQL
            sale_id: ID de la vente parente (optionnel)

        Returns:
            Dict avec les champs pour le modèle Lot
        """
        url_key = product.get("url_key", "")
        lot_number = self._extract_lot_number(url_key, product.get("sku"))

        # Description (HTML -> texte brut)
        desc_html = product.get("description", {}).get("html", "")
        short_desc_html = product.get("short_description", {}).get("html", "")
        description = desc_html or short_desc_html

        # Catégories
        categories = self._parse_categories(product.get("categories", []))

        # Caractéristiques détaillées
        caracteristiques = self._parse_custom_attributes(product.get("custom_attributes", []))

        # Images
        images = self._parse_images(product.get("media_gallery_entries", []))

        # Prix actuel (last_bid prioritaire sinon price_auction), en euros
        price = self._parse_price_value(product.get("last_bid"))
        if price is None:
            price = self._parse_price_value(product.get("price_auction"))

        # Localisation
        depot_location = self._parse_dropoff_location(product.get("dropoff_location_fo"))

        return {
            "sale_id": sale_id,
            "lot_number": lot_number,
            "title": product.get("name"),
            "description": description,
            "categories": categories if categories else None,
            "caracteristiques": caracteristiques if caracteristiques else None,
            "professionnel": product.get("professional_only", False),
            "price": price,
            "status": "available",  # Par défaut
            "depot_location": depot_location,
            "url": f"https://encheres-domaine.gouv.fr/lot/{url_key}",
            "image_url": images if images else None,
            "is_active": 1,
            "last_updated": datetime.utcnow()
        }

    async def upsert_lot(
        self,
        product: Dict[str, Any],
        sale_id: Optional[int] = None
    ) -> Optional[Lot]:
        """
        Crée ou met à jour un lot dans la BDD

        Args:
            product: Données brutes de l'API GraphQL
            sale_id: ID de la vente parente

        Returns:
            Instance Lot créée ou mise à jour, ou None si erreur
        """
        try:
            parsed = self._parse_lot_data(product, sale_id)

            if not parsed["lot_number"]:
                logger.warning(f"Could not extract lot_number from {product.get('url_key')}")
                return None

            # Chercher si le lot existe déjà
            query = select(Lot).where(Lot.lot_number == parsed["lot_number"])
            if sale_id:
                query = query.where(Lot.sale_id == sale_id)

            result = await self.db.execute(query)
            lot = result.scalar_one_or_none()

            if lot:
                # Mise à jour
                previous_price = lot.price

                for key, value in parsed.items():
                    if key not in ["lot_number", "sale_id"]:
                        setattr(lot, key, value)

                # Track price change
                if parsed["price"] and parsed["price"] != previous_price:
                    price_history = PriceHistory(
                        lot_id=lot.id,
                        price=parsed["price"],
                        status=parsed["status"]
                    )
                    self.db.add(price_history)

                    # Trigger alerts
                    await self.notification_service.trigger_price_alerts(
                        lot, parsed["price"], previous_price
                    )

                logger.info(f"Updated lot #{parsed['lot_number']}: {parsed['title']}")
            else:
                # Création
                lot = Lot(**parsed)
                self.db.add(lot)
                await self.db.flush()

                # Initial price history
                if parsed["price"]:
                    price_history = PriceHistory(
                        lot_id=lot.id,
                        price=parsed["price"],
                        status=parsed["status"]
                    )
                    self.db.add(price_history)

                # Trigger new lot alerts
                await self.notification_service.trigger_new_lot_alerts(lot)

                logger.info(f"Created lot #{parsed['lot_number']}: {parsed['title']}")

            await self.db.flush()
            return lot

        except Exception as e:
            logger.error(f"Error upserting lot: {e}")
            return None

    async def sync_lot_by_url_key(self, url_key: str, sale_id: Optional[int] = None) -> Optional[Lot]:
        """
        Synchronise un lot spécifique par son url_key

        Args:
            url_key: Clé URL du lot
            sale_id: ID de la vente parente (optionnel)

        Returns:
            Lot synchronisé ou None si erreur
        """
        product = await self.fetch_lot_details(url_key)
        if not product:
            return None

        lot = await self.upsert_lot(product, sale_id)
        await self.db.commit()

        return lot

    def _parse_auction_lot_data(self, lot_data: Dict[str, Any], sale_id: int) -> Dict[str, Any]:
        """
        Parse les données d'un lot depuis getAuctionLots (format simplifié)

        Args:
            lot_data: Données brutes du lot depuis getAuctionLots
            sale_id: ID de la vente parente

        Returns:
            Dict avec les champs pour le modèle Lot
        """
        # Description
        desc = lot_data.get("description") or {}
        short_desc = lot_data.get("short_description") or {}
        description = desc.get("html", "") or short_desc.get("html", "")

        # Prix courant: privilégier last_bid sinon price_auction (tous en euros)
        price = self._parse_price_value(lot_data.get("last_bid"))
        if price is None:
            price = self._parse_price_value(lot_data.get("price_auction"))

        # Prix de réserve - également en euros
        price_reserve = self._parse_price_value(lot_data.get("reserve_price"))

        # Localisation
        dropoff = lot_data.get("dropoff_location") or {}
        city = dropoff.get("city", "")
        postcode = dropoff.get("postcode", "")
        depot_location = f"{city} {postcode}".strip() if city or postcode else None

        # Image
        small_image = lot_data.get("small_image") or {}
        image_url = small_image.get("url")
        images = [image_url] if image_url else None

        return {
            "sale_id": sale_id,
            "lot_number": lot_data.get("lot_number"),
            "title": lot_data.get("name"),
            "description": description,
            "professionnel": lot_data.get("professional_only", False),
            "price": price,
            "price_reserve": price_reserve,
            "status": lot_data.get("lot_status_label", "available"),
            "depot_location": depot_location,
            "url": f"https://encheres-domaine.gouv.fr/lot/{lot_data.get('url_key')}",
            "image_url": images,
            "is_active": 1,
            "last_updated": datetime.utcnow()
        }

    async def sync_auction_lots(
        self,
        auction_id: str,
        sale_id: int,
        fetch_full_details: bool = False
    ) -> Dict[str, int]:
        """
        Synchronise TOUS les lots d'une vente via GraphQL (100% GraphQL!)

        Workflow:
        1. Récupère la liste complète des lots via getAuctionLots
        2. Parse chaque lot
        3. Upsert en BDD avec association à la vente (sale_id)
        4. (Optionnel) Récupère les détails complets via getProductPageMain

        Args:
            auction_id: ID de la vente dans l'API (ex: "152")
            sale_id: ID de la vente dans notre BDD
            fetch_full_details: Si True, récupère aussi les custom_attributes

        Returns:
            Stats: {"new_lots": X, "updated_lots": Y, "total": Z}
        """
        logger.info(f"🔄 Syncing lots for auction {auction_id} (sale_id: {sale_id})")

        # Récupérer tous les lots
        lots = await self.fetch_all_lots_from_auction(auction_id)

        stats = {"new_lots": 0, "updated_lots": 0, "total": len(lots), "errors": 0}

        for lot_data in lots:
            try:
                lot_number = lot_data.get("lot_number")

                # Chercher si le lot existe déjà
                result = await self.db.execute(
                    select(Lot).where(
                        Lot.lot_number == lot_number,
                        Lot.sale_id == sale_id
                    )
                )
                existing_lot = result.scalar_one_or_none()

                # Parser les données
                parsed = self._parse_auction_lot_data(lot_data, sale_id)

                if existing_lot:
                    # Mise à jour
                    previous_price = existing_lot.price

                    for key, value in parsed.items():
                        if key not in ["lot_number", "sale_id"]:
                            setattr(existing_lot, key, value)

                    # Track price change
                    if parsed["price"] and parsed["price"] != previous_price:
                        price_history = PriceHistory(
                            lot_id=existing_lot.id,
                            price=parsed["price"],
                            status=parsed["status"]
                        )
                        self.db.add(price_history)

                        # Trigger alerts
                        await self.notification_service.trigger_price_alerts(
                            existing_lot, parsed["price"], previous_price
                        )

                    stats["updated_lots"] += 1
                else:
                    # Création
                    new_lot = Lot(**parsed)
                    self.db.add(new_lot)
                    await self.db.flush()

                    # Initial price history
                    if parsed["price"]:
                        price_history = PriceHistory(
                            lot_id=new_lot.id,
                            price=parsed["price"],
                            status=parsed["status"]
                        )
                        self.db.add(price_history)

                    # Trigger alerts
                    await self.notification_service.trigger_new_lot_alerts(new_lot)

                    stats["new_lots"] += 1
                    existing_lot = new_lot

                # Optionnel: récupérer les détails complets (custom_attributes)
                if fetch_full_details:
                    url_key = lot_data.get("url_key")
                    if url_key:
                        product = await self.fetch_lot_details(url_key)
                        if product:
                            # Mettre à jour avec les données complètes
                            caracteristiques = self._parse_custom_attributes(
                                product.get("custom_attributes", [])
                            )
                            categories = self._parse_categories(
                                product.get("categories", [])
                            )
                            if caracteristiques:
                                existing_lot.caracteristiques = caracteristiques
                            if categories:
                                existing_lot.categories = categories

            except ScraperPausedError:
                await self.db.commit()
                raise
            except Exception as e:
                logger.error(f"Error syncing lot {lot_data.get('lot_number')}: {e}")
                stats["errors"] += 1

        # Commit en une seule fois
        await self.db.commit()

        logger.info(f"✅ Synced {stats['total']} lots: {stats['new_lots']} new, {stats['updated_lots']} updated")
        return stats
