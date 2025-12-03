"""
Modèle Notification - Gestion des notifications utilisateur

Ce module définit le modèle Notification représentant les notifications in-app envoyées
aux utilisateurs. Les notifications peuvent provenir de diverses sources : alertes de prix,
nouveaux lots, actions système, messages administratifs, etc.

Types de notifications supportés :
    - info : Information générale (couleur bleue)
    - warning : Avertissement (couleur orange)
    - success : Action réussie (couleur verte)
    - error : Erreur (couleur rouge)

Fonctionnalités :
    - Notifications en temps réel dans l'interface utilisateur
    - Suivi de l'état de lecture (non lu / lu)
    - Lien optionnel vers la ressource concernée
    - Tri chronologique avec horodatage

Dépendances SQLAlchemy :
    - Column : Définit une colonne de table
    - Integer, String, Boolean, DateTime, Text : Types de données
    - ForeignKey : Clé étrangère vers User
    - relationship : Définit les relations avec d'autres modèles

Impact sur la BDD :
    - Table créée : 'notifications'
    - Relations :
        * Many-to-One avec User (plusieurs notifications → un utilisateur)
    - Cascade delete : Suppression de l'utilisateur → suppression de toutes ses notifications
    - Index : (is_read) et (created_at) pour optimiser les requêtes de listing
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.db.base import Base


class Notification(Base):
    """
    Modèle Notification - Représente une notification in-app pour un utilisateur

    Les notifications sont créées automatiquement par le système lors de divers événements :
    - Déclenchement d'une alerte (baisse de prix, nouveau lot correspondant)
    - Actions administratives (modération, suspension de compte)
    - Messages système (maintenance, nouvelles fonctionnalités)
    - Événements liés aux lots suivis (vente terminée, lot retiré)

    Cycle de vie d'une notification :
    1. Création : is_read=False, created_at=now()
    2. Affichage : Apparaît dans le badge de notifications de l'utilisateur
    3. Lecture : is_read=True, read_at=now()
    4. Nettoyage : Suppression des vieilles notifications (optionnel)

    Bonnes pratiques :
    - Limiter le nombre de notifications non lues pour éviter le spam
    - Regrouper les notifications similaires (ex: "3 nouveaux lots")
    - Supprimer automatiquement les notifications de plus de 30 jours

    Impact BDD :
    ⚠️ ATTENTION : La suppression de l'utilisateur entraîne la suppression
    automatique de TOUTES ses notifications (ON DELETE CASCADE).
    """
    __tablename__ = "notifications"  # Nom de la table dans PostgreSQL

    # ========== Colonnes d'Identité ==========

    # id : Clé primaire auto-incrémentée, identifiant unique de la notification
    # Impact : Utilisé pour marquer une notification comme lue
    # Note : Référencé dans les API de marquage lu/non-lu
    id = Column(Integer, primary_key=True, index=True)

    # user_id : Référence vers l'utilisateur destinataire de la notification
    # Impact : FK vers users.id avec CASCADE DELETE
    # Nullable : False car une notification doit appartenir à un utilisateur
    # Cascade : Suppression de l'utilisateur → suppression de toutes ses notifications
    # Index : Créé automatiquement par la FK pour optimiser les requêtes
    # ⚠️ CRITIQUE : ON DELETE CASCADE côté BDD pour cohérence des données
    # Utilisation : Requêtes "notifications de l'utilisateur X"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # ========== Colonnes de Contenu ==========

    # title : Titre court de la notification (affiché en gras)
    # Impact : Affiché dans la liste des notifications et le badge
    # Nullable : False car une notification doit avoir un titre
    # Format : Court et explicite (max 100 caractères recommandé)
    # Exemples :
    #   - "Baisse de prix !"
    #   - "Nouveau lot correspondant à votre alerte"
    #   - "Maintenance programmée"
    # Utilisation : Titre principal dans l'UI, push notifications
    title = Column(String, nullable=False)

    # message : Message détaillé de la notification (corps du texte)
    # Impact : Type Text pour supporter des messages longs (>255 chars)
    # Nullable : False car une notification doit avoir un message
    # Format : Markdown optionnel pour formatage (gras, liens, listes)
    # Exemples :
    #   - "Le lot #42 'Renault Clio' est passé de 5000€ à 4200€"
    #   - "Un nouveau lot 'BMW' est disponible à Paris"
    #   - "Une maintenance est prévue le 15/12 de 2h à 4h"
    # Utilisation : Détails de la notification, corps de l'email
    message = Column(Text, nullable=False)

    # notification_type : Type/catégorie de la notification pour stylisation UI
    # Impact : Détermine la couleur et l'icône dans l'interface
    # Valeurs : "info", "warning", "success", "error", NULL
    # Nullable : True car le type est optionnel (défaut = "info")
    # Mapping UI :
    #   - info : Bleu, icône ℹ️ (information générale)
    #   - warning : Orange, icône ⚠️ (avertissement)
    #   - success : Vert, icône ✓ (action réussie)
    #   - error : Rouge, icône ✗ (erreur)
    # Utilisation : Stylisation côté frontend, filtrage par type
    notification_type = Column(String, nullable=True)

    # ========== Colonnes de Navigation ==========

    # link : URL optionnelle vers la ressource liée à la notification
    # Impact : Rend la notification cliquable pour navigation directe
    # Nullable : True car certaines notifications n'ont pas de lien
    # Format : String pour URL relative ou absolue
    # Exemples :
    #   - "/lots/42" (lien vers page de détail du lot)
    #   - "/profile/alerts" (lien vers gestion des alertes)
    #   - "https://example.com/news" (lien externe)
    # Utilisation : Navigation au clic sur la notification
    link = Column(String, nullable=True)

    # ========== Colonnes d'État ==========

    # is_read : Flag indiquant si la notification a été lue par l'utilisateur
    # Impact : Affichage visuel (gras si non lu), badge de compteur
    # Default : False = notification non lue à la création
    # Index : Optimise les requêtes "notifications non lues"
    # Utilisation :
    #   - Badge "5 notifications non lues"
    #   - Style visuel différent pour notifications non lues
    #   - Filtrage "afficher uniquement non lues"
    is_read = Column(Boolean, default=False, index=True)

    # ========== Colonnes d'Audit ==========

    # created_at : Date de création de la notification (timestamp UTC)
    # Impact : Index pour tri chronologique "notifications récentes d'abord"
    # Immutable : Ne change jamais après création
    # Default : Timestamp de l'insertion en BDD
    # Utilisation :
    #   - Tri chronologique inversé dans la liste
    #   - Affichage "il y a 5 minutes"
    #   - Nettoyage automatique des vieilles notifications (>30 jours)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # read_at : Date de première lecture de la notification (timestamp UTC)
    # Impact : Permet de tracker le délai de lecture des notifications
    # Nullable : True car NULL si jamais lue (cohérent avec is_read=False)
    # Mise à jour : Mise à jour manuelle lors du marquage comme lu
    # Utilisation :
    #   - Statistiques : délai moyen de lecture des notifications
    #   - Affichage "lue il y a 2 heures"
    #   - Analytique : taux d'engagement des notifications
    read_at = Column(DateTime, nullable=True)

    # ========== Relations SQLAlchemy ==========

    # user : Utilisateur destinataire de la notification (relation Many-to-One)
    # Type : Many-to-One (plusieurs notifications → un user)
    # back_populates : Relation bidirectionnelle avec User.notifications
    # Impact BDD : FK user_id → users.id ON DELETE CASCADE
    # Cascade : Géré au niveau BDD (ondelete="CASCADE" dans ForeignKey)
    # Suppression user → suppression automatique de toutes ses notifications
    # Utilisation : Accès facile aux notifications depuis l'objet User
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        """
        Représentation textuelle de l'objet Notification pour le debugging

        Returns:
            str : Format "<Notification {title} for user={user_id}>"

        Utilisation : Affichage dans les logs, debugging, shell interactif
        Exemple : <Notification Baisse de prix ! for user=5>
        """
        return f"<Notification {self.title} for user={self.user_id}>"
