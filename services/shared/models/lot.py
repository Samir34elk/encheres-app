"""
Modèle Lot - Gestion des lots aux enchères

Ce module définit le modèle Lot représentant un lot/article mis en vente aux enchères.
Un lot appartient à une vente (Sale) et possède des métadonnées sur son état, son prix,
son historique, et les interactions utilisateurs (favoris, commentaires, alertes).

Dépendances SQLAlchemy :
    - Column : Définit une colonne de table
    - Integer, String, DateTime, Text : Types de données
    - ForeignKey : Clé étrangère vers une autre table
    - Index : Index composé pour optimiser les requêtes
    - relationship : Définit les relations avec d'autres modèles

Impact sur la BDD :
    - Table créée : 'lots'
    - Relations :
        * Many-to-One avec Sale (plusieurs lots → une vente)
        * One-to-Many avec Favorite, PriceHistory, Comment, Alert
    - Cascade delete : La suppression d'un lot supprime tous ses favoris, historique de prix,
                       commentaires et alertes associés
    - Index composé : (is_active, last_updated) pour requêtes de recherche optimisées
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Index, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.db.base import Base


class Lot(Base):
    """
    Modèle Lot - Représente un lot/article aux enchères du domaine public

    Centralise toutes les informations d'un lot :
    - Identité : lot_number, title, description
    - Commercial : price, status, depot_location
    - Web : url, image_url
    - Métadonnées : first_seen, last_updated, is_active
    - Popularité : view_count, favorite_count
    - Relations : sale, favorites, price_history, comments, alerts

    Statuts possibles du lot :
    - "available" : Lot disponible pour enchères
    - "sold" : Lot vendu
    - "withdrawn" : Lot retiré de la vente
    - NULL : Statut inconnu (données incomplètes)

    Impact BDD :
    ⚠️ ATTENTION : La suppression d'un Lot entraîne la suppression en cascade de :
    - Tous les favoris associés (Favorite)
    - Tout l'historique de prix (PriceHistory)
    - Tous les commentaires (Comment)
    - Toutes les alertes configurées (Alert)

    ⚠️ ATTENTION : sale_id est NULLABLE. Un lot peut exister sans vente associée
    (vente supprimée ou lot créé manuellement). La suppression d'une vente rend
    les lots orphelins (sale_id = NULL).
    """
    __tablename__ = "lots"  # Nom de la table dans PostgreSQL

    # ========== Colonnes d'Identité ==========

    # id : Clé primaire auto-incrémentée, identifiant unique du lot
    # Impact : Référencé par les FK de favorites, price_history, comments, alerts
    # Note : ID interne, différent du lot_number (numéro officiel)
    id = Column(Integer, primary_key=True, index=True)

    # sale_id : Référence vers la vente à laquelle appartient ce lot
    # Impact : FK vers sales.id, nullable pour permettre les lots orphelins
    # Nullable : True car un lot peut exister sans vente (vente supprimée)
    # Index : Optimise les requêtes "tous les lots d'une vente"
    # Cascade : Pas de cascade delete depuis Sale, le lot devient orphelin
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True, index=True)

    # lot_number : Numéro officiel du lot dans la vente (ex: 42, 123)
    # Impact : Index pour recherche rapide, utilisé dans l'URL (ex: /lot/42)
    # ⚠️ CRITIQUE : Combiné avec sale_id, identifie le lot officiellement
    # Note : Pas unique car plusieurs ventes peuvent avoir un lot #1
    # Utilisation : Affichage "Lot n°42", tri par ordre d'apparition
    lot_number = Column(Integer, index=True, nullable=False)

    # ========== Colonnes de Contenu ==========

    # title : Titre/nom du lot (ex: "Renault Clio 2015")
    # Impact : Index pour recherche full-text, affiché dans toute l'interface
    # Nullable : False car un lot doit avoir un titre
    # Limite : String sans limite (illimité en PostgreSQL)
    # Utilisation : Recherche, affichage liste, détail, SEO
    title = Column(String, nullable=False, index=True)

    # description : Description détaillée du lot (état, options, historique)
    # Impact : Type Text pour supporter de longs textes (>255 chars)
    # Nullable : True car certains lots n'ont pas de description
    # Contenu : Informations techniques, défauts, historique, modalités
    # Utilisation : Page de détail, recherche avancée
    description = Column(Text, nullable=True)

    # categories : Catégories du lot au format JSON (ex: ["Véhicules", "Voitures"])
    # Impact : Permet un filtrage multi-critères et une navigation par catégorie
    # Format : Array JSON de strings
    # Utilisation : Filtres de recherche, facettes, breadcrumb
    categories = Column(JSONB, nullable=True)

    # caracteristiques : Caractéristiques techniques détaillées du lot (format JSON)
    # Impact : Stocke tous les attributs custom de l'API GraphQL
    # Format : Object JSON clé-valeur (ex: {"marque": "Renault", "année": "2015"})
    # Utilisation : Affichage détaillé, filtres avancés, recherche
    caracteristiques = Column(JSONB, nullable=True)

    # professionnel : Indique si le lot est réservé aux professionnels
    # Impact : Filtre d'accès, certains lots ne sont visibles que pour comptes pro
    # Utilisation : Badge "Professionnels uniquement", restrictions d'accès
    professionnel = Column(Boolean, nullable=False, default=False)

    # ========== Colonnes Commerciales ==========

    # price : Prix actuel ou final du lot (en centimes d'euros)
    # Impact : Utilisé pour tri, filtrage, alertes de prix
    # Format : Integer (centimes) pour éviter les erreurs de précision des Float
    # Exemple : 15000 = 150.00€, 1250 = 12.50€
    # Nullable : True car le prix peut être inconnu ou "sur demande"
    # Mise à jour : Génère une entrée PriceHistory à chaque changement
    price = Column(Integer, nullable=True)

    # price_reserve : Prix de réserve du lot (prix minimum pour vente)
    # Impact : Utilisé pour afficher "Prix de réserve" et gérer les enchères
    # Format : Integer (centimes) comme price
    # Nullable : True car tous les lots n'ont pas de prix de réserve
    # Utilisation : Logique d'enchères, affichage conditionnel
    price_reserve = Column(Integer, nullable=True)

    # status : Statut commercial actuel du lot
    # Valeurs : "available", "sold", "withdrawn", NULL
    # Impact : Utilisé pour filtrer les lots actifs/vendus
    # Nullable : True car le statut peut être inconnu (scraping incomplet)
    # Utilisation : Badge de statut UI, filtres de recherche
    status = Column(String, nullable=True)

    # depot_location : Localisation du dépôt/fourrière où se trouve le lot
    # Impact : Index pour recherche géographique (ex: "Paris", "Lyon")
    # Format : Texte libre, dépend de la source de données
    # Nullable : True car la localisation peut être inconnue
    # Utilisation : Filtres géographiques, alertes par localisation
    depot_location = Column(String, nullable=True, index=True)

    # ========== Colonnes Web ==========

    # url : URL de la page officielle du lot sur le site source
    # Impact : Lien externe vers la page d'origine pour plus de détails
    # Nullable : True car certains lots historiques n'ont plus d'URL
    # Format : String sans limite pour supporter les URLs longues
    # Utilisation : Bouton "Voir l'annonce officielle"
    url = Column(String, nullable=True)

    # image_url : URLs des images du lot (array JSON)
    # Impact : Affichées dans les cartes de liste et la galerie de détail
    # Format : JSONB array (ex: ["image1.jpg", "image2.jpg", ...])
    # Changement : String → JSONB pour supporter plusieurs images (GraphQL API)
    # Nullable : True car certains lots n'ont pas d'image
    # Note : Images externes, pas stockées localement (économie de stockage)
    # Utilisation : Vignette (première image), galerie d'images (toutes)
    image_url = Column(JSONB, nullable=True)

    # ========== Colonnes de Métadonnées ==========

    # first_seen : Date de première découverte du lot par le scraper (timestamp UTC)
    # Impact : Index pour tri chronologique "nouveaux lots"
    # Immutable : Ne change jamais après création (date de scraping initial)
    # Utilisation : Filtrer "lots ajoutés cette semaine", audit
    # ⚠️ Différent de created_at : first_seen = date sur le site, created_at = date en BDD
    first_seen = Column(DateTime, default=datetime.utcnow, index=True)

    # last_updated : Date de dernière modification du lot (timestamp UTC)
    # Impact : Auto-update à chaque UPDATE via onupdate
    # Utilisation : Détecter les lots récemment modifiés, tri par fraîcheur
    # Trigger : Mis à jour automatiquement lors de tout changement (prix, statut, etc.)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # is_active : Flag d'archivage (0 = archivé, 1 = actif)
    # Impact : Utilisé pour soft delete (archivage sans suppression réelle)
    # Type : Integer au lieu de Boolean pour compatibilité avec anciens systèmes
    # Valeurs : 0 = archived (masqué), 1 = active (visible)
    # Utilisation : Filtrer les lots actifs, archiver les ventes terminées
    # Migration : Devrait être Boolean mais gardé en Integer pour compatibilité
    is_active = Column(Integer, default=1)

    # ========== Colonnes de Popularité ==========

    # view_count : Compteur de vues du lot par les utilisateurs
    # Impact : Métrique de popularité, utilisée pour tri "plus vus"
    # Maintenance : Incrémenté à chaque affichage de la page de détail
    # Utilisation : Top des lots populaires, recommandations
    # Performance : Dénormalisé pour éviter les COUNT(*) coûteux
    view_count = Column(Integer, default=0)

    # favorite_count : Nombre d'utilisateurs ayant mis ce lot en favori
    # Impact : Métrique de popularité, badge "X personnes suivent ce lot"
    # Maintenance : Mis à jour lors de l'ajout/suppression d'un Favorite
    # Utilisation : Tri par popularité, statistiques
    # Performance : Dénormalisé pour éviter les COUNT(*) sur table favorites
    favorite_count = Column(Integer, default=0)

    # ========== Relations SQLAlchemy ==========

    # sale : Vente à laquelle appartient ce lot (relation Many-to-One)
    # Type : Many-to-One (plusieurs lots → une sale)
    # back_populates : Relation bidirectionnelle avec Sale.lots
    # Impact BDD : FK sale_id → sales.id
    # Nullable : True, un lot peut être orphelin (sale_id = NULL)
    # Cascade : Pas de cascade depuis Sale, le lot survit à la suppression de la vente
    sale = relationship("Sale", back_populates="lots")

    # favorites : Liste des favoris pointant vers ce lot
    # Type : One-to-Many (un lot a plusieurs favoris)
    # Cascade : "all, delete-orphan" = suppression du lot → suppression de tous ses favoris
    # back_populates : Relation bidirectionnelle avec Favorite.lot
    # Impact BDD : FK dans table favorites (lot_id → lots.id ON DELETE CASCADE)
    # ⚠️ Suppression du lot = perte de tous les favoris associés
    favorites = relationship("Favorite", back_populates="lot", cascade="all, delete-orphan")

    # price_history : Historique des changements de prix du lot
    # Type : One-to-Many (un lot a plusieurs entrées d'historique)
    # Cascade : Suppression du lot → suppression de tout son historique de prix
    # Utilisation : Graphiques d'évolution, détection de baisse de prix
    # Impact BDD : FK dans table price_history (lot_id → lots.id ON DELETE CASCADE)
    price_history = relationship("PriceHistory", back_populates="lot", cascade="all, delete-orphan")

    # comments : Liste des commentaires postés sur ce lot
    # Type : One-to-Many (un lot a plusieurs commentaires)
    # Cascade : Suppression du lot → suppression de tous ses commentaires
    # back_populates : Relation bidirectionnelle avec Comment.lot
    # Impact BDD : FK dans table comments (lot_id → lots.id ON DELETE CASCADE)
    comments = relationship("Comment", back_populates="lot", cascade="all, delete-orphan")

    # alerts : Liste des alertes configurées pour ce lot
    # Type : One-to-Many (un lot a plusieurs alertes)
    # Cascade : Suppression du lot → suppression de toutes ses alertes
    # Utilisation : Notifications de changement de prix/statut
    # Impact BDD : FK dans table alerts (lot_id → lots.id ON DELETE CASCADE)
    alerts = relationship("Alert", back_populates="lot", cascade="all, delete-orphan")

    # ========== Index et Contraintes ==========

    # Index composé pour optimiser les requêtes fréquentes :
    # - Recherche des lots actifs récemment mis à jour
    # - Tri par fraîcheur dans la liste des lots actifs
    # Impact Performance : Accélère les requêtes "SELECT * FROM lots WHERE is_active=1 ORDER BY last_updated DESC"
    # Note : PostgreSQL supporte aussi les index GIN trigram (pg_trgm) pour recherche full-text,
    #        mais non utilisé ici pour compatibilité avec les tiers gratuits
    __table_args__ = (
        Index('idx_lot_active', 'is_active', 'last_updated'),
    )

    def __repr__(self):
        """
        Représentation textuelle de l'objet Lot pour le debugging

        Returns:
            str : Format "<Lot {lot_number}: {title}>"

        Utilisation : Affichage dans les logs, debugging, shell interactif
        Exemple : <Lot 42: Renault Clio 2015>
        """
        return f"<Lot {self.lot_number}: {self.title}>"
