from dataclasses import dataclass
import sqlite3
from konstante import BAZA_MODELOV
import re
from enum import Enum
import math


class Motor(Enum):
    BENCIN = 1
    DIEZEL = 2
    HIBRID = 3
    ELEKTRIČNI = 4

class Menjalnik(Enum):
    ROČNI = 1
    AVTOMATSKI = 2

@dataclass
class Avtomobil:
    ime_znamke: str=None
    ime_modela: str=None
    ime_razlicice: str=None
    tip_modela: str=None
    menjalnik: Menjalnik=None
    vrsta_motorja: Motor=None
    stevilo_vrat: int=None
    stevilo_prestav: int=None
    konjske_moci: int=None
    kilovati: int=None
    prostornina_motorja: float=None

@dataclass
class NajdenAvtomobil(Avtomobil):
    povezava: str=None
    naslov_oglasa: str=None
    leto_izdelave: int=None
    stevilo_kilometrov: int=None
    cena: float=None
    id_razlicice: int=None
    id_modela: int=None

@dataclass
class ModelAvtomobila(Avtomobil):
    id_razlicice: int=None
    id_modela: int=None
    opis_razlicice: str=None
    zacetno_leto: int=None
    koncno_leto: int=None

baza = sqlite3.connect(BAZA_MODELOV)

splosen_query = """\
SELECT razlicice.id, razlicice.ime, razlicice.opis,
modeli.ime, modeli.id, znamke.ime, znamke.id, razlicice.zacetno_leto, razlicice.koncno_leto,
razlicice.vrsta_motorja
FROM razlicice INNER JOIN
(modeli INNER JOIN znamke ON modeli.znamka_id=znamke.id)
ON razlicice.model_id=modeli.id
"""


def query(sql: str):
    c = baza.execute(sql)
    return c.fetchall()

def identificiraj(a: NajdenAvtomobil) -> tuple:
    """
    Poišče id te različice avtomobila v bazi."""
    prestave = (
        (str(a.stevilo_prestav) if not a.stevilo_prestav is None else "")
        + ("AM" if a.menjalnik == Menjalnik.AVTOMATSKI else "MT" if a.menjalnik == Menjalnik.ROČNI else "")
    )
    match a.vrsta_motorja:
        case Motor.BENCIN:
            pogon = "gasoline"
        case Motor.DIEZEL:
            pogon = "diesel"
        case Motor.HIBRID:
            pogon = "hybrid"
        case Motor.ELEKTRIČNI:
            pogon = "electric"
        case None:
            pogon = ""
    prostornina = str(math.floor(a.prostornina_motorja)) + "." + str(math.ceil(10*(a.prostornina_motorja - math.floor(a.prostornina_motorja)))) if not a.prostornina_motorja is None else ""
    konjske = str(a.konjske_moci) if not a.konjske_moci is None else str(round(a.kilovati/1.34102209)) if not a.kilovati is None else ""
    zadetki = query(
        splosen_query
        + "WHERE "
        + f'znamke.ime LIKE \"%{a.ime_znamke.upper().replace("-", " ") if not a.ime_znamke == "VW" else "VOLKSWAGEN"}%\" '
        + 'AND ( '
        + " OR ".join(f'modeli.ime LIKE \"%{beseda.upper()}%\"' for beseda in a.ime_modela.split())
        + ' ) '
        # + f'AND (razlicice.opis LIKE \"%{prostornina}L%\" '
        # + f'OR razlicice.opis LIKE \"%{konjske} HP%\") '
        + f'AND razlicice.vrsta_motorja LIKE \"%{pogon}%\"'
        + f'AND razlicice.opis LIKE \"%{prestave}%\"'
        + f'AND ({a.leto_izdelave} BETWEEN razlicice.zacetno_leto-1 AND razlicice.koncno_leto+1)'
    )
    if len(zadetki) > 1:
        return (zadetki[0][4], None)
    elif len(zadetki) == 1:
        return (zadetki[0][4], zadetki[0][0])
    else:
        return (None, None)

def pridobi_model(id: int) -> ModelAvtomobila:
    (id_razlicice,
    ime_razlicice,
    opis_razlicice,
    ime_modela,
    ime_znamke,
    zacetno_leto,
    koncno_leto,
    vrsta_motorja) = query(splosen_query + f"WHERE razlicice.id={id}")[0]
    try:
        stevilo_prestav, menjalnik = re.search(r'(\d)(AT|MT)', opis_razlicice).groups()
    except AttributeError:
        stevilo_prestav, menjalnik = None, None
    print(stevilo_prestav, menjalnik)
