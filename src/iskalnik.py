from dataclasses import dataclass, asdict
from typing import Union
from types import NoneType
from avtomobil import Motor, Menjalnik, NajdenAvtomobil, identificiraj
from konstante import ZNAMKE_BOLHA
import grequests, requests
import re
import math
from difflib import SequenceMatcher
import pandas as pd


class Filter:
    def __init__(
        self,
        znamke: list=None,
        modeli: list=None,
        cena: tuple=None,
        leto_izdelave: tuple=None,
        prevoženi_kilometri: tuple=None,
        motor: Motor=None,
        moč_motorja: int=None,
        menjalnik: Menjalnik=None,
        število_vrat: int=None,

    ):
        self.znamke = znamke
        self.modeli = modeli
        self.cena = cena
        self.leto_izdelave = leto_izdelave
        self.prevoženi_kilometri = prevoženi_kilometri
        self.motor = motor
        self.moč_motorja = moč_motorja
        self.menjalnik = menjalnik
        self.število_vrat = število_vrat
    
    def kriterijski_niz(self):
        raise NotImplementedError
    
    def znamke_str(self):
        raise NotImplementedError


class FilterBolha:
    def kriterijski_niz(self):
        return "typeOfTransaction=Prodam"
    
    def znamke_str(self):
        idji = [
            str(id) for
            ime, id in
            ZNAMKE_BOLHA.items()
            for z in self.znamke
            if
            SequenceMatcher(
                None,
                ime.replace(" ", "").upper(),
                z.replace(" ", "").upper()
            ).ratio() > 0.9
            
        ]
        return f"vehicleIds={'%2C'.join(idji)}"


class Iskalnik:
    def __init__(self, filter: Filter):
        self.filter = filter
        self.najdeni_avtomobili: list[NajdenAvtomobil] = []
    
    def išči(self):
        pass

