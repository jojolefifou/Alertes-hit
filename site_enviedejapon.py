import re
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (veille-pokemon-bot)"}

BASE_URL = "https://enviedejapon.hiboutik.com/shop/"

# Catégories à surveiller
URLS_CATEGORIES = [
    "https://enviedejapon.hiboutik.com/shop/?page=products&cat=124",
    "https://enviedejapon.hiboutik.com/shop/?page=products&cat=125",
]


def _parse_categorie(html):
    """Extrait les produits (nom, prix, url) d'une page de catégorie Hiboutik."""
    soup = BeautifulSoup(html, "html.parser")
    produits = {}

    for figure in soup.select("figure.g-pos-rel"):
        lien = figure.select_one("a[href*='page=product']")
        if not lien or not lien.get("href"):
            continue

        href = lien["href"]  # ex: "?page=product&id=14441"
        m = re.search(r"id=(\d+)", href)
        if not m:
            continue

        url = BASE_URL + href

        media = figure.find_next_sibling("div", class_="media")
        nom = None
        prix = "?"
        if media:
            nom_tag = media.select_one("h4 a")
            if nom_tag:
                nom = nom_tag.get_text(strip=True)
            prix_tag = media.select_one("span.g-font-size-17")
            if prix_tag:
                prix = prix_tag.get_text(strip=True)

        if not nom:
            img = figure.select_one("img")
            nom = img.get("alt", "?").strip() if img else "?"

        produits[url] = {"nom": nom, "prix": prix}

    return produits


def _lire_stock(url):
    """Va chercher le stock exact affiché sur la fiche produit ('Stock: 19')."""
    try:
        reponse = requests.get(url, headers=HEADERS, timeout=20)
        reponse.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(reponse.text, "html.parser")
    for li in soup.select("li"):
        texte = li.get_text(strip=True)
        m = re.match(r"Stock:\s*(-?\d+)", texte)
        if m:
            return int(m.group(1))
    return None


def lire():
    """Lit les catégories surveillées, puis va chercher le stock de chaque produit."""
    tous_produits = {}

    for url_cat in URLS_CATEGORIES:
        try:
            reponse = requests.get(url_cat, headers=HEADERS, timeout=20)
            reponse.raise_for_status()
        except requests.RequestException as e:
            print(f"[ERREUR] enviedejapon {url_cat} : {e}")
            continue
        tous_produits.update(_parse_categorie(reponse.text))

    # Le stock n'est visible que sur la fiche produit : on va le chercher pour chacun
    for url, infos in tous_produits.items():
        stock = _lire_stock(url)
        infos["en_stock"] = stock is None or stock > 0
        infos["stock"] = stock

    return tous_produits


def lire_quantite(url):
    """Utilisé par monitor.py pour afficher la quantité exacte dans l'alerte."""
    return _lire_stock(url)
