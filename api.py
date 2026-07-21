#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DealHunter API - FastAPI

Déploiement conseillé : même pattern que ai-aggregator (service Render séparé).
Variables d'environnement requises : SERPAPI_KEY, APP_ACCESS_TOKEN (optionnel),
AI_AGGREGATOR_URL (optionnel, a une valeur par défaut).
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from scraper import comparer
from multimodal_check import verifier_bonnes_affaires

app = FastAPI(title="DealHunter API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restreins à franfran120374-design.github.io en prod si besoin
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok", "version": "3.0"}


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
