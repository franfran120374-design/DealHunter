#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DealHunter V3 - Moteur de comparaison de prix (données réelles, sans simulation)

Sources :
- Neuf      : SerpAPI (engine=google_shopping)
- Occasion  : SerpAPI (engine=ebay) + BackMarket (endpoint JSON public de recherche)
- LeBonCoin : non implémenté (anti-bot DataDome trop agressif pour du scraping direct
              sans proxy résidentiel payant) -> stub qui renvoie une liste vide + un flag

Chaque résultat porte un champ `donnees_reelles: bool` pour ne JAMAIS laisser
planer le doute sur l'origine d'un prix. S'il n'y a pas de données réelles
disponibles pour une source, on ne l'affiche pas, on ne l'invente pas.
"""

import os
import re
import requests
from datetime import datetime

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
SEUIL_BONNE_AFFAIRE = float(os.getenv("SEUIL_BONNE_AFFAIRE", "0.60"))  # 60% du prix neuf max


def extraire_prix(prix_str):
    """Extrait un nombre depuis '499,99 EUR' -> 499.99"""
    if not prix_str or prix_str in ("N/A", None):
        return None
    clean = str(prix_str).replace("EUR", "").replace("€", "").replace(" ", "").replace(",", ".")
    nombres = re.findall(r"\d+\.?\d*", clean)
    return float(nombres[0]) if nombres else None


# ============================================================================
# PARTIE 1 : PRIX NEUFS (SerpAPI Google Shopping)
# ============================================================================

def chercher_prix_neufs(query, num=5):
    """Retourne (liste_offres, prix_min) ou (None, None) si indisponible.
    Ne renvoie JAMAIS de données de démo silencieuses : si la clé est absente
    ou l'appel échoue, on retourne explicitement None pour que l'appelant
    puisse le signaler à l'utilisateur."""
    if not SERPAPI_KEY:
        return None, None

    try:
        from serpapi import GoogleSearch
    except ImportError:
        return None, None

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_KEY,
        "gl": "fr",
        "hl": "fr",
        "num": num,
    }

    try:
        results = GoogleSearch(params).get_dict()
        shopping = results.get("shopping_results", [])
        if not shopping:
            return [], None

        neufs = []
        for i, item in enumerate(shopping[:num], 1):
            prix_num = extraire_prix(item.get("price"))
            if prix_num is None:
                continue
            neufs.append({
                "rang": i,
                "titre": str(item.get("title", "?"))[:80],
                "prix": prix_num,
                "prix_affiche": item.get("price", "?"),
                "source": str(item.get("source", "?")),
                "lien": item.get("product_link", item.get("link", "#")),
                "image": item.get("thumbnail"),
                "donnees_reelles": True,
            })

        prix_min = min((n["prix"] for n in neufs), default=None)
        return neufs, prix_min

    except Exception as e:
        print(f"[chercher_prix_neufs] Erreur API : {e}")
        return None, None


# ============================================================================
# PARTIE 2 : PRIX OCCASION - eBay via SerpAPI
# ============================================================================

def chercher_ebay(query, num=5):
    """Occasion réelle via le moteur eBay de SerpAPI. Retourne None si indisponible."""
    if not SERPAPI_KEY:
        return None

    try:
        from serpapi import GoogleSearch
    except ImportError:
        return None

    params = {
        "engine": "ebay",
        "_nkw": query,
        "ebay_domain": "ebay.fr",
        "LH_ItemCondition": "3000",  # filtre "occasion" côté eBay
        "api_key": SERPAPI_KEY,
    }

    try:
        results = GoogleSearch(params).get_dict()
        items = results.get("organic_results", [])
        offres = []
        for item in items[:num]:
            prix_num = extraire_prix(item.get("price", {}).get("raw") if isinstance(item.get("price"), dict) else item.get("price"))
            if prix_num is None:
                continue
            offres.append({
                "site": "eBay",
                "titre": str(item.get("title", "?"))[:80],
                "prix": prix_num,
                "etat": item.get("condition", "Occasion"),
                "url": item.get("link", "#"),
                "image": item.get("thumbnail"),
                "donnees_reelles": True,
            })
        return offres
    except Exception as e:
        print(f"[chercher_ebay] Erreur API : {e}")
        return None


