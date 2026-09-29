"""Veille coffrets Pokémon : alerte Discord sur nouvelle fiche ou retour en stock.
Ce fichier orchestre la lecture de chaque site (un module par site) et gère
la comparaison avec l'état précédent, via les fonctions communes."""
import sys

import commun
import commun, site_lechoppe, site_enviedejapon

SITES = [site_lechoppe, site_enviedejapon]


def main():
    ancien = commun.charger_etat()
    nouveau = dict(ancien or {})

    for site in SITES:
        nom_site = site.__name__
        try:
            produits = site.lire()
        except Exception as e:  # site bloqué, panne, etc. : on continue
            print(f"[ERREUR] {nom_site} : {e}", file=sys.stderr)
            continue

        if not produits:
            print(f"[ATTENTION] aucun produit lu sur {nom_site} (structure changée ou blocage ?)")
        else:
            print(f"[INFO] {len(produits)} produit(s) lu(s) sur {nom_site} :")
            for p in produits.values():
                statut = "en stock" if p["en_stock"] else "indisponible"
                print(f"   - {p['nom']} | {p['prix']} | {statut}")

        for url, p in produits.items():
            avant = (ancien or {}).get(url)
            if ancien is not None:  # pas d'alerte au tout premier passage
                if avant is None:
                    qte = site.lire_quantite(url)
                    suffixe = f" — {qte} en stock" if qte is not None else ""
                    commun.alerter(f"🆕 Nouvelle fiche : **{p['nom']}** ({p['prix']}){suffixe}\n{url}")
                elif p["en_stock"] and not avant["en_stock"]:
                    qte = site.lire_quantite(url)
                    suffixe = f" — {qte} en stock" if qte is not None else ""
                    commun.alerter(f"✅ De retour en stock : **{p['nom']}** ({p['prix']}){suffixe}\n{url}")
            nouveau[url] = p

    commun.sauvegarder_etat(nouveau)


if __name__ == "__main__":
    main()
