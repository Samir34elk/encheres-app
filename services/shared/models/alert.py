"""
Modèle Alert - Gestion des alertes utilisateur

Ce module définit le modèle Alert permettant aux utilisateurs de configurer des alertes
automatiques sur les lots aux enchères. Les alertes peuvent être basées sur le prix,
les mots-clés, la localisation, ou l'ajout de nouveaux lots.

Types d'alertes supportés :
    - PRICE_DROP : Alerte lors d'une baisse de prix
    - PRICE_BELOW : Alerte si le prix passe sous un seuil
    - ANY_CHANGE : Alerte à tout changement sur le lot
    - PRICE_CHANGE : Alias de ANY_CHANGE (rétrocompatibilité)
    - NEW_LOT : Alerte lors de l'ajout de nouveaux lots
    - KEYWORD : Alerte si un mot-clé apparaît dans un lot

Dépendances SQLAlchemy :
    - Column : Définit une colonne de table
    - Integer, String, Boolean, DateTime, Enum : Types de données
    - ForeignKey : Clé étrangère vers User et Lot
    - relationship : Définit les relations avec d'autres modèles

Impact sur la BDD :
    - Table créée : 'alerts'
    - Relations :
        * Many-to-One avec User (plusieurs alertes → un utilisateur)
        * Many-to-One avec Lot (plusieurs alertes → un lot) - optionnel
    - Cascade delete : Suppression de l'utilisateur OU du lot → suppression de l'alerte
    - Contraintes : user_id obligatoire, lot_id optionnel (alertes génériques)
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from shared.db.base import Base


class AlertType(str, enum.Enum):
    """
    Énumération des types d'alertes disponibles

    Définit les différents types de déclencheurs d'alerte :
    - PRICE_DROP : Alerte lors d'une baisse de prix (requiert lot_id)
    - PRICE_BELOW : Alerte si prix < target_price (requiert target_price)
    - ANY_CHANGE : Alerte à tout changement (prix, statut, description)
    - PRICE_CHANGE : Alias de ANY_CHANGE (conservé pour compatibilité)
    - NEW_LOT : Alerte lors de nouveaux lots (utilise keyword, location)
    - KEYWORD : Alerte si keyword apparaît dans titre/description

    Impact : Utilisé par le service de notification pour filtrer les événements
    """
    PRICE_DROP = "price_drop"      # Alerte sur baisse de prix d'un lot spécifique
    PRICE_BELOW = "price_below"    # Alerte si prix passe sous un seuil
    ANY_CHANGE = "any_change"      # Alerte à tout changement sur un lot
    PRICE_CHANGE = "price_change"  # Alias de ANY_CHANGE (rétrocompatibilité)
    NEW_LOT = "new_lot"            # Alerte lors de l'ajout de nouveaux lots
    KEYWORD = "keyword"            # Alerte si un mot-clé est détecté


class Alert(Base):
    """
    Modèle Alert - Représente une alerte configurée par un utilisateur

    Permet aux utilisateurs de recevoir des notifications automatiques basées sur :
    - Changements de prix d'un lot spécifique
    - Apparition de lots correspondant à des critères (mot-clé, localisation)
    - Seuils de prix personnalisés

    Fonctionnement :
    1. Utilisateur crée une alerte avec des conditions (type, keyword, target_price, etc.)
    2. Service de scraping détecte des changements sur les lots
    3. Système vérifie si les conditions de l'alerte sont remplies
    4. Si oui : notification envoyée (email si email_enabled=True) et last_triggered mis à jour

    Structure des alertes :
    - Alertes spécifiques : lot_id renseigné (ex: surveiller le lot #42)
    - Alertes génériques : lot_id NULL (ex: surveiller tous les nouveaux lots avec "Renault")

    Impact BDD :
    ⚠️ ATTENTION : La suppression de l'utilisateur OU du lot entraîne la suppression
    automatique de l'alerte (ON DELETE CASCADE sur les deux FK).
    """
    __tablename__ = "alerts"  # Nom de la table dans PostgreSQL

    # ========== Colonnes d'Identité ==========

    # id : Clé primaire auto-incrémentée, identifiant unique de l'alerte
    # Impact : Utilisé pour activer/désactiver/supprimer une alerte
    # Note : Référencé dans les notifications envoyées
    id = Column(Integer, primary_key=True, index=True)

    # user_id : Référence vers l'utilisateur propriétaire de l'alerte
    # Impact : FK vers users.id avec CASCADE DELETE
    # Nullable : False car une alerte doit appartenir à un utilisateur
    # Cascade : Suppression de l'utilisateur → suppression de toutes ses alertes
    # ⚠️ CRITIQUE : ON DELETE CASCADE côté BDD pour cohérence des données
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # lot_id : Référence vers le lot surveillé (optionnel pour alertes génériques)
    # Impact : FK vers lots.id avec CASCADE DELETE
    # Nullable : True pour permettre les alertes génériques (ex: NEW_LOT, KEYWORD)
    # Index : Optimise la recherche "toutes les alertes pour le lot X"
    # Cascade : Suppression du lot → suppression de toutes ses alertes
    # Utilisation :
    #   - NULL : alerte générique (ex: "nouveaux lots avec 'BMW'")
    #   - Non-NULL : alerte spécifique (ex: "baisse de prix du lot #42")
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=True, index=True)

    # ========== Colonnes de Configuration ==========

    # alert_type : Type d'alerte (PRICE_DROP, PRICE_BELOW, etc.)
    # Impact : Détermine la logique de déclenchement de l'alerte
    # Nullable : False car chaque alerte doit avoir un type
    # Enum : Valeurs limitées à celles définies dans AlertType
    # Validation : Côté application, vérifier cohérence avec autres colonnes
    #   - PRICE_DROP/PRICE_BELOW : requiert target_price
    #   - KEYWORD : requiert keyword
    #   - NEW_LOT : peut utiliser keyword et/ou location
    alert_type = Column(Enum(AlertType), nullable=False)

    # is_active : Flag pour activer/désactiver temporairement l'alerte
    # Impact : Les alertes désactivées (False) ne déclenchent pas de notifications
    # Default : True = alerte active dès création
    # Utilisation : Permet de mettre en pause une alerte sans la supprimer
    # Cas d'usage : Utilisateur en vacances, trop de notifications, etc.
    is_active = Column(Boolean, default=True)

    # ========== Colonnes de Conditions ==========

    # keyword : Mot-clé à rechercher dans titre/description des lots
    # Impact : Utilisé pour filtrer les lots lors du déclenchement
    # Nullable : True, utilisé uniquement pour NEW_LOT et KEYWORD
    # Format : Texte libre, recherche case-insensitive recommandée
    # Exemples : "renault clio", "paris", "véhicule utilitaire"
    # Utilisation : Alertes génériques "nouveaux lots contenant X"
    keyword = Column(String, nullable=True)

    # target_price : Prix seuil pour les alertes de prix (en centimes d'euros)
    # Impact : Condition de déclenchement pour PRICE_BELOW
    # Format : Integer (centimes), ex: 50000 = 500.00€
    # Nullable : True, utilisé uniquement pour PRICE_BELOW
    # Logique : Alerte déclenchée si lot.price < target_price
    # Exemple : target_price=100000 → alerte si prix passe sous 1000€
    target_price = Column(Integer, nullable=True)

    # location : Localisation géographique pour filtrer les alertes
    # Impact : Filtre les lots par depot_location
    # Nullable : True, utilisé pour les alertes génériques géo-localisées
    # Format : Texte libre, doit correspondre à lot.depot_location
    # Exemples : "Paris", "Île-de-France", "75"
    # Utilisation : "Nouveaux lots à Paris contenant 'BMW'"
    location = Column(String, nullable=True)

    # ========== Colonnes de Notification ==========

    # email_enabled : Flag pour activer/désactiver les notifications email
    # Impact : Si False, seules les notifications in-app sont créées
    # Default : True = emails activés par défaut
    # Utilisation : Utilisateur peut préférer uniquement les notifications web
    # Performance : Désactiver pour réduire la charge d'envoi d'emails
    email_enabled = Column(Boolean, default=True)

    # ========== Colonnes d'Audit ==========

    # created_at : Date de création de l'alerte (timestamp UTC)
    # Impact : Immutable après création, utilisé pour audit
    # Default : Timestamp de l'insertion en BDD
    # Utilisation : Statistiques, tri des alertes par ancienneté
    created_at = Column(DateTime, default=datetime.utcnow)

    # last_triggered : Date du dernier déclenchement de l'alerte (timestamp UTC)
    # Impact : Permet d'éviter de spammer l'utilisateur
    # Nullable : True car NULL si jamais déclenchée
    # Mise à jour : Mise à jour manuelle lors de chaque déclenchement
    # Utilisation :
    #   - Eviter les déclenchements multiples (ex: ne pas alerter 2x pour le même changement)
    #   - Afficher "dernière alerte il y a 2h" dans l'interface
    #   - Désactiver automatiquement les alertes trop anciennes
    last_triggered = Column(DateTime, nullable=True)

    # ========== Relations SQLAlchemy ==========

    # user : Utilisateur propriétaire de l'alerte (relation Many-to-One)
    # Type : Many-to-One (plusieurs alertes → un user)
    # back_populates : Relation bidirectionnelle avec User.alerts
    # Impact BDD : FK user_id → users.id ON DELETE CASCADE
    # Cascade : Géré au niveau BDD (ondelete="CASCADE" dans ForeignKey)
    # Suppression user → suppression automatique de toutes ses alertes
    user = relationship("User", back_populates="alerts")

    # lot : Lot surveillé par l'alerte (relation Many-to-One optionnelle)
    # Type : Many-to-One (plusieurs alertes → un lot)
    # back_populates : Relation bidirectionnelle avec Lot.alerts
    # Impact BDD : FK lot_id → lots.id ON DELETE CASCADE
    # Nullable : True pour permettre les alertes génériques
    # Cascade : Suppression du lot → suppression de toutes ses alertes
    # Exemple : Si lot #42 supprimé, toutes les alertes PRICE_DROP sur ce lot disparaissent
    lot = relationship("Lot", back_populates="alerts")

    def __repr__(self):
        """
        Représentation textuelle de l'objet Alert pour le debugging

        Returns:
            str : Format "<Alert {alert_type} for user={user_id} lot={lot_id}>"

        Utilisation : Affichage dans les logs, debugging, shell interactif
        Exemple : <Alert PRICE_DROP for user=5 lot=42>
        """
        return f"<Alert {self.alert_type} for user={self.user_id} lot={self.lot_id}>"
