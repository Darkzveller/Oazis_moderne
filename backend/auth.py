"""
Gestion de l'authentification auprès du portail OASIS.

Le site repose sur une session PHP classique : un cookie de session est posé
dès le premier GET sur la page d'accueil, puis "activé" côté serveur après un
POST de login réussi. On utilise donc une requests.Session() unique pendant
toute la durée de vie du client, pour que ce cookie soit automatiquement
réutilisé sur les appels suivants (récupération des notes, etc.).

Aucun nom de matière, de semestre ou d'année n'apparaît dans ce fichier :
il ne s'occupe que de la connexion, pas du contenu.
"""

import requests
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
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        )
    })
    session.get(f"{config.BASE_URL}/?", timeout=15)
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
    data = {
        "login": identifiant,
        "password": mot_de_passe,
        "url": "",
    }

    response = session.post(
        config.AJAX_ENDPOINT,
        params=params,
        data=data,
        headers=config.DEFAULT_HEADERS,
        timeout=15,
    )
    response.raise_for_status()

    # NOTE IMPORTANTE : dans le HAR fourni, le corps de la réponse du login
    # n'a pas été capturé (seule sa taille l'a été). On vérifie donc la
    # connexion de façon indirecte pour le moment (voir _est_authentifie).
    # Dès le premier test réel, il faudra imprimer `response.text` pour
    # voir le format exact (JSON ? "OK" ? code d'erreur ?) et fiabiliser
    # cette vérification.
    if not _est_authentifie(session):
        raise LoginError(
            "Connexion refusée : identifiant ou mot de passe incorrect "
            "(ou format de réponse du site différent de ce qui était prévu — "
            "voir le commentaire dans auth.login)."
        )

    return OasisSession(session=session, login=identifiant)


def _est_authentifie(session: requests.Session) -> bool:
    """
    Vérifie que la session est bien authentifiée en rechargeant la page
    d'accueil : si elle contient encore le formulaire de connexion, on n'est
    pas connecté.
    """
    home = session.get(f"{config.BASE_URL}/?", timeout=15)
    contenu = home.text.lower()

    indices_deconnecte = ['name="login"', 'name="password"', "se connecter"]
    return not any(indice in contenu for indice in indices_deconnecte)


def logout(oasis_session: OasisSession) -> None:
    """Déconnecte proprement la session côté serveur."""
    oasis_session.session.get(
        config.LOGOUT_ENDPOINT,
        params={"targetProject": config.TARGET_PROJECT},
        timeout=15,
    )
