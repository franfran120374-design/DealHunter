#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revente : calcul du prix plancher (marge min garantie) et génération
d'annonce via l'ai-aggregator existant (même pattern que multimodal_check.py).
"""

import os
import re
import json
import requests

AI_AGGREGATOR_URL = os.getenv("AI_AGGREGATOR_URL", "https://ai-aggregator-78gp.onrender.com")
APP_ACCESS_TOKEN = os.getenv("APP_ACCESS_TOKEN", "")
MARGE_MIN = float(os.getenv("MARGE_MIN", "0.25"))  # 25% par défaut, sur le prix d'achat

PROMPT_ANNONCE = """Rédige une annonce de revente en français pour cet objet d'occasion, prête à publier sur Vinted/LeBonCoin.
Titre original : {titre}
Prix d'achat : {prix_achat}€
Prix de vente minimum : {prix_revente}€ (marge {marge}% minimum sur le prix d'achat)
État : {etat}

Réponds en JSON strict, une seule ligne, sans texte autour :
{{"titre_annonce": "...", "description": "...", "prix_conseille": nombre}}
Le titre_annonce doit être court et accrocheur (<80 caractères).
La description doit être honnête sur l'état, sans rien inventer, et donner envie d'acheter.
Le prix_conseille doit toujours être >= {prix_revente}€."""


def prix_revente_min(prix_achat: float) -> float:
    """Prix plancher pour garantir la marge minimum définie par MARGE_MIN."""
    return round(prix_achat * (1 + MARGE_MIN), 2)


def generer_annonce(titre, prix_achat, etat=None, timeout=20):
    """Génère titre + description + prix conseillé via ai-aggregator.
    Retourne None si le service est indisponible (jamais d'annonce inventée
    localement sans passer par l'IA)."""
    prix_revente = prix_revente_min(prix_achat)
    prompt = PROMPT_ANNONCE.format(
        titre=titre,
        prix_achat=prix_achat,
        prix_revente=prix_revente,
        marge=int(MARGE_MIN * 100),
        etat=etat or "occasion, bon état",
    )

    headers = {"Content-Type": "application/json"}
    if APP_ACCESS_TOKEN:
        headers["X-Access-Token"] = APP_ACCESS_TOKEN

    try:
        resp = requests.post(
            f"{AI_AGGREGATOR_URL}/chat",
            json={"prompt": prompt, "category": "redaction"},
            headers=headers,
            timeout=timeout,
        )
        resp.raise_for_status()
        texte = resp.json().get("response", "")
        match = re.search(r"\{.*\}", texte, re.DOTALL)
        annonce = json.loads(match.group(0)) if match else None
        if annonce and annonce.get("prix_conseille", 0) < prix_revente:
            annonce["prix_conseille"] = prix_revente  # garde-fou marge mini
        return annonce
    except Exception as e:
        print(f"[generer_annonce] ai-aggregator indisponible : {e}")
        return None
