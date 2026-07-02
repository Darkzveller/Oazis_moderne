"""
Script de diagnostic : teste la connexion et affiche les informations brutes.
Utile pour voir exactement ce que retourne le serveur.
"""
import requests
import sys

BASE_URL = "https://polytech-sorbonne.oasis.aouka.org"
AJAX_ENDPOINT = f"{BASE_URL}/prod/bo/core/Router/Ajax/ajax.php"
TARGET_PROJECT = "oasis_polytech_sorbonne"

identifiant = "21517175"
mot_de_passe = "PR0joueur2004@@"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
})

print("=== ETAPE 1: GET initial sur / ===")
r0 = session.get(f"{BASE_URL}/", timeout=15)
print(f"Status: {r0.status_code}")
print(f"Cookies apres GET /: {dict(session.cookies)}")
print(f"Set-Cookie headers: {r0.headers.get('Set-Cookie', 'AUCUN')}")
print(f"Page contient 'login': {'name=\"login\"' in r0.text.lower()}")
print()

print("=== ETAPE 2: POST login ===")
params = {
    "targetProject": TARGET_PROJECT,
    "route": r"BO\Connection\User::login",
}
data = {
    "login": identifiant,
    "password": mot_de_passe,
    "url": "codepage=MYCALENDAR",
}
headers = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": BASE_URL,
}

r1 = session.post(AJAX_ENDPOINT, params=params, data=data, headers=headers, timeout=15)
print(f"Status: {r1.status_code}")
print(f"Response headers: {dict(r1.headers)}")
print(f"Response text (brut): '{r1.text}'")
print(f"Cookies apres login: {dict(session.cookies)}")
print()

print("=== ETAPE 3: GET / pour verifier la session ===")
r2 = session.get(f"{BASE_URL}/", timeout=15, headers={"Referer": f"{BASE_URL}/"})
print(f"Status: {r2.status_code}")
print(f"Page contient 'login' form: {'name=\"login\"' in r2.text}")
print(f"Page contient 'deconnexion': {'deconnex' in r2.text.lower() or 'logout' in r2.text.lower()}")
print(f"Cookies: {dict(session.cookies)}")
# Sauvegarder la page pour inspection
with open("page_apres_login.html", "w", encoding="utf-8") as f:
    f.write(r2.text)
print("-> Page sauvegardee dans page_apres_login.html")
print()

print("=== ETAPE 4: Fetch MYMARKS ===")
r3 = session.get(
    AJAX_ENDPOINT,
    params={
        "targetProject": TARGET_PROJECT,
        "route": r"BO\Layout\MainContent::load",
        "codepage": "MYMARKS",
    },
    headers={
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BASE_URL}/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    },
    timeout=20,
)
print(f"Status: {r3.status_code}")
print(f"Response size: {len(r3.text)} chars")
print(f"Debut de la reponse: {r3.text[:300]}")
with open("mymarks.html", "w", encoding="utf-8") as f:
    f.write(r3.text)
print("-> HTML sauvegarde dans mymarks.html")
