import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

# Récupère la clé API
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

if not SERPAPI_KEY:
    print("❌ ERREUR: Clé API manquante ! Vérifie ton fichier .env")
    exit()

def rechercher_prix(produit):
    """
    Recherche les prix d'un produit via SerpApi (Google Shopping)
    """
    url = "https://serpapi.com/search"
    
    params = {
        "engine": "google_shopping",
        "q": produit,
        "api_key": SERPAPI_KEY,
        "gl": "fr",           # Localisation France
        "hl": "fr",           # Langue français
    }
    
    print(f"🔍 Recherche en cours pour: {produit}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extrait les résultats shopping
        results = data.get("shopping_results", [])
        
        if not results:
            print("⚠️ Aucun résultat trouvé")
            return None
        
        # Crée une liste de dictionnaires avec les infos utiles
        deals = []
        for item in results[:10]:  # Limite à 10 résultats
            deal = {
                "titre": item.get("title", "N/A"),
                "prix": item.get("price", "N/A"),
                "lien": item.get("link", "N/A"),
                "source": item.get("source", "N/A"),
                "note": item.get("rating", "N/A"),
            }
            deals.append(deal)
        
        return pd.DataFrame(deals)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


def comparer_prix(df):
    """
    Analyse les prix pour trouver le meilleur deal
    """
    if df is None or df.empty:
        return
    
    print("\n" + "="*50)
    print("📊 RÉSULTATS DE LA RECHERCHE")
    print("="*50)
    
    # Affiche le tableau complet
    print(df.to_string())
    
    print("\n" + "="*50)
    print("🏆 TOP 3 DES MEILLEURS PRIX")
    print("="*50)
    
    # Trie par prix (extraction du nombre)
    def extraire_prix(prix_str):
        try:
            return float(prix_str.replace("€", "").replace(",", ".").strip())
        except:
            return float('inf')
    
    df['prix_numerique'] = df['prix'].apply(extraire_prix)
    top_3 = df.nsmallest(3, 'prix_numerique')
    
    for i, row in top_3.iterrows():
        print(f"\n{i+1}. {row['titre'][:50]}...")
        print(f"   💰 Prix: {row['prix']}")
        print(f"   🏪 Source: {row['source']}")
        print(f"   🔗 {row['lien'][:80]}...")


# ========== PROGRAMME PRINCIPAL ==========

if __name__ == "__main__":
    
    print("="*50)
    print("🛒 DEALHUNTER - Comparateur de Prix")
    print("="*50)
    
    # Demande le produit à l'utilisateur
    produit = input("\nQuel produit cherches-tu ? ")
    
    # Lance la recherche
    resultats = rechercher_prix(produit)
    
    # Compare les prix
    comparer_prix(resultats)
    
    # Sauvegarde optionnelle
    if resultats is not None:
        sauvegarder = input("\n💾 Sauvegarder les résultats en CSV ? (o/n) ")
        if sauvegarder.lower() == 'o':
            nom_fichier = f"deals_{produit.replace(' ', '_')[:20]}.csv"
            resultats.to_csv(nom_fichier, index=False)
            print(f"✅ Sauvegardé dans: {nom_fichier}")
    
    print("\n✨ Recherche terminée !")