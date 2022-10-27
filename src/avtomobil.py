from dataclasses import dataclass
import sqlite3
from konstante import BAZA_MODELOV
import re
from enum import Enum
import math
from razno import podobnost, progressbar


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
class RabljenAvtomobil(Avtomobil):
    povezava: str=None
    naslov_oglasa: str=None
    leto_izdelave: int=None
    stevilo_kilometrov: int=None
    cena: float=None
    platforma: str=None
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

def identificiraj(a: RabljenAvtomobil) -> tuple:
    """
    Poišče id te različice avtomobila v bazi."""
    try:
        id_modela = query(f'SELECT id_modela FROM modeli_platforme WHERE ime_modela_{a.platforma}="{a.ime_modela}"')[0][0]
    except IndexError:
        id_modela = None
    možne_različice = pridobi_različice(
        'WHERE znamke.id=(SELECT id_znamke FROM '
        f'znamke_platforme WHERE ime_znamke_{a.platforma}="{a.ime_znamke}")'
        +
        (f' AND modeli.id={id_modela};' if id_modela else ";")
    )
    if len(možne_različice) == 0: return None

    ujemanja = ((r, ujemanje(a, r)) for r in možne_različice)

    naj_model, naj_ujemanje = max(ujemanja, key=lambda x: x[1])
    return naj_model if naj_ujemanje > 10 else None
    

def ujemanje(n: RabljenAvtomobil, b: ModelAvtomobila):
    u_ime_modela = podobnost(n.ime_modela, b.ime_modela)/100
    u_ime_raz = podobnost(n.ime_razlicice, b.ime_razlicice)/100
    u_leto = n.leto_izdelave in range(b.zacetno_leto, b.koncno_leto+1)
    u_menjalnik = n.menjalnik == b.menjalnik
    u_vrsta_motorja = n.vrsta_motorja == b.vrsta_motorja
    try:
        u_prostornina = min(n.prostornina_motorja, b.prostornina_motorja) / max(n.prostornina_motorja, b.prostornina_motorja)
    except TypeError:
        u_prostornina = 0
    u_tip = n.tip_modela == b.tip_modela
    try:
        u_št_prestav = min(n.stevilo_prestav, b.stevilo_prestav) / max(n.stevilo_prestav, b.stevilo_prestav)
    except TypeError:
        u_št_prestav = 0
    u_št_vrat = n.stevilo_vrat == b.stevilo_vrat

    return (5*u_ime_modela+2*u_ime_raz+1*u_leto+2*u_menjalnik+3*u_vrsta_motorja
            +u_prostornina+3*u_tip+u_št_prestav+u_št_vrat)

def pridobi_različice(where_sql: str=None, id: int=None) -> list[ModelAvtomobila]:
    sql = splosen_query + " " + where_sql if id == None else splosen_query + f" WHERE razlicice.id={id}"
    razlicice = query(sql)
    m = []
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
            število_prestav, menjalnik = None, None
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
    
        m.append(ModelAvtomobila(
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
        ))
    return m