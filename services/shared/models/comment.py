"""
Modèle Comment - Gestion des commentaires sur les lots

Ce module définit le modèle Comment représentant les commentaires/notes publics
postés par les utilisateurs sur les lots aux enchères. Permet l'échange d'informations
entre utilisateurs, le partage d'avis, et l'enrichissement collaboratif des fiches lots.

Fonctionnalités :
    - Commentaires publics visibles par tous les utilisateurs
    - Édition de commentaires existants (updated_at tracké)
    - Attribution automatique à l'auteur (user_id)
    - Tri chronologique pour fil de discussion

Cas d'usage :
    - Utilisateur A poste : "Attention, véhicule accidenté"
    - Utilisateur B demande : "Quelqu'un a déjà acheté dans ce dépôt ?"
    - Utilisateur C partage : "J'ai visité le lot, l'état est correct"
    - Modération : Suppression de commentaires inappropriés

Dépendances SQLAlchemy :
    - Column : Définit une colonne de table
    - Integer, DateTime, Text : Types de données
    - ForeignKey : Clé étrangère vers User et Lot
    - relationship : Définit les relations avec d'autres modèles

Impact sur la BDD :
    - Table créée : 'comments'
    - Relations :
        * Many-to-One avec User (plusieurs commentaires → un utilisateur)
        * Many-to-One avec Lot (plusieurs commentaires → un lot)
    - Cascade delete : Suppression de l'utilisateur OU du lot → suppression du commentaire
    - Index : (created_at) pour tri chronologique des commentaires
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.db.base import Base


class Comment(Base):
    """
    Modèle Comment - Représente un commentaire posté par un utilisateur sur un lot

    Les commentaires permettent aux utilisateurs d'échanger des informations,
    des avis et des conseils sur les lots aux enchères. Ils sont publics et
    visibles par tous les utilisateurs pour enrichir l'information collective.

    Différence avec Favorite.notes :
    - Comment : Public, visible par tous, discussion communautaire
    - Favorite.notes : Privé, visible uniquement par l'auteur, aide-mémoire personnel

    Workflow typique :
    1. Utilisateur consulte la fiche d'un lot
    2. Lit les commentaires existants d'autres utilisateurs
    3. Poste un nouveau commentaire (création)
    4. Peut éditer son commentaire (updated_at mis à jour)
    5. Admin peut supprimer un commentaire inapproprié

    Modération :
    - Prévoir un système de signalement pour commentaires abusifs
    - Possibilité de désactiver les commentaires sur certains lots
    - Filtrage anti-spam recommandé (rate limiting, captcha)

    Impact BDD :
    ⚠️ ATTENTION : La suppression de l'utilisateur OU du lot entraîne la suppression
    automatique de TOUS les commentaires associés (ON DELETE CASCADE).

    ⚠️ ATTENTION : updated_at est mis à jour automatiquement à chaque modification
    pour tracer l'historique des éditions. Considérer un système de versions
    pour garder l'historique complet des modifications.
    """
    __tablename__ = "comments"  # Nom de la table dans PostgreSQL

    # ========== Colonnes d'Identité ==========

    # id : Clé primaire auto-incrémentée, identifiant unique du commentaire
    # Impact : Utilisé pour éditer/supprimer un commentaire spécifique
    # Note : Référencé dans les URLs (ex: /lots/42/comments/123)
    id = Column(Integer, primary_key=True, index=True)

    # user_id : Référence vers l'utilisateur auteur du commentaire
    # Impact : FK vers users.id avec CASCADE DELETE
    # Nullable : False car un commentaire doit avoir un auteur
    # Cascade : Suppression de l'utilisateur → suppression de tous ses commentaires
    # Index : Créé automatiquement par la FK pour optimiser les requêtes
    # ⚠️ CRITIQUE : ON DELETE CASCADE côté BDD pour cohérence des données
    # Utilisation : Affichage "Commentaire de @username", filtrage par auteur
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # lot_id : Référence vers le lot sur lequel le commentaire est posté
    # Impact : FK vers lots.id avec CASCADE DELETE
    # Nullable : False car un commentaire doit être lié à un lot
    # Cascade : Suppression du lot → suppression de tous ses commentaires
    # Index : Créé automatiquement par la FK pour optimiser les requêtes
    # ⚠️ CRITIQUE : ON DELETE CASCADE côté BDD pour cohérence des données
    # Utilisation : Requête "tous les commentaires du lot X"
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=False)

    # ========== Colonnes de Contenu ==========

    # content : Contenu textuel du commentaire
    # Impact : Type Text pour supporter de longs commentaires (>255 chars)
    # Nullable : False car un commentaire doit avoir du contenu
    # Format : Texte libre, support Markdown recommandé pour formatage
    # Validation recommandée :
    #   - Longueur min : 10 caractères (éviter spam "ok", "bien")
    #   - Longueur max : 2000 caractères (lisibilité)
    #   - Filtrage : mots interdits, liens suspects
    # Exemples :
    #   - "Attention, véhicule accidenté selon le rapport Carfax"
    #   - "J'ai visité le dépôt, l'état est bien meilleur que sur les photos"
    #   - "Prix trop élevé par rapport au marché actuel"
    # Utilisation : Affichage dans le fil de discussion sous le lot
    content = Column(Text, nullable=False)

    # ========== Colonnes d'Audit ==========

    # created_at : Date de création du commentaire (timestamp UTC)
    # Impact : Index pour tri chronologique "plus récents d'abord"
    # Immutable : Ne change jamais après création
    # Default : Timestamp de l'insertion en BDD
    # Utilisation :
    #   - Tri chronologique dans le fil de discussion
    #   - Affichage "posté il y a 2 heures"
    #   - Statistiques : nombre de commentaires par jour
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # updated_at : Date de dernière modification du commentaire (timestamp UTC)
    # Impact : Auto-update à chaque UPDATE via onupdate
    # Default : Égal à created_at lors de la création
    # Trigger : Mis à jour automatiquement lors de toute modification du content
    # Utilisation :
    #   - Badge "édité" si updated_at > created_at + 1 minute
    #   - Affichage "modifié il y a 30 minutes"
    #   - Détection de modifications suspectes (édition après signalement)
    # Limitation : Ne garde pas l'historique des versions, seulement la dernière
    #              modification. Pour historique complet, utiliser une table Comment_History
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ========== Relations SQLAlchemy ==========

    # user : Utilisateur auteur du commentaire (relation Many-to-One)
    # Type : Many-to-One (plusieurs commentaires → un user)
    # back_populates : Relation bidirectionnelle avec User.comments
    # Impact BDD : FK user_id → users.id ON DELETE CASCADE
    # Cascade : Géré au niveau BDD (ondelete="CASCADE" dans ForeignKey)
    # Suppression user → suppression automatique de tous ses commentaires
    # Utilisation : Afficher username, avatar, badge "auteur" dans l'UI
    user = relationship("User", back_populates="comments")

    # lot : Lot sur lequel le commentaire est posté (relation Many-to-One)
    # Type : Many-to-One (plusieurs commentaires → un lot)
    # back_populates : Relation bidirectionnelle avec Lot.comments
    # Impact BDD : FK lot_id → lots.id ON DELETE CASCADE
    # Cascade : Suppression du lot → suppression de tous ses commentaires
    # Utilisation : Navigation "voir le lot commenté", compteur "X commentaires"
    lot = relationship("Lot", back_populates="comments")

    def __repr__(self):
        """
        Représentation textuelle de l'objet Comment pour le debugging

        Returns:
            str : Format "<Comment user={user_id} lot={lot_id}>"

        Utilisation : Affichage dans les logs, debugging, shell interactif
        Exemple : <Comment user=5 lot=42>
        """
        return f"<Comment user={self.user_id} lot={self.lot_id}>"