# ============================================================================
# PARTIE 3 : PRIX OCCASION - BackMarket (endpoint JSON public)
# ============================================================================

def chercher_backmarket(query, num=5):
    """Interroge l'endpoint de recherche JSON public de BackMarket.
    C'est un endpoint non officiel (pas d'API publique documentée) : plus stable
    qu'un scraping HTML classique, mais peut casser si BackMarket change son front.
    Retourne None si l'appel échoue, jamais de données inventées."""
    url = "https://www.backmarket.fr/bapi/marketing/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DealHunter/1.0)",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, params={"q": query, "page_size": num}, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        offres = []
        for item in data.get("results", [])[:num]:
            prix_num = extraire_prix(item.get("price"))
            if prix_num is None:
                continue
            offres.append({
                "site": "BackMarket",
                "titre": str(item.get("title", "?"))[:80],
                "prix": prix_num,
                "etat": item.get("grade_display", "Reconditionné"),
                "url": "https://www.backmarket.fr" + item.get("url_path", ""),
                "image": item.get("image_url"),
                "donnees_reelles": True,
            })
        return offres
    except Exception as e:
        print(f"[chercher_backmarket] Endpoint indisponible ou format changé : {e}")
        return None


# ============================================================================
# PARTIE 4 : LeBonCoin - stub explicite (pas de simulation)
# ============================================================================

def chercher_leboncoin(query, num=5):
    """Non implémenté : DataDome bloque le scraping direct sans proxy résidentiel.
    Retourne toujours None pour signaler clairement 'source indisponible'
    plutôt que de générer un faux résultat."""
    return None


# ============================================================================
# PARTIE 5 : Agrégation
# ============================================================================

def comparer(query, num=5):
    """Point d'entrée principal. Ne mélange jamais du réel et du généré :
    chaque source manquante est signalée comme telle dans `sources_indisponibles`."""
    neufs, prix_neuf_min = chercher_prix_neufs(query, num)

    occasions = []
    sources_indisponibles = []

    ebay = chercher_ebay(query, num)
    if ebay is None:
        sources_indisponibles.append("eBay")
    else:
        occasions.extend(ebay)

    backmarket = chercher_backmarket(query, num)
    if backmarket is None:
        sources_indisponibles.append("BackMarket")
    else:
        occasions.extend(backmarket)

    leboncoin = chercher_leboncoin(query, num)
    sources_indisponibles.append("LeBonCoin (non implémenté)")

    bonnes_affaires = []
    if prix_neuf_min:
        for o in occasions:
            reduction_pct = ((prix_neuf_min - o["prix"]) / prix_neuf_min) * 100
            o["reduction_pct"] = round(reduction_pct, 1)
            o["est_bonne_affaire"] = o["prix"] <= prix_neuf_min * SEUIL_BONNE_AFFAIRE
            if o["est_bonne_affaire"]:
                bonnes_affaires.append(o)

    occasions.sort(key=lambda o: o["prix"])

    return {
        "query": query,
        "horodatage": datetime.utcnow().isoformat(),
        "prix_neuf_min": prix_neuf_min,
        "offres_neuves": neufs or [],
        "offres_occasion": occasions,
        "bonnes_affaires": bonnes_affaires,
        "sources_indisponibles": sources_indisponibles,
        "cle_serpapi_configuree": bool(SERPAPI_KEY),
    }


if __name__ == "__main__":
    import sys
    import json
    q = " ".join(sys.argv[1:]) or "iPhone 13 128Go"
    resultat = comparer(q)
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
