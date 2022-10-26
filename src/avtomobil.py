from dataclasses import dataclass
import sqlite3
from unittest.mock import NonCallableMagicMock
from konstante import BAZA_MODELOV
import re
from enum import Enum
import math
from razno import strip_accents


class Motor(Enum):
    BENCIN = 1
    DIEZEL = 2
    HIBRID = 3
    ELEKTRIČNI = 4
    PLIN = 5

class Menjalnik(Enum):
    ROČNI = 1
    AVTOMATSKI = 2

class TipVozila(Enum):
    SPREMENLJIV = 1
    COUPÉ = 2
    SUV = 3
    HATCHBACK = 4
    KARAVAN = 5
    KOMBI = 6
    TOVORNJAK = 7

@dataclass
class Avtomobil:
    ime_znamke: str=None
    ime_modela: str=None
    ime_razlicice: str=None
    tip_modela: TipVozila=None
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
razlicice.vrsta_motorja, modeli.tip
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
        + ("AT" if a.menjalnik == Menjalnik.AVTOMATSKI else "MT" if a.menjalnik == Menjalnik.ROČNI else "")
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
    sql = (
        splosen_query
        + "WHERE "
        + f'znamke.ime LIKE \"%{strip_accents(a.ime_znamke.upper().replace("-", " ")) if not a.ime_znamke == "VW" else "VOLKSWAGEN"}%\" '
        + 'AND ( '
        + " OR ".join(f'modeli.ime LIKE \"%{beseda.upper()}%\"' for beseda in a.ime_modela.split())
        + ' OR '
        + " OR ".join(f'razlicice.ime LIKE \"%{beseda.upper()}%\"' for beseda in a.ime_modela.split())
        + ' ) '
        # + f'AND (razlicice.opis LIKE \"%{prostornina}L%\" '
        # + f'OR razlicice.opis LIKE \"%{konjske} HP%\") '
        + f'AND razlicice.vrsta_motorja LIKE \"%{pogon}%\"'
        + f'AND razlicice.opis LIKE \"%{prestave}%\"'
        + f'AND ({a.leto_izdelave} BETWEEN razlicice.zacetno_leto AND razlicice.koncno_leto)'
    )
    zadetki = query(sql)
    if len(zadetki) > 1:
        return (zadetki[0][4], None)
    elif len(zadetki) == 1:
        return (zadetki[0][4], zadetki[0][0])
    else:
        return (None, None)

def pridobi_različice(where_sql: str=None, id: int=None) -> list[ModelAvtomobila]:
    sql = splosen_query + " " + where_sql if id == None else splosen_query + f" WHERE razlicice.id={id}"
    razlicice = query(sql)
    for r in razlicice:
        (id_razlicice,
        ime_razlicice,
        opis_razlicice,
        ime_modela,
        id_modela,
        ime_znamke,
        id_znamke,
        zacetno_leto,
        koncno_leto,
        vrsta_motorja,
        tip_modela) = r
        try:
            število_prestav, menjalnik = re.search(r'(\d)(AT|MT)', opis_razlicice).groups()
            število_prestav = int(število_prestav)
            menjalnik = {"AT": Menjalnik.AVTOMATSKI, "MT": Menjalnik.ROČNI}[menjalnik]
        except AttributeError:
            stevilo_prestav, menjalnik = None, None
        try:
            konjske_moči = int(re.search(r'(\d{1,3}) HP', opis_razlicice).group(1))
        except AttributeError:
            konjske_moči = None
        try:
            prostornina_motorja = float(re.search(r'(\d\.\d)L', opis_razlicice).group(1))
        except AttributeError:
            prostornina_motorja = None
        vrsta_motorja = {
            "gasoline": Motor.BENCIN,
            "diesel": Motor.DIEZEL,
            "hybrid": Motor.HIBRID,
            "%s": None,
            "natural gas": Motor.PLIN,
            "hybrid gasoline": Motor.HIBRID,
            "electric": Motor.ELEKTRIČNI,
            "mild hybrid": Motor.HIBRID,
            "mild hybrid diesel": Motor.HIBRID,
            "ethanol": Motor.PLIN,
            "hybrid diesel": Motor.DIEZEL,
            "liquefied petroleum gas (lpg)": Motor.PLIN,
            "plug-in hybrid": Motor.HIBRID
        }[vrsta_motorja]

        tip_modela = {
            "Convertible (spider/spyder, cabrio/cabriolet, "
            "drop/open/soft top)": TipVozila.SPREMENLJIV,
            "Coupé (two-door)": TipVozila.COUPÉ,
            "SUV (Sports Utility Vehicle)": TipVozila.SUV,
            "None": None,
            "Hatchback": TipVozila.HATCHBACK,
            "Wagon (station wagon, estate, combi, touring)": TipVozila.KARAVAN,
            "Van": TipVozila.KOMBI,
            "Truck": TipVozila.TOVORNJAK
        }[tip_modela]

        for o in (ime_modela, ime_razlicice, opis_razlicice):
            število_vrat = re.search(r'(\d) Doors', o)
            if not število_vrat is None:
                število_vrat = int(število_vrat.group(1))
                break
    
        yield ModelAvtomobila(
            ime_znamke,
            ime_modela,
            ime_razlicice,
            tip_modela,
            menjalnik,
            vrsta_motorja,
            število_vrat,
            število_prestav,
            konjske_moči,
            None,
            prostornina_motorja,
            id_razlicice,
            id_modela,
            opis_razlicice,
            zacetno_leto,
            koncno_leto
        )
