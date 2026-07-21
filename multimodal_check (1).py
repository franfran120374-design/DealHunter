#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérification des annonces d'occasion via l'ai-aggregator existant.

IMPORTANT : /chat sur ai-aggregator n'accepte que du texte pour l'instant
(ChatRequest = {prompt, category, provider, model_id, premium, premium_provider} -
pas de champ image). Cette version fait donc un check textuel (cohérence
titre/prix/état), PAS une analyse de photo. Pour du vrai multimodal (analyser
la photo de l'annonce), il faut d'abord ajouter un champ image à ChatRequest
et un chemin vision dans call_model() côté ai-aggregator -> c'est un chantier
séparé sur ce repo-là, pas quelque chose que DealHunter peut faire seul.
"""

import os
import re
import json
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

Sois suspect si : la réduction dépasse 70% sans justification apparente,
l'état déclaré est incohérent avec le prix, ou le titre contient des
signaux classiques d'arnaque (paiement hors plateforme, urgence artificielle)."""


def verifier_offre(offre, prix_neuf, timeout=15):
    """Check textuel via ai-aggregator. Retourne un dict {"suspect", "raison"}
    ou None si le service est indisponible (jamais d'avis inventé)."""
    prompt = PROMPT_VERIFICATION.format(
        titre=offre.get("titre", "?"),
        prix=offre.get("prix", "?"),
        etat=offre.get("etat", "?"),
        prix_neuf=prix_neuf or "inconnu",
    )

    headers = {"Content-Type": "application/json"}
    if APP_ACCESS_TOKEN:
        headers["X-Access-Token"] = APP_ACCESS_TOKEN

    try:
        resp = requests.post(
            f"{AI_AGGREGATOR_URL}/chat",
            json={"prompt": prompt, "category": "analyse"},
            headers=headers,
            timeout=timeout,
        )
        resp.raise_for_status()
        texte = resp.json().get("response", "")
        match = re.search(r"\{.*\}", texte, re.DOTALL)
        return json.loads(match.group(0)) if match else None
    except Exception as e:
        print(f"[verifier_offre] ai-aggregator indisponible : {e}")
        return None


def verifier_bonnes_affaires(bonnes_affaires, prix_neuf):
    for offre in bonnes_affaires:
        offre["verification_ia"] = verifier_offre(offre, prix_neuf)
    return bonnes_affaires
