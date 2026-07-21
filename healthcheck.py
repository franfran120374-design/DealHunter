#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health-check des sources DealHunter. Pensé pour tourner en cron (GitHub Action).
Ne vérifie PAS juste que le site répond (200 OK) : vérifie que le format de
réponse attendu est toujours là, sinon un changement de layout côté
BackMarket/eBay passerait inaperçu jusqu'à ce qu'on cherche un deal.

Exit code != 0 si une source casse -> fait échouer le job GitHub Actions ->
notification automatique par mail au propriétaire du repo.
"""

import sys
import requests

ECHECS = []


def check_backmarket():
    url = "https://www.backmarket.fr/bapi/marketing/search"
    try:
        resp = requests.get(
            url,
            params={"q": "iphone 13", "page_size": 3},
            headers={"User-Agent": "Mozilla/5.0 (compatible; DealHunter-HealthCheck/1.0)"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            ECHECS.append("BackMarket : réponse 200 mais 'results' vide ou absent — format probablement changé.")
        elif "price" not in results[0] or "title" not in results[0]:
            ECHECS.append(f"BackMarket : les clés attendues (price/title) ne sont plus dans la réponse : {list(results[0].keys())}")
        else:
            print("✅ BackMarket OK")
    except Exception as e:
        ECHECS.append(f"BackMarket : {e}")


def check_serpapi_ebay():
    import os
    key = os.getenv("SERPAPI_KEY", "")
    if not key:
        print("⚠️ SERPAPI_KEY absente de l'environnement du health-check, eBay non testé.")
        return
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={"engine": "ebay", "_nkw": "iphone 13", "ebay_domain": "ebay.fr", "api_key": key},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("organic_results"):
            ECHECS.append("eBay (SerpAPI) : pas de organic_results — vérifier le moteur ou le quota SerpAPI.")
        else:
            print("✅ eBay (SerpAPI) OK")
    except Exception as e:
        ECHECS.append(f"eBay (SerpAPI) : {e}")


if __name__ == "__main__":
    check_backmarket()
    check_serpapi_ebay()

    if ECHECS:
        print("\n❌ Sources en échec :")
        for e in ECHECS:
            print(f"  - {e}")
        sys.exit(1)

    print("\n✅ Toutes les sources répondent avec le format attendu.")
    sys.exit(0)
