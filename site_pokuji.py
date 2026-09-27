import re
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (veille-pokemon-bot)"}

# Catégories à surveiller sur pokuji.fr
URLS_CATEGORIES = [
    "https://pokuji.fr/produits/cartes-a-collectionner-tcg/pokemon/pokemon-francais/",
    "https://pokuji.fr/produits/cartes-a-collectionner-tcg/one-piece/one-piece-francais/",
]


def _parse_page(html):
    """Extrait les produits d'une page de catégorie pokuji.fr."""
    soup = BeautifulSoup(html, "html.parser")
    produits = {}

    for div in soup.select("div.e-loop-item.product"):
        classes = div.get("class", [])
        en_stock = "instock" in classes  # WooCommerce pose cette classe de façon fiable

        lien = div.select_one("h3.product_title a")
        if not lien or not lien.get("href"):
            continue
        url = lien["href"].split("?")[0].rstrip("/")
        nom = lien.get_text(strip=True)

        # Prix : priorité au prix soldé (ins) s'il existe, sinon prix normal
        prix_tag = div.select_one("ins span.woocommerce-Price-amount") \
            or div.select_one("span.woocommerce-Price-amount")
        prix = prix_tag.get_text(" ", strip=True).replace("\xa0", " ") if prix_tag else "?"

        stock_tag = div.select_one("p.stock")
        texte_stock = stock_tag.get_text(strip=True) if stock_tag else ""

        produits[url] = {
            "nom": nom,
            "prix": prix,
            "en_stock": en_stock,
            "texte_stock": texte_stock,
        }

    return produits


def _a_une_page_suivante(html):
    """Vérifie s'il existe un lien vers la page suivante dans la pagination."""
    soup = BeautifulSoup(html, "html.parser")
    nav = soup.select_one("nav.elementor-pagination")
    if not nav:
        return False
    return nav.select_one("a.page-numbers.next") is not None


def lire():
    """Lit toutes les catégories surveillées sur pokuji.fr (avec pagination)."""
    tous_produits = {}

    for url_categorie in URLS_CATEGORIES:
        page = 1
        while True:
            url_page = url_categorie if page == 1 else f"{url_categorie}page/{page}/"
            try:
                reponse = requests.get(url_page, headers=HEADERS, timeout=20)
            except requests.RequestException as e:
                print(f"[ERREUR] pokuji.fr {url_page} : {e}")
                break

            if reponse.status_code == 404:
                break
            reponse.raise_for_status()

            produits_page = _parse_page(reponse.text)
            if not produits_page:
                break

            tous_produits.update(produits_page)

            if not _a_une_page_suivante(reponse.text):
                break
            page += 1

    return tous_produits


def lire_quantite(url):
    """Va chercher sur la fiche produit le nombre exact d'exemplaires en stock, si affiché."""
    try:
        reponse = requests.get(url, headers=HEADERS, timeout=20)
        reponse.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(reponse.text, "html.parser")
    stock_tag = soup.select_one(".stockQuantityLeft .elementor-shortcode")
    if stock_tag:
        texte = stock_tag.get_text(strip=True)
        m = re.search(r"Plus que (\d+) en stock", texte)
        if m:
            return int(m.group(1))
    return None
