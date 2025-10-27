from playwright.sync_api import sync_playwright
from threading import Thread
from tkinter import Tk, messagebox
import time

urls_data = {
    "https://encheres-domaine.gouv.fr/lot/honda-crf-150-r.html": ("Crf bon etat", "50"),
    "https://encheres-domaine.gouv.fr/lot/honda-crf-150-r-doo-1.html": ("crf mauvais etat", "51"),
    "https://encheres-domaine.gouv.fr/lot/68b6e95cb0058.html": ("kisbee", "62"),
    "https://encheres-domaine.gouv.fr/lot/250421bi01601.html": ("vespa", "59"),
    "https://encheres-domaine.gouv.fr/lot/quadyamahacw008af-1.html": ("raptor", "64"),
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
                    Thread(target=show_alert, args=(message,), daemon=True).start()

                pages[url]["prix"] = new_prix
                print(f"Rafraîchi: {info['titre']} - {new_prix}")

monitor()
