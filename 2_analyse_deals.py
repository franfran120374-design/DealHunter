# 2_analyse_deals.py
# Le cerveau de DealHunter : il lit les prix et predit si c'est une bonne affaire

import pandas as pd
from config import SEUIL_PROMO, FICHIER_PRIX

print("🧠 DealHunter analyse les prix...")

# 1. On ouvre le fichier de donnees
donnees = pd.read_csv(FICHIER_PRIX)

# 2. On calcule le prix moyen (la moyenne historique)
prix_moyen = donnees["prix_produit"].mean()

# 3. On prend le dernier prix connu
dernier_prix = donnees["prix_produit"].iloc[-1]

# 4. On calcule la reduction en %
reduction = ((prix_moyen - dernier_prix) / prix_moyen) * 100

print(f"Prix moyen historique : {prix_moyen:.2f} €")
print(f"Dernier prix vu : {dernier_prix:.2f} €")
print(f"Reduction actuelle : {reduction:.1f} %")

# 5. Le MODELE de prediction simple
if reduction >= SEUIL_PROMO:
    print("🚨 ALERTE BON PLAN ! C'est le moment d'acheter !")
else:
    print("😐 Pas encore extraordinaire... On attend un peu.")

print("✅ Analyse terminee.")