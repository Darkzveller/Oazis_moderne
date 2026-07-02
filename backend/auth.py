"""
Gestion de l'authentification auprès du portail OASIS.

Le site repose sur une session PHP classique : un cookie de session est posé
dès le premier GET sur la page d'accueil, puis "activé" côté serveur après un
POST de login réussi. On utilise donc une requests.Session() unique pendant
toute la durée de vie du client, pour que ce cookie soit automatiquement
réutilisé sur les appels suivants (récupération des notes, etc.).

Le serveur renvoie un JSON lors du login, par exemple :
  {"nexturl": "#codepage=MYCALENDAR", "text": "Connexion en cours...",
   "success": true, "reload": "no"}
On s'appuie sur ce champ "success" pour valider la connexion, ce qui est
plus fiable qu'un second GET sur la page d'accueil.

Aucun nom de matière, de semestre ou d'année n'apparaît dans ce fichier :
il ne s'occupe que de la connexion, pas du contenu.
"""

import requests
import json as _json
from dataclasses import dataclass

from . import config


class LoginError(Exception):
    """Levée quand l'authentification échoue (identifiants invalides, etc.)."""


@dataclass
class OasisSession:
    """
    Enveloppe autour d'une requests.Session() authentifiée.
    On la fait transiter explicitement d'un module à l'autre plutôt que de
    garder un état global, pour que le code reste facilement testable.
    """
    session: requests.Session
    login: str


def _create_client() -> requests.Session:
    """
    Crée une session HTTP "propre" et effectue le GET initial sur la page
    d'accueil, nécessaire pour obtenir un premier cookie de session avant
    d'envoyer les identifiants.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    })
    # Ce GET est indispensable : il déclenche un Set-Cookie PHPSESSID que le
    # serveur associera ensuite au compte après le POST de login.
    session.get(f"{config.BASE_URL}/", timeout=15)
    return session


def login(identifiant: str, mot_de_passe: str) -> OasisSession:
    """
    Authentifie l'utilisateur sur le portail OASIS.

    :param identifiant: numéro étudiant / login OASIS
    :param mot_de_passe: mot de passe associé
    :raises LoginError: si le serveur ne confirme pas la connexion
    :return: un OasisSession prêt à être utilisé pour les appels suivants
    """
    session = _create_client()

    params = {
        "targetProject": config.TARGET_PROJECT,
        "route": config.ROUTE_LOGIN,
    }
    # Le champ "url" doit correspondre à la page de redirection post-login,
    # exactement comme l'envoie le navigateur (observé dans le HAR).
    data = {
        "login": identifiant,
        "password": mot_de_passe,
        "url": "codepage=MYCALENDAR",
    }
    # Ces headers reproduisent exactement ce qu'envoie Chrome (HAR).
    login_headers = {
        **config.DEFAULT_HEADERS,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": config.BASE_URL,
    }

    response = session.post(
        config.AJAX_ENDPOINT,
        params=params,
        data=data,
        headers=login_headers,
        timeout=15,
    )
    response.raise_for_status()

    # Le serveur renvoie du JSON : {"success": true/false, "text": "...", ...}
    # On s'appuie directement sur ce champ plutôt que d'effectuer un second GET.
    try:
        payload = response.json()
    except ValueError:
        raise LoginError(
            f"Réponse inattendue du serveur (non-JSON) : {response.text[:200]!r}"
        )

    if not payload.get("success", False):
        message = payload.get("text", "raison inconnue")
        raise LoginError(f"Connexion refusée par le serveur : {message}")

    return OasisSession(session=session, login=identifiant)


def logout(oasis_session: OasisSession) -> None:
    """Déconnecte proprement la session côté serveur."""
    oasis_session.session.get(
        config.LOGOUT_ENDPOINT,
        params={"targetProject": config.TARGET_PROJECT},
        timeout=15,
    )
