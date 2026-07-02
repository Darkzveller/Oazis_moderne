"""
Récupération des pages brutes du portail OASIS.

Ce module ne fait AUCUN parsing : il se contente d'aller chercher du HTML.
L'extraction des notes est déléguée à un futur module parser.py, afin de
garder une séparation nette entre "aller chercher la donnée" (ce fichier)
et "comprendre la donnée" (le parsing).
"""

from .auth import OasisSession
from . import config


def fetch_page_html(oasis_session: OasisSession, codepage: str) -> str:
    """
    Récupère le fragment HTML d'une "codepage" du portail
    (ex: "MYMARKS" pour les notes, "MYCURSUS" pour le cursus, etc.).

    :param oasis_session: session authentifiée (voir auth.login)
    :param codepage: identifiant de la page côté OASIS
    :return: le HTML brut renvoyé par le serveur
    """
    params = {
        "targetProject": config.TARGET_PROJECT,
        "route": config.ROUTE_LOAD_PAGE,
        "codepage": codepage,
    }
    response = oasis_session.session.get(
        config.AJAX_ENDPOINT,
        params=params,
        headers=config.DEFAULT_HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    return response.text


def fetch_marks_html(oasis_session: OasisSession) -> str:
    """Raccourci pour récupérer spécifiquement la page des notes (MYMARKS)."""
    return fetch_page_html(oasis_session, config.CODEPAGE_MARKS)
