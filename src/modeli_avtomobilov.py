import sqlite3
import os
from konstante import BAZA_MODELOV, URL_MODELI_AVTOMOBILOV
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
import re
import time

def izvedi_sql(povezava: sqlite3.Connection, sql: str):
    try:
        c = povezava.cursor()
        c.execute(sql)
    except sqlite3.Error as e:
        print(e)

def ustvari_bazo_in_tabele(p: sqlite3.Connection):
    izvedi_sql(p,
"""CREATE TABLE IF NOT EXISTS znamke (
    id integer PRIMARY KEY AUTOINCREMENT,
    ime text NOT NULL
);"""
    )

    izvedi_sql(p,
"""\
CREATE TABLE IF NOT EXISTS modeli (
    id integer PRIMARY KEY AUTOINCREMENT,
    ime text NOT NULL,
    znamka_id integer NOT NULL,
    tip text,
    FOREIGN KEY (znamka_id) REFERENCES znamke (id)
);"""
    )

def preberi_znamke_avtomobilov(url: str, brskalnik: webdriver) -> dict:
    brskalnik.get(url)
    time.sleep(3)
    brskalnik.find_element(by=By.XPATH, value='/html/body/div[1]/div/div/div/div[2]/div/button[2]').click()
    znamke = []
    for z in brskalnik.find_elements(
        By.CSS_SELECTOR, "div[itemtype='https://schema.org/Brand']"
    ):
        ime = z.find_element(By.TAG_NAME, "h5").text
        znamke.append(ime)
    return znamke

def shrani_znamke_v_tabelo(
    p: sqlite3.Connection,
    znamke: list
):
    for z in znamke:
        izvedi_sql(p,
f"""\
INSERT INTO znamke(ime) VALUES("{z}");
""")

if __name__ == "__main__":
    p = sqlite3.connect(BAZA_MODELOV)
    brskalnik = webdriver.Firefox(service=Service(GeckoDriverManager().install()))
    brskalnik.implicitly_wait(5)
    znamke = preberi_znamke_avtomobilov(URL_MODELI_AVTOMOBILOV, brskalnik)
    print(znamke)
    shrani_znamke_v_tabelo(p, znamke)
