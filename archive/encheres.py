from playwright.sync_api import sync_playwright
from selectolax.parser import HTMLParser
import csv
import re

output_file = "/home/samir/Bureau/encheres.csv"

def extract_number(text):
    """Extrait le premier nombre entier trouvé dans le texte"""
    match = re.search(r'\d+', text.replace(' ', ''))
    return int(match.group()) if match else None

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    numero_de_vente = 87
    page_number = 1
    all_data = []

    while True:
        url = f"https://encheres-domaine.gouv.fr/vente/{numero_de_vente}?page={page_number}"
        print(f"🔹 Récupération de la page {page_number} ...")
        page.goto(url, wait_until="networkidle")
        html = page.content()

        tree = HTMLParser(html)
        ul = tree.css_first("ul.fr-list-product")
        if not ul:
            print("⚠️ Plus d'annonces trouvées ou page vide. Fin de la récupération.")
            break

        for item in ul.css("div.fr-list-product__item"):
            # Titre et URL du lot
            title_node = item.css_first("h3.fr-card-product__title a")
            title = title_node.text(strip=True) if title_node else "N/A"
            url_lot = "https://encheres-domaine.gouv.fr" + title_node.attributes.get("href", "") if title_node else "N/A"

            # Numéro de lot
            lot_node = item.css_first("p.fr-card-product__desc span")
            lot_number = extract_number(lot_node.text(strip=True)) if lot_node else None

            # Prix et statut
            price_node = item.css_first("p.fr-price__price")
            price = extract_number(price_node.text(strip=True)) if price_node else None
            status_node = item.css_first("p.fr-price__text")
            status = status_node.text(strip=True) if status_node else "N/A"

            # Lieu du dépôt
            depot_node = item.css_first("p.fr-text--xs strong")
            depot = depot_node.text(strip=True) if depot_node else "N/A"

            # Image principale
            img_node = item.css_first("div.fr-card-product__img img")
            img_url = img_node.attributes.get("src", "") if img_node else "N/A"

            # Description courte
            desc_node = item.css_first("div.fr-text--sm.fr-ellipsis--3 p")
            description = desc_node.text(strip=True) if desc_node else "N/A"

            all_data.append({
                "Titre": title,
                "Lot": lot_number,
                "Prix": price,
                "Statut": status,
                "Lieu dépôt": depot,
                "URL Lot": url_lot,
                "URL Image": img_url,
                "Description": description
            })

        page_number += 1

    browser.close()

# Écriture directe dans le CSV
with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["Titre", "Lot", "Prix", "Statut", "Lieu dépôt", "URL Lot", "URL Image", "Description"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in all_data:
        writer.writerow(row)

print(f"✅ Récupération terminée. Données sauvegardées dans : {output_file}")
