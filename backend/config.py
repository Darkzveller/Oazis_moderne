"""
Configuration du portail OASIS Polytech Sorbonne.

Toutes les URLs et routes sont centralisées ici : si le site change de
domaine ou de nom de projet un jour, c'est le seul fichier à modifier.
"""

BASE_URL = "https://polytech-sorbonne.oasis.aouka.org"
TARGET_PROJECT = "oasis_polytech_sorbonne"

AJAX_ENDPOINT = f"{BASE_URL}/prod/bo/core/Router/Ajax/ajax.php"
LOGOUT_ENDPOINT = f"{BASE_URL}/core/Connection/php_logout.php"

# Routes internes utilisées par le portail OASIS (paramètre "route" de ajax.php)
ROUTE_LOGIN = r"BO\Connection\User::login"
ROUTE_LOAD_PAGE = r"BO\Layout\MainContent::load"

# "codepage" correspondant à la page "Mes notes"
CODEPAGE_MARKS = "MYMARKS"

# En-têtes observés dans le HAR : nécessaires pour que le serveur traite
# la requête comme un appel AJAX interne du portail (et non une visite directe)
DEFAULT_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/?",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

# Numéro du premier semestre affiché aujourd'hui sur le site (le plus récent).
# À ajuster une seule fois si jamais ce numéro change (nouvelle année de cycle).
NUMERO_PREMIER_SEMESTRE = 5
