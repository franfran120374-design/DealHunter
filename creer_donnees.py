import pandas as pd

# On cree les donnees a la main dans Python
donnees = pd.DataFrame({
    "date": ["2025-01-15", "2025-02-15", "2025-03-15", "2025-04-15", "2025-05-15", "2025-06-15", "2025-07-01", "2025-07-05", "2025-07-10"],
"prix_produit": [120.00, 120.00, 115.50, 110.00, 120.00, 95.00, 89.99, 120.00, 80.00],
    "nom_produit": ["Casque Audio ZX", "Casque Audio ZX", "Casque Audio ZX", "Casque Audio ZX", "Casque Audio ZX", "Casque Audio ZX", "Casque Audio ZX", "Casque Audio ZX", "Casque Audio ZX"]
})

# On sauvegarde proprement dans un fichier CSV
donnees.to_csv("data_prix.csv", index=False, encoding='utf-8')

print("✅ Fichier data_prix.csv cree proprement par Python !")