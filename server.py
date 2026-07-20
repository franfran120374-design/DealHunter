from flask import Flask, request, jsonify, render_template_string
import sys
import os

# On importe les fonctions spécifiques de ton fichier dealhunter
from dealhunter import chercher_prix_neufs, chercher_occasions, extraire_prix

app = Flask(__name__)

# Un petit template HTML simple pour afficher les résultats joliment
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>DealHunter -Résultats</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; background-color: #f4f4f9; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .card { background: white; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .neuf { border-left: 5px solid #e74c3c; }
        .occas { border-left: 5px solid #27ae60; }
        .prix { font-size: 1.5em; font-weight: bold; color: #333; }
        .source { color: #7f8c8d; font-size: 0.9em; }
        .win { background-color: #d5f5e3; }
    </style>
</head>
<body>
    <h1>🎯 Résultats pour : {{ query }}</h1>
    
    <h2>🏪 Prix Neufs (Référence)</h2>
    {% for item in neufs %}
    <div class="card neuf">
        <div class="prix">{{ item.prix_affiche }}</div>
        <div class="source">{{ item.source }} - {{ item.titre }}</div>
    </div>
    {% endfor %}

    <h2>♻️ Meilleures Occasions</h2>
    {% for item in occaz %}
    <div class="card occas {% if item.est_bonne_affaire %}win{% endif %}">
        <div class="prix">{{ "{:.2f}".format(item.prix) }}€ <span style="font-size:0.6em; color:#e74c3c">(-{{ "{:.0f}".format(item.reduction_pct) }}%)</span></div>
        <div class="source">{{ item.site }} | {{ item.etat }}</div>
        {% if item.est_bonne_affaire %}
        <div style="color: green; font-weight:bold; margin-top:5px;">✅ BONNE AFFAIRE !</div>
        {% endif %}
        <a href="{{ item.url }}" target="_blank" style="display:inline-block; margin-top:10px; color:#3498db;">Voir l'offre ➔</a>
    </div>
    {% endfor %}
</body>
</html>
"""

@app.route('/')
def home():
    return """
    <h1>🎯 DealHunter Web Server</h1>
    <p>Le serveur est actif !</p>
    <p>Exemple d'utilisation : <a href="/search?query=iPhone 13">Chercher iPhone 13</a></p>
    """

@app.route('/search')
def search():
    query = request.args.get('query', 'iPhone 15 128Go')
    
    # --- EXÉCUTION DE TON CODE ---
    
    # 1. Prix Neufs
    neufs, prix