class IskalnikBolha(Iskalnik):
    def __init__(self, filter: Filter, *args, **kwargs):
        super().__init__(filter, *args, **kwargs)
        self._filter = filter
        self._url = "https://www.bolha.com/rabljeni-avtomobili"
        self._osnovni_url = "https://www.bolha.com"

    def _pridobi_html(self, url, stran) -> Union[str, NoneType]:
        html = requests.get(url+f"?page={stran}").text
        if "Trenutno ni oglasov," in html:
            return False
        else: return html
    
    def _poišči_avtomobile(self, html) -> list:
        iskalnik_avtomobilov = re.compile(
            r'<li class=" EntityList-item EntityList-item--Regular[\s\S]*?<article[\S\s]*?</article>',
            re.MULTILINE
        )
        iskalnik_podatkov = re.compile(
            r'<h3 class="entity-title"><a (?:name="(?P<id>\d+?)")?.*?'
            r'href="(?P<povezava>.*?)">(?P<naslov>.*?)</a>'
            r'(:?[\S\s]*?Rabljeno vozilo.\s(?P<stevilo_kilometrov>\d+?)\skm)?'
            r'(:?[\S\s]*?Leto izdelave.\s(?P<leto_izdelave>\d+?)\.)?',
            re.MULTILINE
        )
        najdeni = iskalnik_avtomobilov.findall(html)
        avtomobili = [iskalnik_podatkov.search(a)
            for a in najdeni]
        return [
            NajdenAvtomobil(
               povezava = a["povezava"],
               leto_izdelave = a["leto_izdelave"],
               naslov_oglasa=a["naslov"],
            )
            for a in avtomobili
        ]

    def _podatki_o_avtomobilu(self, request) -> NajdenAvtomobil:
        p = re.search(
            r'<h1 class="ClassifiedDetailSummary-title"\s?>(?P<naslov_oglasa>.*?)</h1>'
            r'(?:[\s\S]*?<dd class="ClassifiedDetailSummary-priceDomestic"\s?>[\s\S]*?(?P<cena>[\d\.,]+?)[^\d\.,]*?€)?'
            r'(?:[\s\S]*?Znamka avtomobila[\s\S]*?'
            r'<span.*?>(?P<znamka>.*?)</span>)?'
            r'(?:[\s\S]*?Model avtomobila[\s\S]*?'
            r'<span.*?>(?P<model>.*?)</span>)?'
            r'(?:[\s\S]*?Tip avtomobila[\s\S]*?'
            r'<span.*?>(?P<razlicica>.*?)</span>)?'
            r'(?:[\s\S]*?Leto izdelave[\s\S]*?'
            r'<span.*?>(?P<leto_izdelave>.*?)</span>)?'
            r'(?:[\s\S]*?Prevoženi kilometri[\s\S]*?'
            r'<span.*?>(?P<prevozeni_kilometri>\d+?)\skm</span>)?'
            r'(?:[\s\S]*?Motor[\s\S]*?'
            r'<span.*?>(?P<pogon>.*?)</span>)?'
            r'(?:[\s\S]*?Moč motorja[\s\S]*?'
            r'<span.*?>(?P<moc_motorja>\d+?) <)?'
            r'(?:[\s\S]*?Delovna prostornina[\s\S]*?'
            r'<span.*?>(?P<prostornina_motorja>[\d\.]+?) <)?'
            r'(?:[\s\S]*?Menjalnik[\s\S]*?'
            r'<span.*?>(?P<menjalnik>.+?)</span>)?'
            r'(?:[\s\S]*?Število prestav[\s\S]*?'
            r'<span.*?>(?P<stevilo_prestav>\d+?) stopenj)?'
            r'(?:[\s\S]*?Oblika karoserije: (?P<tip>[^\n]*?)\s+?</li)?'
            r'(?:[\s\S]*?Število vrat: (?P<stevilo_vrat>\d))?'
            ,
            request.text,
            re.MULTILINE
        )
        if p is None: return None
        match p["menjalnik"]:
            case "Mehanski menjalnik":
                menjalnik = Menjalnik.ROČNI
            case "Avtomatski":
                menjalnik = Menjalnik.AVTOMATSKI
            case "Avtomatski sekvenčni":
                menjalnik = Menjalnik.AVTOMATSKI
            case None:
                menjalnik = None
            case _:
                raise NotImplementedError(f'ne poznam menjalnika: {p["menjalnik"]}, {request.url}')
        match p["pogon"]:
            case "Bencin":
                vrsta_motorja = Motor.BENCIN
            case "Diezel":
                vrsta_motorja = Motor.DIEZEL
            case None:
                vrsta_motorja = None
            case _:
                raise NotImplementedError(f'ne poznam motorja: {p["pogon"]}, {request.url}')
        if not p["cena"] is None: cena = float(p["cena"].replace(".", "").replace(",", "."))
        else: cena = None
        a = NajdenAvtomobil(
            ime_znamke = p["znamka"],
            ime_modela = p["model"],
            ime_razlicice = p["razlicica"],
            tip_modela = p["tip"],
            menjalnik = menjalnik,
            vrsta_motorja = vrsta_motorja,
            stevilo_vrat = int(p["stevilo_vrat"]) if not p["stevilo_vrat"] is None else None,
            stevilo_prestav = int(p["stevilo_prestav"]) if not p["stevilo_prestav"] is None else None,
            konjske_moci = None,
            kilovati = int(p["moc_motorja"]) if not p["moc_motorja"] is None else None,
            prostornina_motorja = float(p["prostornina_motorja"]) if not p["prostornina_motorja"] is None else None,
            povezava = request.url,
            naslov_oglasa = p["naslov_oglasa"],
            leto_izdelave = int(p["leto_izdelave"]) if not p["leto_izdelave"] is None else None,
            stevilo_kilometrov = int(p["prevozeni_kilometri"]) if not p["prevozeni_kilometri"] is None else None,
            cena = cena,
        )
        return a

    def _število_strani(self):
        oglasov = re.search(
            r'<div class="entity-list-meta">[\S\s]+?-count">(\d+?)</strong>',
            requests.get(self._poln_url()).text
        ).group(1)
        return math.ceil(int(oglasov) / 25)
    
    def _poln_url(self, stran=1):
        return self._url + "?" + self._filter.kriterijski_niz() + f"&page={stran}"

    def _poišči_podrobno_avtomobile(self, povezave) -> list:
        print("Iščem podatke o avtomobilih:")
        rs = (grequests.get(self._osnovni_url + u) for u in povezave)
        reqs = grequests.map(rs)
        return [self._podatki_o_avtomobilu(r) for r in reqs]
    
    def išči(self, podrobno=True, samo_prva_stran=False):
        povezave = [
            self._poln_url(s+1) for s in range(self._število_strani())
        ]
        if samo_prva_stran: povezave = povezave[:1]
        n = []
        rs = (grequests.get(u) for u in povezave)
        print("Listam strani na bolhi:")
        for r in grequests.map(rs):
            html = r.text
            n.extend(self._poišči_avtomobile(html))
        if podrobno:
            self.najdeni_avtomobili = self._poišči_podrobno_avtomobile([a.povezava for a in n])
        else:
            self.najdeni_avtomobili = n
        
        self._poišči_v_bazi()
        
    def _poišči_v_bazi(self):
        for a in self.najdeni_avtomobili:
            a.id_modela, a.id_razlicice = identificiraj(a)
    
    def tabela(self) -> pd.DataFrame:
        return pd.DataFrame.from_records([asdict(a) for a in self.najdeni_avtomobili])