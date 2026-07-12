# 1_preparation_coffre.py
# Script de preparation pour DealHunter

import pandas as pd
import numpy as np

print("🚀 Le script DealHunter se lance...")

# Exemple : creation d'un coffre de donnees vide
coffre = pd.DataFrame({
    "nom": ["Article_1", "Article_2"],
    "prix": [10.5, 24.0],
    "en_promo": [True, False]
})

print("Voici le contenu du coffre :")
print(coffre)

print("✅ Preparation terminee avec succes !")