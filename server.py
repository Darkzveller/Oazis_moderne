"""
Serveur Flask minimal qui :
  1. Reçoit les identifiants OASIS via POST /api/login
  2. Se connecte au portail, récupère les notes, les parse
  3. Renvoie un JSON structuré à la page HTML frontend
"""

from flask import Flask, jsonify, request, send_from_directory
import os
import sys

# Ajouter le dossier parent au path pour importer backend.*
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import auth, scraper
from backend.parser import parse_marks

app = Flask(__name__, static_folder='frontend', static_url_path='')


# ── Servir le frontend ────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')


# ── API ───────────────────────────────────────────────────────────────────────

@app.route('/api/login', methods=['POST'])
def api_login():
    """
    Body JSON : {"login": "...", "password": "..."}
    Retourne   : {"ok": true, "data": {...}} ou {"ok": false, "error": "..."}
    """
    body = request.get_json(force=True, silent=True) or {}
    identifiant = body.get('login', '').strip()
    mot_de_passe = body.get('password', '').strip()

    if not identifiant or not mot_de_passe:
        return jsonify(ok=False, error="Identifiant ou mot de passe manquant."), 400

    try:
        session = auth.login(identifiant, mot_de_passe)
    except auth.LoginError as e:
        return jsonify(ok=False, error=str(e)), 401
    except Exception as e:
        return jsonify(ok=False, error=f"Erreur réseau : {e}"), 503

    try:
        html = scraper.fetch_marks_html(session)
        data = parse_marks(html)
    except Exception as e:
        auth.logout(session)
        return jsonify(ok=False, error=f"Erreur lors de la récupération des notes : {e}"), 500

    auth.logout(session)
    return jsonify(ok=True, data=data)


if __name__ == '__main__':
    print("Serveur OASIS démarré sur http://localhost:5000")
    app.run(debug=True, port=5000)
