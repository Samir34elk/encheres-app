"""
Modèle User - Gestion des utilisateurs de la plateforme

Ce module définit le modèle central User qui représente un utilisateur de l'application.
Il gère l'authentification (locale ou OAuth), les rôles, les préférences et les relations
avec les autres entités (favoris, alertes, notifications, commentaires).

Dépendances SQLAlchemy :
    - Column : Définit une colonne de table
    - Integer, String, Boolean, DateTime, Enum : Types de données
    - relationship : Définit les relations entre modèles

Impact sur la BDD :
    - Table créée : 'users'
    - Relations : One-to-Many avec Favorite, Alert, Notification, Comment
    - Cascade : Suppression d'un user supprime toutes ses données liées
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from shared.db.base import Base


class UserRole(str, enum.Enum):
    """
    Énumération des rôles utilisateur

    Définit les trois niveaux d'autorisation dans l'application :
    - GUEST : Visiteur non authentifié (lecture seule limitée)
    - USER : Utilisateur standard (lecture + actions personnelles)
    - ADMIN : Administrateur (toutes les permissions)

    Impact : Utilisé pour le contrôle d'accès dans tous les services
    """
    GUEST = "guest"    # Visiteur anonyme, accès limité en lecture
    USER = "user"      # Utilisateur authentifié standard
    ADMIN = "admin"    # Administrateur avec tous les droits


class AuthProvider(str, enum.Enum):
    """
    Énumération des méthodes d'authentification

    Permet de tracker comment l'utilisateur s'est authentifié :
    - LOCAL : Email/mot de passe classique (hashed_password requis)
    - GOOGLE : OAuth2 via Google (hashed_password null)
    - GITHUB : OAuth2 via GitHub (hashed_password null)

    Impact : Détermine si hashed_password doit être vérifié lors du login
    """
    LOCAL = "local"    # Authentification par email/mot de passe
    GOOGLE = "google"  # Authentification OAuth2 Google
    GITHUB = "github"  # Authentification OAuth2 GitHub


class User(Base):
    """
    Modèle User - Représente un utilisateur de la plateforme

    Centralise toutes les informations d'un utilisateur :
    - Identité : email, username, full_name
    - Authentification : hashed_password, auth_provider
    - Autorisation : role, is_active, is_admin
    - Préférences : language, theme
    - Audit : created_at, updated_at, last_login

    Relations :
    - favorites : Lots favoris de l'utilisateur (cascade delete)
    - alerts : Alertes configurées (cascade delete)
    - notifications : Notifications reçues (cascade delete)
    - comments : Commentaires postés (cascade delete)

    Impact BDD :
    ⚠️ ATTENTION : La suppression d'un User entraîne la suppression en cascade
    de TOUTES ses données liées (favoris, alertes, notifications, commentaires)
    """
    __tablename__ = "users"  # Nom de la table dans PostgreSQL

    # ========== Colonnes d'Identité ==========

    # id : Clé primaire auto-incrémentée, identifiant unique de l'utilisateur
    # Impact : Référencé par les FK de favorites, alerts, notifications, comments
    id = Column(Integer, primary_key=True, index=True)

    # email : Adresse email unique, utilisée pour le login
    # Impact : Index créé pour optimiser les requêtes de login (WHERE email = ?)
    # ⚠️ RGPD : Donnée personnelle sensible, chiffrée en transit (SSL)
    email = Column(String, unique=True, index=True, nullable=False)

    # username : Nom d'utilisateur public unique, affiché dans l'interface
    # Impact : Index pour recherche rapide, contrainte unique pour éviter doublons
    username = Column(String, unique=True, index=True, nullable=False)

    # hashed_password : Mot de passe haché (bcrypt), NULL si OAuth
    # Impact : Nullable=True permet les utilisateurs OAuth sans mot de passe local
    # 🔐 Sécurité : Toujours haché avec bcrypt + salt, jamais stocké en clair
    hashed_password = Column(String, nullable=True)

    # full_name : Nom complet optionnel de l'utilisateur
    # Impact : Utilisé pour l'affichage et les emails de notification
    full_name = Column(String, nullable=True)

    # ========== Colonnes d'Autorisation ==========

    # is_active : Flag pour désactiver un compte sans le supprimer (soft delete)
    # Impact : Vérifié à chaque authentification, bloque l'accès si False
    # Utilisation : Suspension temporaire, modération, suppression RGPD partielle
    is_active = Column(Boolean, default=True)

    # is_admin : Flag booléen rapide pour vérifier les droits admin
    # Impact : Utilisé pour les vérifications rapides, redondant avec role=ADMIN
    # Note : Maintenu pour compatibilité, mais role est la source de vérité
    is_admin = Column(Boolean, default=False)

    # role : Rôle principal de l'utilisateur (GUEST, USER, ADMIN)
    # Impact : Détermine les permissions dans tous les services
    # Migration : Si changé, mettre à jour toute la logique d'autorisation
    role = Column(Enum(UserRole), default=UserRole.USER)

    # auth_provider : Méthode d'authentification utilisée (LOCAL, GOOGLE, GITHUB)
    # Impact : Détermine le flow de login (password vs OAuth)
    # Note : Si LOCAL, hashed_password doit être non-NULL
    auth_provider = Column(Enum(AuthProvider), default=AuthProvider.LOCAL)

    # ========== Colonnes de Préférences ==========

    # language : Langue de l'interface utilisateur (fr ou en)
    # Impact : Utilisé pour l'i18n du frontend et les emails de notification
    # Valeurs acceptées : "fr" (français), "en" (anglais)
    language = Column(String, default="fr")

    # theme : Thème de l'interface (light ou dark)
    # Impact : Préférence visuelle, stockée pour persistance entre sessions
    # Valeurs acceptées : "light", "dark"
    theme = Column(String, default="light")

    # ========== Colonnes d'Audit et Métadonnées ==========

    # created_at : Date de création du compte (timestamp UTC)
    # Impact : Immutable après création, utilisé pour les statistiques
    # ⚠️ Toujours en UTC pour éviter les problèmes de timezone
    created_at = Column(DateTime, default=datetime.utcnow)

    # updated_at : Date de dernière modification du compte (timestamp UTC)
    # Impact : Auto-update à chaque modification via onupdate
    # Utilisation : Audit, détection de comptes inactifs
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # last_login : Date de dernière connexion (timestamp UTC)
    # Impact : Mis à jour manuellement lors de chaque login réussi
    # Utilisation : Détection de comptes inactifs, statistiques d'engagement
    last_login = Column(DateTime, nullable=True)

    # ========== Relations SQLAlchemy ==========

    # favorites : Liste des lots favoris de l'utilisateur
    # Type : One-to-Many (un user a plusieurs favoris)
    # Cascade : "all, delete-orphan" = suppression du user → suppression favoris
    # back_populates : Crée la relation bidirectionnelle avec Favorite.user
    # Impact BDD : FK dans table favorites (user_id → users.id ON DELETE CASCADE)
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

    # alerts : Liste des alertes configurées par l'utilisateur
    # Type : One-to-Many (un user a plusieurs alertes)
    # Cascade : Suppression du user → suppression de toutes ses alertes
    # Impact : Arrête toutes les notifications d'alerte pour ce user
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

    # notifications : Liste des notifications reçues par l'utilisateur
    # Type : One-to-Many (un user a plusieurs notifications)
    # Cascade : Suppression du user → suppression de toutes ses notifications
    # Impact : Nettoyage complet de l'historique de notifications
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    # comments : Liste des commentaires postés par l'utilisateur
    # Type : One-to-Many (un user a plusieurs commentaires)
    # Cascade : Suppression du user → suppression de tous ses commentaires
    # Impact : Les lots perdent les commentaires de ce user
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        """
        Représentation textuelle de l'objet User pour le debugging

        Returns:
            str : Format "<User email@example.com>"

        Utilisation : Affichage dans les logs, debugging, shell interactif
        """
        return f"<User {self.email}>"
