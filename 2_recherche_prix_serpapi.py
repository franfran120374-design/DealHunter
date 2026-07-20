import requests
import json
import os

def rechercher_produits(api_key, query):
    url = f"https://serpapi.com/search.json?q={query}&tbm=shop&api_key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def extraire_informations(resultats):
    if 'shopping_results' in resultats:
        for produit in resultats['shopping_results']:
            print(f"Nom : {produit.get('title')}")
            print(f"Prix : {produit.get('price')}")
            print(f"Vendeur : {produit.get('source')}")
            print("-" * 20)
    else:
        print("Aucun résultat trouvé")

def main():
    api_key = os.environ.get('SERPAPI_KEY')
    if api_key is None:
        print("Erreur : La variable d'environnement SERPAPI_KEY n'est pas définie.")
        return
    
    query = "iPhone 14"
    print(f"Recherche de '{query}' en cours...")
    resultats = rechercher_produits(api_key, query)

    if resultats:
        print("Résultats trouvés :")
        extraire_informations(resultats)
    else:
        print("Erreur lors de la récupération des résultats")

if __name__ == "__main__":
    main()