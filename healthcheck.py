#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health-check des sources DealHunter. Tourne en cron (GitHub Action).
Vérifie que le FORMAT de réponse attendu est là, pas juste un 200 OK.
Exit code != 0 si une source casse -> échec du job -> mail automatique.
"""

import os
import sys
import requests

ECHECS = []


def check_serpapi_ebay():
    key = os.getenv("SERPAPI_KEY", "")
    if not key:
        print("⚠️ SERPAPI_KEY absente, eBay non testé.")
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


def check_serpapi_google_shopping():
    key = os.getenv("SERPAPI_KEY", "")
    if not key:
        print("⚠️ SERPAPI_KEY absente, Google Shopping non testé.")
        return
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={"engine": "google_shopping", "q": "iphone 13", "gl": "fr", "hl": "fr", "api_key": key},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("shopping_results"):
            ECHECS.append("Google Shopping (SerpAPI) : pas de shopping_results — vérifier le moteur ou le quota.")
        else:
            print("✅ Google Shopping (SerpAPI) OK")
    except Exception as e:
        ECHECS.append(f"Google Shopping (SerpAPI) : {e}")


if __name__ == "__main__":
    check_serpapi_ebay()
    check_serpapi_google_shopping()

    if ECHECS:
        print("\n❌ Sources en échec :")
        for e in ECHECS:
            print(f"  - {e}")
        sys.exit(1)

    print("\n✅ Toutes les sources répondent avec le format attendu.")
    sys.exit(0)
