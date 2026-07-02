"""
Parser de la page MYMARKS du portail OASIS.

Extrait les données de notes structurées à partir du HTML brut renvoyé
par l'endpoint ajax.php?route=BO\Layout\MainContent::load&codepage=MYMARKS

Retourne un dict structuré par semestres avec toutes les statistiques.
"""

import re
from bs4 import BeautifulSoup


def _parse_grade(s: str) -> float | None:
    """Convertit '12,17' -> 12.17. Retourne None si non numérique."""
    s = s.strip()
    if not s or s in ('V', '–', '-', '—', 'ABS', 'DIS'):
        return None
    # Remplacer les caracteres de substitution (encoding latin-1 mal decode)
    s = re.sub(r'[\x80-\xff]', '', s)
    try:
        return float(s.replace(',', '.'))
    except ValueError:
        return None


def _compute_semester_number(num_semester: int, year: int, all_years: list[int]) -> int:
    """
    Calcule le numéro OASIS du semestre (S5, S6, S7...).

    La convention OASIS : la première année de scolarité = S1/S2,
    la suivante = S3/S4, etc.
    num_semester=1 => impair, num_semester=2 => pair.
    
    On ordonne les années du plus ancien au plus récent pour déduire
    le rang (1ère année scolaire = rang 0).
    """
    sorted_years = sorted(set(all_years))
    year_rank = sorted_years.index(year)  # 0 = plus ancienne
    if num_semester == 1:
        return year_rank * 2 + 1
    else:
        return year_rank * 2 + 2


def parse_marks(html: str) -> dict:
    """
    Parse le HTML de la page MYMARKS.

    :param html: contenu brut renvoyé par l'endpoint OASIS
    :return: dict avec la liste des semestres et leurs modules
    """
    soup = BeautifulSoup(html, 'html.parser')

    semester_divs = soup.find_all('div', id=lambda x: x and x.startswith('Semester'))

    # Collecte d'abord toutes les années pour calculer le rang
    all_years = []
    for sd in semester_divs:
        h2 = sd.find('h2', class_='semesterTitle')
        if h2:
            try:
                all_years.append(int(h2.get('data-year', 0)))
            except (ValueError, TypeError):
                pass

    semestres = []

    for sem_div in semester_divs:
        h2 = sem_div.find('h2', class_='semesterTitle')
        if not h2:
            continue

        try:
            num_sem = int(h2.get('data-num_semester', 0))
            year = int(h2.get('data-year', 0))
        except (ValueError, TypeError):
            continue

        avg_span = h2.find('span', class_='semesterAverage')
        avg = _parse_grade(avg_span.get_text(strip=True)) if avg_span else None

        s_num = _compute_semester_number(num_sem, year, all_years)

        modules = []

        # Extraction des épreuves individuelles (TabTests)
        # Col 0 : "EPU-F5-SEE <char_latin1>Titre du module" — on extrait le sigle
        # Col 1 : Nom de l'épreuve | Col 2 : Date | Col 3 : Note | Col 4 : Coeff
        # Col 5 : Min | Col 6 : Max | Col 7 : Moyenne classe
        epreuves_by_sigle: dict = {}
        tests_tab = sem_div.find('div', id=lambda x: x and x.startswith('TabTests'))
        if tests_tab:
            table = tests_tab.find('table')
            if table:
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) < 4:
                        continue
                    texts = [c.get_text(strip=True) for c in cols]
                    # Extraire le sigle = premier token alphanumérique/tiret
                    m = re.match(r'^([A-Z0-9-]+)', texts[0])
                    sigle_key = m.group(1) if m else texts[0]
                    epreuve = {
                        "nom":        texts[1] if len(texts) > 1 else '',
                        "date":       texts[2] if len(texts) > 2 else '',
                        "note":       _parse_grade(texts[3]) if len(texts) > 3 else None,
                        "coeff":      _parse_grade(texts[4]) if len(texts) > 4 else None,
                        "min":        _parse_grade(texts[5]) if len(texts) > 5 else None,
                        "max":        _parse_grade(texts[6]) if len(texts) > 6 else None,
                        "moy_classe": _parse_grade(texts[7]) if len(texts) > 7 else None,
                    }
                    epreuves_by_sigle.setdefault(sigle_key, []).append(epreuve)

        # Onglet "Courses" = liste des modules avec note, coeff, min, max, moy
        courses_tab = sem_div.find(
            'div',
            id=lambda x: x and x.startswith('TabCourses')
        )
        if courses_tab:
            table = courses_tab.find('table')
            if table:
                rows = table.find_all('tr')
                # headers: Module | Sigle | Titre fr | Bloc | Note | Résultat EC |
                #          Commentaire EC | Coeff | Max | Min | Moy
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) < 5:
                        continue
                    texts = [c.get_text(strip=True) for c in cols]

                    nom = texts[2] if len(texts) > 2 else texts[0]
                    sigle = texts[1] if len(texts) > 1 else ''
                    note = _parse_grade(texts[4]) if len(texts) > 4 else None
                    coeff = _parse_grade(texts[7]) if len(texts) > 7 else None
                    max_note = _parse_grade(texts[8]) if len(texts) > 8 else None
                    min_note = _parse_grade(texts[9]) if len(texts) > 9 else None
                    moy_classe = _parse_grade(texts[10]) if len(texts) > 10 else None

                    modules.append({
                        "nom": nom,
                        "sigle": sigle,
                        "note": note,
                        "coeff": coeff,
                        "max": max_note,
                        "min": min_note,
                        "moy_classe": moy_classe,
                        "epreuves": epreuves_by_sigle.get(sigle, [])
                    })

        semestres.append({
            "label": f"S{s_num}",
            "num_semester": num_sem,
            "year": year,
            "year_label": f"{year}/{year + 1}",
            "average": avg,
            "modules": modules,
        })

    # Trier du plus ancien au plus récent
    semestres.sort(key=lambda s: (s["year"], s["num_semester"]))

    return {"semestres": semestres}
