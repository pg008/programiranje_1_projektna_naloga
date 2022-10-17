import os


MAPA_PODATKI = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..", "podatki"
    )
)

BAZA_MODELOV = os.path.join(MAPA_PODATKI, "modeli_avtomobilov.db")

URL_MODELI_AVTOMOBILOV = "https://www.autoevolution.com/cars/"