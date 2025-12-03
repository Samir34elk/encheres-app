from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.db.base import Base


class Sale(Base):
    __tablename__ = "sales"  # Nom de la table dans PostgreSQL

    # ========== Colonnes d'Identité ==========

    # id : Clé primaire auto-incrémentée, identifiant interne unique
    # Impact : Référencé par lots.sale_id (FK nullable)
    # Note : ID interne, différent du sale_number officiel
    id = Column(Integer, primary_key=True, index=True)

    # sale_number : Numéro officiel de la vente (ex: 240515 pour 15 mai 2024)
    # ⚠️ CRITIQUE : Utilisé par le scraper pour identifier les ventes
    # Format typique : YYMMDD ou numéro séquentiel selon la source
    sale_number = Column(Integer, nullable=False, index=True)

    # title : Titre de la vente (ex: "Vente de véhicules - Paris")
    # Impact : Affiché dans l'interface utilisateur, limité à 255 caractères
    # Utilisation : Liste des ventes, recherche, SEO
    title = Column(String(255), nullable=False)

    # description : Description détaillée de la vente (optionnelle)
    # Impact : Type Text pour supporter de longs textes (>255 chars)
    # Contenu : Conditions de vente, modalités, informations pratiques
    # Nullable : Certaines ventes n'ont pas de description
    description = Column(Text, nullable=True)

    # organiser : Organisateur de la vente (commissaire-priseur ou institution)
    # Impact : Affiché dans l'interface, permet filtrage par organisateur
    # Format : String (ex: "CAV Paris", "Domaine Public")
    # Source : sales_inspector_label depuis l'API GraphQL
    # Utilisation : Affichage, filtres, statistiques par organisateur
    organiser = Column(String(255), nullable=False)

    # type_vente : Type de vente (ex: "Enchères", "Vente amiable", "Adjudication")
    # Impact : Permet de différencier les types de procédures de vente
    # Format : String limité à 50 caractères
    # Source : type_text depuis l'API GraphQL
    # Utilisation : Filtres, badges de type
    type_vente = Column(String(50), nullable=True)

    # categories : Catégories de la vente au format JSON (ex: ["Véhicules", "Mobilier"])
    # Impact : Navigation par catégorie, filtres multi-critères
    # Format : JSONB array de strings
    # Source : categories[].name depuis l'API GraphQL
    # Utilisation : Facettes de recherche, breadcrumb, filtres
    categories = Column(JSONB, nullable=True)

    # image_url : URL de l'image de présentation de la vente
    # Impact : Vignette dans la liste des ventes
    # Format : String URL complète (préfixe + image_path de l'API)
    # Source : image_path depuis l'API GraphQL
    # Utilisation : Affichage liste des ventes, page de détail
    image_url = Column(String(500), nullable=True)

    # ========== Colonnes Temporelles ==========

    # start_date : Date et heure de début de la vente (timezone-aware UTC)
    # Impact : Utilisé pour filtrer les ventes à venir / en cours
    # Nullable : Certaines ventes n'ont pas de date précise
    # Note : Toujours stocker en UTC, convertir en local côté frontend
    start_date = Column(DateTime, nullable=True)

    # end_date : Date et heure de fin de la vente (timezone-aware UTC)
    # Impact : Utilisé pour identifier les ventes terminées
    # Logique : Si end_date < now() → status peut passer à "closed"
    # Nullable : Certaines ventes ont une durée indéterminée
    end_date = Column(DateTime, nullable=True)

    # ========== Colonnes de Statut ==========

    # status : État actuel de la vente
    # Valeurs : "active" (défaut), "closed", "upcoming"
    # Impact : Utilisé pour filtrer les ventes dans l'UI
    # Migration : Si vous ajoutez un statut, mettez à jour les filtres
    # Limite : 50 caractères pour éviter les valeurs trop longues
    status = Column(String(50), default="active")

    # total_lots : Nombre total de lots dans cette vente
    # Impact : Compteur dénormalisé pour éviter les COUNT(*) coûteux
    # Maintenance : Mis à jour lors de l'ajout/suppression de lots
    # Utilisation : Affichage rapide "123 lots disponibles"
    # Default : 0 pour les ventes nouvellement créées
    total_lots = Column(Integer, default=0)

    # ========== Colonnes de Scraping ==========

    # url : URL de la page web de la vente sur le site officiel
    # Impact : Utilisée par le scraper pour récupérer les données
    # ⚠️ CRITIQUE : Sans URL, le scraper ne peut pas mettre à jour la vente
    # Format : String(500) pour supporter les URLs longues avec paramètres
    # Nullable : Certaines ventes historiques peuvent ne plus avoir d'URL
    url = Column(String(500), nullable=True)

    # is_scraped : Flag indiquant si la vente a déjà été scrapée
    # Impact : Utilisé par le scraper pour éviter de scraper deux fois
    # Workflow : False → scraping en attente, True → scraping effectué
    # Reset : Peut être remis à False pour forcer un re-scraping
    is_scraped = Column(Boolean, default=False)

    # last_scraped_at : Date du dernier scraping réussi (timestamp UTC)
    # Impact : Permet de déterminer si un re-scraping est nécessaire
    # Logique : Si (now() - last_scraped_at) > 24h → re-scraper
    # Nullable : NULL si jamais scrapé (cohérent avec is_scraped=False)
    last_scraped_at = Column(DateTime, nullable=True)

    # ========== Colonnes d'Audit ==========

    # created_at : Date de création de l'enregistrement (timestamp UTC)
    # Impact : Auto-généré par PostgreSQL via func.now()
    # server_default : Valeur calculée côté BDD, pas par Python
    # Immutable : Ne change jamais après l'insertion
    # Utilisation : Audit, statistiques, tri par ancienneté
    created_at = Column(DateTime, server_default=func.now())

    # updated_at : Date de dernière modification (timestamp UTC)
    # Impact : Auto-update à chaque UPDATE via onupdate=func.now()
    # server_default : Valeur initiale = created_at lors de l'INSERT
    # onupdate : Recalculé automatiquement lors de tout UPDATE
    # Utilisation : Détection de changements récents, audit
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # ========== Relations SQLAlchemy ==========

    # lots : Liste des lots appartenant à cette vente
    # Type : One-to-Many (une sale a plusieurs lots)
    # back_populates : Relation bidirectionnelle avec Lot.sale
    # Impact BDD : FK dans table lots (sale_id → sales.id)
    # PAS de cascade delete : Si on supprime la sale, les lots restent
    # Justification : Conservation de l'historique des lots même si vente supprimée
    # Note : lot.sale_id devient NULL si la vente est supprimée
    lots = relationship("Lot", back_populates="sale")
