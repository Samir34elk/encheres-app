"""
Modèle PriceHistory - Historique des changements de prix des lots

Ce module définit le modèle PriceHistory qui enregistre l'évolution des prix des lots
au fil du temps. Permet de tracker les variations de prix, détecter les baisses,
et afficher des graphiques d'évolution.

Fonctionnalités :
    - Enregistrement automatique à chaque changement de prix
    - Tracking du statut du lot au moment du changement
    - Horodatage précis pour traçabilité temporelle
    - Détection de baisses de prix pour alertes

Cas d'usage :
    - Graphique d'évolution du prix d'un lot dans le temps
    - Détection de baisse de prix pour déclencher des alertes
    - Analyse de tendances de prix par type de lot
    - Statistiques : prix moyen, min, max d'un lot

Dépendances SQLAlchemy :
    - Column : Définit une colonne de table
    - Integer, String, DateTime : Types de données
    - ForeignKey : Clé étrangère vers Lot
    - relationship : Définit les relations avec d'autres modèles

Impact sur la BDD :
    - Table créée : 'price_history'
    - Relations :
        * Many-to-One avec Lot (plusieurs entrées d'historique → un lot)
    - Cascade delete : Suppression du lot → suppression de tout son historique
    - Index : (lot_id) et (recorded_at) pour requêtes de recherche chronologique
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.db.base import Base


class PriceHistory(Base):
    """
    Modèle PriceHistory - Représente une entrée d'historique de prix d'un lot

    Chaque fois que le prix d'un lot change, une nouvelle entrée est créée dans
    cette table pour garder une trace de l'évolution. Cela permet de :
    - Afficher un graphique d'évolution du prix
    - Calculer la variation de prix (hausse/baisse en %)
    - Détecter les baisses pour déclencher des alertes utilisateur
    - Analyser les tendances de prix du marché

    Workflow typique :
    1. Scraper récupère nouveau prix pour un lot
    2. Comparaison : nouveau prix != ancien prix ?
    3. Si changement : création d'une entrée PriceHistory
    4. Mise à jour de lot.price avec la nouvelle valeur
    5. Vérification des alertes PRICE_DROP configurées sur ce lot

    Optimisations :
    - Index sur lot_id pour requête "historique du lot X"
    - Index sur recorded_at pour tri chronologique
    - Limite : Garder uniquement les N dernières entrées (ex: 100) par lot
              pour éviter une croissance infinie de la table

    Impact BDD :
    ⚠️ ATTENTION : La suppression d'un Lot entraîne la suppression automatique
    de TOUT son historique de prix (ON DELETE CASCADE).

    ⚠️ CROISSANCE : Cette table peut grossir rapidement (une ligne par changement).
    Prévoir un nettoyage périodique des vieilles entrées (>90 jours).
    """
    __tablename__ = "price_history"  # Nom de la table dans PostgreSQL

    # ========== Colonnes d'Identité ==========

    # id : Clé primaire auto-incrémentée, identifiant unique de l'entrée
    # Impact : Utilisé pour identifier une entrée spécifique d'historique
    # Note : Rarement utilisé directement, surtout pour la cohérence du schéma
    id = Column(Integer, primary_key=True, index=True)

    # lot_id : Référence vers le lot dont on enregistre le prix
    # Impact : FK vers lots.id avec CASCADE DELETE
    # Nullable : False car une entrée d'historique doit appartenir à un lot
    # Index : Optimise la requête "historique complet du lot X"
    # Cascade : Suppression du lot → suppression de tout son historique
    # ⚠️ CRITIQUE : ON DELETE CASCADE côté BDD pour cohérence des données
    # Utilisation : Groupement "GROUP BY lot_id" pour statistiques
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=False, index=True)

    # ========== Colonnes de Données ==========

    # price : Prix du lot au moment de l'enregistrement (en euros, entier)
    # Impact : Valeur historique pour calcul de variations
    # Format : Integer (euros)
    # Exemple : 1500 = 1500€, 125 = 125€
    # Nullable : False car on doit toujours avoir un prix
    # Utilisation :
    #   - Graphique d'évolution : tracé de la courbe de prix
    #   - Calcul variation : (nouveau_prix - ancien_prix) / ancien_prix * 100
    #   - Détection baisse : ancien_prix > nouveau_prix
    price = Column(Integer, nullable=False)

    # status : Statut du lot au moment de l'enregistrement du prix
    # Impact : Permet de corréler changement de prix avec changement de statut
    # Valeurs : "available", "sold", "withdrawn", NULL
    # Nullable : True car le statut peut être inconnu
    # Utilisation :
    #   - Déterminer si le prix a changé suite à une vente
    #   - Filtrer "historique uniquement quand disponible"
    #   - Analyse : corrélation entre statut et évolution de prix
    # Exemple : Prix baisse → statut reste "available" = vraie baisse
    #           Prix baisse + statut = "sold" = prix de vente final
    status = Column(String, nullable=True)

    # ========== Colonnes d'Audit ==========

    # recorded_at : Date d'enregistrement de cette entrée d'historique (timestamp UTC)
    # Impact : Index pour tri chronologique et requêtes temporelles
    # Immutable : Ne change jamais après création
    # Default : Timestamp de l'insertion en BDD
    # Utilisation :
    #   - Axe X des graphiques d'évolution de prix
    #   - Requêtes "variation de prix sur les 7 derniers jours"
    #   - Nettoyage "DELETE WHERE recorded_at < now() - interval '90 days'"
    # ⚠️ Toujours en UTC pour cohérence internationale
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    # ========== Relations SQLAlchemy ==========

    # lot : Lot auquel appartient cette entrée d'historique (relation Many-to-One)
    # Type : Many-to-One (plusieurs entrées d'historique → un lot)
    # back_populates : Relation bidirectionnelle avec Lot.price_history
    # Impact BDD : FK lot_id → lots.id ON DELETE CASCADE
    # Cascade : Géré au niveau BDD (ondelete="CASCADE" dans ForeignKey)
    # Suppression lot → suppression automatique de tout son historique
    # Utilisation : Accès à lot.price_history pour afficher le graphique
    lot = relationship("Lot", back_populates="price_history")

    def __repr__(self):
        """
        Représentation textuelle de l'objet PriceHistory pour le debugging

        Returns:
            str : Format "<PriceHistory lot={lot_id} price={price}>"

        Utilisation : Affichage dans les logs, debugging, shell interactif
        Exemple : <PriceHistory lot=42 price=15000> (150.00€)
        """
        return f"<PriceHistory lot={self.lot_id} price={self.price}>"
