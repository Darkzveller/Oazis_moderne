"""
Script de test manuel — à exécuter en LOCAL, depuis le dossier polytech-notes/.

Objectif : valider que la connexion fonctionne réellement contre le vrai
site, et voir à quoi ressemble la page des notes brute, avant d'écrire le
parsing.

Usage :
    pip install -r requirements.txt
    python test_login.py

Rien n'est jamais affiché ni écrit en clair : le mot de passe est saisi de
façon masquée (getpass) et n'est conservé dans aucune variable au-delà de
l'appel de connexion.
"""

import getpass

from backend import auth, scraper


def main() -> None:
    # identifiant = input("Identifiant OASIS : ").strip()
    # mot_de_passe = getpass.getpass("Mot de passe : ")
    identifiant =  "21517175"
    mot_de_passe = "PR0joueur2004@@"
    print("\n→ Tentative de connexion...")
    try:
        session = auth.login(identifiant, mot_de_passe)
        print("✅ Connexion réussie.")
    except auth.LoginError as e:
        print(f"❌ {e}")
        return

    print("\n→ Récupération de la page des notes (MYMARKS)...")
    html = scraper.fetch_marks_html(session)
    print(f"✅ {len(html)} caractères reçus.")

    with open("notes_brutes.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("→ HTML sauvegardé dans notes_brutes.html pour inspection.")

    auth.logout(session)
    print("→ Déconnexion effectuée.")


if __name__ == "__main__":
    main()
