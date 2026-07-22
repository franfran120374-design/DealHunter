#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DealHunter API - FastAPI

Déploiement conseillé : même pattern que ai-aggregator (service Render séparé).
Variables d'environnement requises : SERPAPI_KEY, APP_ACCESS_TOKEN (optionnel),
AI_AGGREGATOR_URL (optionnel, a une valeur par défaut).

Nouvelles variables (onglets Recommandation d'achat / Revente) :
GOOGLE_SHEET_WEBHOOK_URL (webhook Apps Script, voir apps_script/Code.gs),
MARGE_MIN (optionnel, défaut 0.25 = 25%).
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper import comparer
from multimodal_check import verifier_bonnes_affaires
from revente import prix_revente_min, generer_annonce
from google_sheets import log_achat, list_achats, update_achat

app = FastAPI(title="DealHunter API", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restreins à franfran120374-design.github.io en prod si besoin
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AchatIn(BaseModel):
    titre: str
    prix: float
    site: str = ""
    url: str = ""
    image: str = ""
    etat: str = ""


class AnnonceIn(BaseModel):
    id: str = ""
    titre: str
    prix_achat: float
    etat: str = ""


@app.get("/")
def health():
    return {"status": "ok", "version": "4.0"}


@app.get("/search")
def search(
    q: str = Query(..., min_length=2, description="Produit recherché"),
    verify: bool = Query(False, description="Active la vérification multimodale IA sur les bonnes affaires (plus lent)"),
    num: int = Query(5, ge=1, le=10),
):
    if not q.strip():
        raise HTTPException(400, "Requête vide")

    resultat = comparer(q, num=num)

    if verify and resultat["bonnes_affaires"]:
        resultat["bonnes_affaires"] = verifier_bonnes_affaires(
            resultat["bonnes_affaires"], resultat["prix_neuf_min"]
        )

    return resultat


@app.post("/achat")
def acheter(offre: AchatIn):
    """Appelé quand l'utilisateur clique 'Acheter' sur une recommandation.
    Trace l'achat dans Google Sheets et renvoie le prix de revente plancher
    (marge minimum garantie) pour préparer l'onglet Revente."""
    prix_revente = prix_revente_min(offre.prix)
    row = {
        "titre": offre.titre,
        "site": offre.site,
        "prix_achat": offre.prix,
        "url": offre.url,
        "image": offre.image,
        "etat": offre.etat,
        "prix_revente_suggere": prix_revente,
    }
    tracked = log_achat(row)
    return {
        "ok": True,
        "tracked_in_sheets": tracked,
        "prix_revente_min": prix_revente,
    }


@app.get("/achats")
def achats():
    """Liste des achats trackés, utilisée par l'onglet Revente."""
    return {"achats": list_achats()}


@app.post("/generer-annonce")
def annonce(item: AnnonceIn):
    """Génère une annonce de revente (titre + description + prix conseillé)
    via l'ai-aggregator, avec un prix plancher garantissant la marge min."""
    resultat = generer_annonce(item.titre, item.prix_achat, item.etat)
    if resultat is None:
        raise HTTPException(503, "ai-aggregator indisponible, réessaie plus tard")

    if item.id:
        update_achat(item.id, {
            "annonce_titre": resultat.get("titre_annonce", ""),
            "annonce_description": resultat.get("description", ""),
            "prix_conseille": resultat.get("prix_conseille", ""),
            "statut": "annonce_prete",
        })

    return resultat
