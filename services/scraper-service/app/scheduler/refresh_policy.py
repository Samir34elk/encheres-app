"""
Politique de rafraîchissement des lots d'une vente.

Avant : TOUTES les ventes de la BDD (y compris clôturées depuis des mois) étaient
re-scrapées toutes les 15 minutes → des centaines de requêtes par passage → IP bloquée.

Maintenant, une vente n'est re-scrapée que si c'est utile :
- jamais scrapée                    → oui (priorité haute)
- clôturée / date de fin dépassée   → une seule fois après la fin (prix final), puis plus jamais
- se termine dans moins de 3h       → toutes les 15 min
- se termine dans moins de 24h      → toutes les heures
- en cours                          → toutes les 6h
- à venir                           → toutes les 12h

`Sale.last_scraped_at` représente la date du dernier scraping des LOTS de la vente.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings

# Marge après la date de fin avant de capturer l'état final (le site met parfois
# quelques minutes à publier les adjudications).
FINAL_SCRAPE_GRACE = timedelta(minutes=30)


@dataclass(frozen=True)
class RefreshDecision:
    due: bool
    priority: int  # plus petit = plus urgent
    reason: str


def decide_lots_refresh(
    status: Optional[str],
    end_date: Optional[datetime],
    last_scraped_at: Optional[datetime],
    now: datetime,
) -> RefreshDecision:
    if last_scraped_at is None:
        return RefreshDecision(True, 1, "jamais scrapée")

    ended = status == "closed" or (end_date is not None and end_date <= now)
    if ended:
        if end_date is None:
            return RefreshDecision(False, 99, "clôturée (sans date de fin)")
        if now < end_date + FINAL_SCRAPE_GRACE:
            return RefreshDecision(False, 99, "clôture en cours, attente du résultat final")
        if last_scraped_at < end_date + FINAL_SCRAPE_GRACE:
            return RefreshDecision(True, 2, "capture des prix finaux")
        return RefreshDecision(False, 99, "clôturée, déjà finalisée")

    if status == "upcoming" and (end_date is None or end_date - now > timedelta(hours=24)):
        interval = timedelta(minutes=settings.LOTS_REFRESH_UPCOMING_MINUTES)
        priority, label = 6, "à venir"
    elif end_date is not None and end_date - now <= timedelta(hours=3):
        interval = timedelta(minutes=settings.LOTS_REFRESH_ENDING_SOON_MINUTES)
        priority, label = 0, "se termine dans < 3h"
    elif end_date is not None and end_date - now <= timedelta(hours=24):
        interval = timedelta(minutes=settings.LOTS_REFRESH_ENDING_TODAY_MINUTES)
        priority, label = 3, "se termine dans < 24h"
    else:
        interval = timedelta(minutes=settings.LOTS_REFRESH_ACTIVE_MINUTES)
        priority, label = 5, "en cours"

    # Petite tolérance pour ne pas rater un passage à quelques secondes près.
    due = now - last_scraped_at >= interval - timedelta(minutes=1)
    return RefreshDecision(due, priority, label)
