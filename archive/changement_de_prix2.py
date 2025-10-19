from playwright.sync_api import sync_playwright
from threading import Thread
from tkinter import Tk, messagebox
import time

urls_data = {
    "https://encheres-domaine.gouv.fr/lot/ar-volkswagen-golf-vii-agrasc.html": ("Golf 7 Gti", "197"),
    "https://encheres-domaine.gouv.fr/lot/2506031br00830.html": ("Clio 4", "141"),
    "https://encheres-domaine.gouv.fr/lot/renault-clio-doo-37.html": ("Clio 3 2eme", "132"),
    "https://encheres-domaine.gouv.fr/lot/26vl2025-1.html": ("DS3", "151"),
    "https://encheres-domaine.gouv.fr/lot/dc-538-vp-1.html": ("Partner", "208"),
    "https://encheres-domaine.gouv.fr/lot/lot-de-4-trottinettes-electriques.html": ("trottinettes", "134"),
}

def show_alert(message):
    """Chaque alerte s'exécute dans sa propre boucle Tkinter."""
    def popup():
        root = Tk()
        root.withdraw()
        messagebox.showinfo("💸 Changement de prix détecté", message)
        root.destroy()
        root.quit()  # ferme proprement la boucle Tkinter

    # Lance une boucle Tkinter isolée dans ce thread
    root_thread = Thread(target=popup)
    root_thread.start()

def get_price(page):
    """Récupère uniquement le prix actuel."""
    try:
        prix = page.locator("p.fr-price__price").text_content().strip()
    except:
        prix = "N/A"
    return prix

def monitor():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        pages = {}

        # Initialisation
        for url, (titre, num) in urls_data.items():
            page = browser.new_page()
            page.goto(url)
            time.sleep(2)
            prix = get_price(page)
            print(f"Lot {num}: {titre} - {prix}")
            pages[url] = {"page": page, "titre": titre, "prix": prix, "num": num}

        # Boucle de surveillance
        while True:
            time.sleep(30)  # toutes les 60 secondes pour les tests
            for url, info in pages.items():
                page = info["page"]
                new_prix = get_price(page)

                if new_prix != info["prix"]:
                    message = f"💰 Le prix de '{info['titre']}' (lot {info['num']}) a changé : {info['prix']} → {new_prix}"
                    print(message)
                    #Thread(target=show_alert, args=(message,), daemon=True).start()

                pages[url]["prix"] = new_prix
                print(f"Rafraîchi: {info['titre']} - {new_prix}")

monitor()
