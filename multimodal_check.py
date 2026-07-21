#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérification multimodale des annonces d'occasion, via l'ai-aggregator existant
(ai-aggregator-78gp.onrender.com), qui route déjà vers Gemini (vision).

But : filtrer les annonces suspectes avant de les afficher comme "bonne affaire" -
prix anormalement bas + photo générique/stock = souvent une arnaque ou une
annonce déjà vendue republiée. On ne bloque jamais silencieusement une offre :
on ajoute un champ `verification_ia` que le frontend peut afficher.
"""

import os
import requests

AI_AGGREGATOR_URL = os.getenv("AI_AGGREGATOR_URL", "https://ai-aggregator-78gp.onrender.com")
APP_ACCESS_TOKEN = os.getenv("APP_ACCESS_TOKEN", "")

PROMPT_VERIFICATION = """Tu analyses une annonce de vente d'occasion pour détecter les signaux d'arnaque.
Titre : {titre}
Prix affiché : {prix}€
État déclaré : {etat}
Prix neuf de référence : {prix_neuf}€

Réponds en JSON strict, une seule ligne, sans texte autour :
{{"suspect": true/false, "raison": "phrase courte en français"}}

Sois suspect si : la réduction dépasse 70% sans justification, l'état déclaré
est incohérent avec le prix, ou le titre contient des signaux classiques
d'arnaque (paiement hors plateforme, urgence artificielle, etc.)."""


def verifier_offre(offre, prix_neuf, image_url=None, timeout=15):
    """Appelle l'ai-aggregator pour un avis sur une offre. Retourne un dict
    {"suspect": bool, "raison": str} ou None si le service est indisponible
    (on n'invente pas d'avis)."""
    prompt = PROMPT_VERIFICATION.format(
        titre=offre.get("titre", "?"),
        prix=offre.get("prix", "?"),
        etat=offre.get("etat", "?"),
        prix_neuf=prix_neuf or "inconnu",
    )

    payload = {"message": prompt}
    if image_url:
        payload["image_url"] = image_url  # à adapter au schéma réel de ton endpoint /chat

    headers = {"Content-Type": "application/json"}
    if APP_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {APP_ACCESS_TOKEN}"

    try:
        resp = requests.post(f"{AI_AGGREGATOR_URL}/chat", json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        texte = data.get("response") or data.get("message") or ""

        import json as _json
        import re as _re
        match = _re.search(r"\{.*\}", texte, _re.DOTALL)
        if not match:
            return None
        return _json.loads(match.group(0))

    except Exception as e:
        print(f"[verifier_offre] ai-aggregator indisponible : {e}")
        return None


def verifier_bonnes_affaires(bonnes_affaires, prix_neuf):
    """Enrichit chaque bonne affaire avec `verification_ia` (ou None si le
    check n'a pas pu être fait)."""
    for offre in bonnes_affaires:
        avis = verifier_offre(offre, prix_neuf, image_url=offre.get("image"))
        offre["verification_ia"] = avis
    return bonnes_affaires
