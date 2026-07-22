#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suivi des achats dans Google Sheets - via webhook Google Apps Script.

Pourquoi pas l'API Google Sheets officielle : elle demande un service account,
un fichier de credentials JSON à stocker en secret sur Render, et une lib
supplémentaire (google-api-python-client). Un Web App Apps Script fait le
même job en beaucoup plus simple : c'est un script collé directement dans le
Sheet, déployé en "web app", qui expose une URL POST/GET. Aucun secret à
gérer côté DealHunter, juste une URL dans GOOGLE_SHEET_WEBHOOK_URL.

Voir apps_script/Code.gs dans ce repo pour le script à coller dans le Sheet.
"""

import os
import requests

GOOGLE_SHEET_WEBHOOK_URL = os.getenv("GOOGLE_SHEET_WEBHOOK_URL", "")


def log_achat(row: dict, timeout=10) -> bool:
    """Ajoute une ligne 'achat' dans le Sheet. Retourne False si le webhook
    n'est pas configuré ou indisponible (jamais d'exception qui casse /achat)."""
    if not GOOGLE_SHEET_WEBHOOK_URL:
        print("[log_achat] GOOGLE_SHEET_WEBHOOK_URL non configurée - achat non tracké")
        return False
    try:
        resp = requests.post(
            GOOGLE_SHEET_WEBHOOK_URL,
            json={"action": "log_achat", "data": row},
            timeout=timeout,
        )
        resp.raise_for_status()
        return bool(resp.json().get("ok", False))
    except Exception as e:
        print(f"[log_achat] Webhook Sheets indisponible : {e}")
        return False


def list_achats(timeout=10) -> list:
    """Récupère la liste des achats trackés (utilisé par l'onglet Revente)."""
    if not GOOGLE_SHEET_WEBHOOK_URL:
        return []
    try:
        resp = requests.get(
            GOOGLE_SHEET_WEBHOOK_URL,
            params={"action": "list_achats"},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("achats", [])
    except Exception as e:
        print(f"[list_achats] Webhook Sheets indisponible : {e}")
        return []


def update_achat(achat_id: str, updates: dict, timeout=10) -> bool:
    """Met à jour une ligne existante (ex: statut 'revendu', annonce générée)."""
    if not GOOGLE_SHEET_WEBHOOK_URL:
        return False
    try:
        resp = requests.post(
            GOOGLE_SHEET_WEBHOOK_URL,
            json={"action": "update_achat", "id": achat_id, "data": updates},
            timeout=timeout,
        )
        resp.raise_for_status()
        return bool(resp.json().get("ok", False))
    except Exception as e:
        print(f"[update_achat] Webhook Sheets indisponible : {e}")
        return False
