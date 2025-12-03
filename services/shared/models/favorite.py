"""
Modèle Favorite - Gestion des favoris utilisateur

Ce module définit le modèle Favorite représentant les lots mis en favoris par les utilisateurs.
Permet aux utilisateurs de sauvegarder des lots d'intérêt, d'ajouter des tags personnalisés
et des notes privées pour organiser leur veille.

Fonctionnalités :
    - Sauvegarde de lots favoris pour suivi rapide
    - Tags personnalisés pour catégorisation (ex: "à surveiller", "bonne affaire")
    - Notes privées pour mémoriser des informations importantes
    - Contrainte d'unicité : un utilisateur ne peut favoriser un lot qu'une seule fois

Dépendances SQLAlchemy :
    - Column : Définit une colonne de table
    - Integer, String, DateTime : Types de données
    - ForeignKey : Clé étrangère vers User et Lot
    - UniqueConstraint : Contrainte d'unicité composée (user_id, lot_id)
    - relationship : Définit les relations avec d'autres modèles

Impact sur la BDD :
    - Table créée : 'favorites'
    - Relations :
        * Many-to-One avec User (plusieurs favoris → un utilisateur)
        * Many-to-One avec Lot (plusieurs favoris → un lot)
    - Cascade delete : Suppression de l'utilisateur OU du lot → suppression du favori
    - Contrainte unique : (user_id, lot_id) = un utilisateur ne peut favoriser un lot qu'une fois
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.db.base import Base


class Favorite(Base):
    """
    Modèle Favorite - Représente un lot mis en favori par un utilisateur

    Table de liaison enrichie entre User et Lot avec métadonnées personnalisables.
    Permet aux utilisateurs de créer leur propre "watchlist" de lots aux enchères.

    Cas d'usage :
    - Utilisateur découvre un lot intéressant → ajoute en favori
    - Utilisateur ajoute tag "urgent" pour lots à surveiller de près
    - Utilisateur note "prix trop élevé, attendre baisse" dans notes
    - Utilisateur consulte sa liste de favoris filtrée par tags

    Contraintes :
    - Un utilisateur ne peut favoriser un même lot qu'une seule fois
    - Tentative de doublon → erreur d'intégrité (UniqueConstraint)

    Impact BDD :
    ⚠️ ATTENTION : La suppression de l'utilisateur OU du lot entraîne la suppression
    automatique du favori (ON DELETE CASCADE sur les deux FK).

    ⚠️ ATTENTION : La modification de lot.favorite_count doit être synchronisée :
    - Ajout de favori → incrémenter lot.favorite_count
    - Suppression de favori → décrémenter lot.favorite_count
    """
    __tablename__ = "favorites"  # Nom de la table dans PostgreSQL

    # ========== Colonnes d'Identité ==========

    # id : Clé primaire auto-incrémentée, identifiant unique du favori
    # Impact : Utilisé pour supprimer un favori spécifique
    # Note : Alternative = utiliser (user_id, lot_id) comme clé primaire composée
    #        mais PK simple facilite les opérations CRUD
    id = Column(Integer, primary_key=True, index=True)

    # user_id : Référence vers l'utilisateur ayant mis le lot en favori
    # Impact : FK vers users.id avec CASCADE DELETE
    # Nullable : False car un favori doit appartenir à un utilisateur
    # Cascade : Suppression de l'utilisateur → suppression de tous ses favoris
    # Index : Créé automatiquement par la FK pour optimiser les requêtes
    # ⚠️ CRITIQUE : ON DELETE CASCADE côté BDD pour cohérence des données
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # lot_id : Référence vers le lot mis en favori
    # Impact : FK vers lots.id avec CASCADE DELETE
    # Nullable : False car un favori doit référencer un lot
    # Cascade : Suppression du lot → suppression de tous ses favoris
    # Index : Créé automatiquement par la FK pour optimiser les requêtes
    # ⚠️ CRITIQUE : ON DELETE CASCADE côté BDD pour cohérence des données
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=False)

    # ========== Colonnes de Métadonnées Personnalisables ==========

    # tags : Tags/étiquettes personnalisés pour catégoriser les favoris
    # Impact : Permet de filtrer les favoris par catégorie
    # Format : String libre, conventions recommandées :
    #   - Liste séparée par virgules : "urgent,bonne affaire,à vérifier"
    #   - Ou JSON array : ["urgent", "bonne affaire"]
    # Nullable : True car les tags sont optionnels
    # Exemples : "à surveiller", "deal", "potentiel", "urgent", "paris"
    # Utilisation : Filtrage "mes favoris avec tag 'urgent'", organisation personnelle
    tags = Column(String, nullable=True)

    # notes : Notes privées de l'utilisateur sur le lot
    # Impact : Mémorisation d'informations personnelles non partagées
    # Format : Texte libre
    # Nullable : True car les notes sont optionnelles
    # Exemples :
    #   - "Prix trop élevé, attendre une baisse"
    #   - "Vérifier l'état avant d'enchérir"
    #   - "Contact vendeur: 06.XX.XX.XX.XX"
    # Utilisation : Rappels personnels, aide-mémoire
    # Limite : String (pas Text) pour notes courtes, migrer vers Text si besoin de texte long
    notes = Column(String, nullable=True)

    # ========== Colonnes d'Audit ==========

    # created_at : Date d'ajout du favori (timestamp UTC)
    # Impact : Index pour tri chronologique "derniers favoris ajoutés"
    # Immutable : Ne change jamais après création
    # Utilisation :
    #   - Tri "mes favoris récents"
    #   - Statistiques "favoris ajoutés cette semaine"
    #   - Nettoyage automatique des vieux favoris (lots vendus depuis longtemps)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # ========== Relations SQLAlchemy ==========

    # user : Utilisateur ayant créé ce favori (relation Many-to-One)
    # Type : Many-to-One (plusieurs favoris → un user)
    # back_populates : Relation bidirectionnelle avec User.favorites
    # Impact BDD : FK user_id → users.id ON DELETE CASCADE
    # Cascade : Géré au niveau BDD (ondelete="CASCADE" dans ForeignKey)
    # Suppression user → suppression automatique de tous ses favoris
    user = relationship("User", back_populates="favorites")

    # lot : Lot mis en favori (relation Many-to-One)
    # Type : Many-to-One (plusieurs favoris → un lot)
    # back_populates : Relation bidirectionnelle avec Lot.favorites
    # Impact BDD : FK lot_id → lots.id ON DELETE CASCADE
    # Cascade : Suppression du lot → suppression de tous ses favoris
    # ⚠️ ATTENTION : Penser à décrémenter lot.favorite_count lors de la cascade
    lot = relationship("Lot", back_populates="favorites")

    # ========== Contraintes ==========

    # Contrainte d'unicité composée : (user_id, lot_id)
    # Impact : Empêche un utilisateur de favoriser deux fois le même lot
    # Nom : 'uq_user_lot_favorite' pour référence explicite dans migrations
    # Comportement : Tentative d'insertion en doublon → IntegrityError
    # Gestion : Côté application, utiliser INSERT ... ON CONFLICT DO NOTHING
    #          ou vérifier existence avant insertion
    # Exemple erreur : sqlalchemy.exc.IntegrityError: duplicate key value violates
    #                  unique constraint "uq_user_lot_favorite"
    __table_args__ = (
        UniqueConstraint('user_id', 'lot_id', name='uq_user_lot_favorite'),
    )

    def __repr__(self):
        """
        Représentation textuelle de l'objet Favorite pour le debugging

        Returns:
            str : Format "<Favorite user={user_id} lot={lot_id}>"

        Utilisation : Affichage dans les logs, debugging, shell interactif
        Exemple : <Favorite user=5 lot=42>
        """
        return f"<Favorite user={self.user_id} lot={self.lot_id}>"
