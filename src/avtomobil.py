from dataclasses import dataclass
import sqlite3
from konstante import BAZA_MODELOV
import re

@dataclass
class ModelAvtomobila:
    id_razlicice: int
    ime_razlicice: str
    opis_razlicice: str
    ime_modela: str
    tip_modela: str
    ime_znamke: str
    zacetno_leto: int
    koncno_leto: int
    vrsta_motorja: str
    stevilo_prestav: int
    menjalnik: str
    konjske_moci: int
    stevilo_vrat: int

baza = sqlite3.connect(BAZA_MODELOV)

splosen_query = """\
SELECT razlicice.id, razlicice.ime, razlicice.opis,
modeli.ime, znamke.ime, razlicice.zacetno_leto, razlicice.koncno_leto,
razlicice.vrsta_motorja
FROM razlicice INNER JOIN
(modeli INNER JOIN znamke ON modeli.znamka_id=znamke.id)
ON razlicice.model_id=modeli.id
"""


def query(sql: str):
    c = baza.execute(sql)
    return c.fetchall()

def poisci_model(
    ime: str,
    menjalnik: str=None,
    stevilo_prestav: int=None,
    konjske_moci: int=None,
) -> ModelAvtomobila:
    pass

def ustvari_model(id: int) -> ModelAvtomobila:
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

ustvari_model(44)