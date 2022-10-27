from dataclasses import dataclass, asdict
from typing import Union
from types import NoneType
from avtomobil import ModelAvtomobila, Motor, Menjalnik, RabljenAvtomobil, TipVozila, identificiraj
import grequests, requests
import re
import math
import pandas as pd
from razno import progressbar
from enum import Enum
import copy


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
        # idji = [
        #     str(id) for
        #     ime, id in
        #     ZNAMKE_BOLHA.items()
        #     for z in self.znamke
        #     if
        #     SequenceMatcher(
        #         None,
        #         ime.replace(" ", "").upper(),
        #         z.replace(" ", "").upper()
        #     ).ratio() > 0.9
            
        # ]
        # return f"vehicleIds={'%2C'.join(idji)}"
        pass

class Iskalnik:
    def __init__(
        self, 
        filter: Filter=None,
        ime_platforme: str=None,
        url: str=None,
        osnovni_url: str=None
    ):
        self._filter = filter if filter else Filter()
        self._ime_platforme = ime_platforme
        self._url = url
        self._osnovni_url = osnovni_url
        self.najdeni_avtomobili: list[RabljenAvtomobil] = []
        self.obdelani_avtomobili = None
    
    def išči(self):
        pass

    def _obdelaj_in_poišči_v_bazi_vse_avtomobile(self):
        print("Identificiram najdene avtomobile.")
        if self.obdelani_avtomobili:
            print("Že obdelano")
            return
        self.obdelani_avtomobili = copy.deepcopy(self.najdeni_avtomobili)
        for a in progressbar(self.obdelani_avtomobili):
            self._obdelaj_najden_avtomobil(a)
            self._poišči_v_bazi(a)
    
    def _obdelaj_najden_avtomobil(self, a):
        pass

    def _poišči_v_bazi(self, a):
        zadetek: ModelAvtomobila = identificiraj(a)
        if zadetek is None: return
        a.id_modela, a.id_razlicice = zadetek.id_modela, zadetek.id_razlicice
        a.ime_znamke, a.ime_modela, a.ime_razlicice = zadetek.ime_znamke, zadetek.ime_modela, zadetek.ime_razlicice

    def tabela(self, obdelani: bool=True) -> pd.DataFrame:
        """Vrne pandas DataFrame s podatki o avtomobilih."""
        l = self.obdelani_avtomobili if obdelani else self.najdeni_avtomobili
        slovarji = [asdict(a) for a in l]
        for s in slovarji:
            for i,a in s.items():
                if isinstance(a, Enum):
                    s[i] = str(a.name)
        return pd.DataFrame.from_records(slovarji)
    
    def _odpri_oglase_in_poišči_podatke(self, povezave) -> list:
        print("Iščem podatke o avtomobilih.")
        najdeni_avtomobili = []
        for sklop_oglasov in progressbar([povezave[x:x+15] for x in range(0, len(povezave), 15)]):
            rs = (grequests.get(o) for o in sklop_oglasov)
            reqs = grequests.map(rs)
            najdeni_avtomobili.extend([self._podatki_o_avtomobilu(r.text, r.url) for r in reqs])
        return najdeni_avtomobili

class IskalnikBolha(Iskalnik):
    def __init__(self, filter: Filter=None, *args, **kwargs):
        super().__init__(
            filter,
            ime_platforme = "bolha",
            url = "https://www.bolha.com/rabljeni-avtomobili",
            osnovni_url = "https://www.bolha.com",
            *args, **kwargs)
        self._filter.__class__ = FilterBolha
    
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
            RabljenAvtomobil(
               povezava = a["povezava"],
               leto_izdelave = a["leto_izdelave"],
               naslov_oglasa=a["naslov"],
            )
            for a in avtomobili
        ]

    def _podatki_o_avtomobilu(self, html, url) -> RabljenAvtomobil:
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
            r'(?:[\s\S]*?Motor</span>[\s\S]*?'
            r'<span.*?>(?P<pogon>.*?)</span>)?'
            r'(?:[\s\S]*?Moč motorja</span>[\s\S]*?'
            r'<span.*?>(?P<moc_motorja>\d+?) <)?'
            r'(?:[\s\S]*?Delovna prostornina</span>[\s\S]*?'
            r'<span.*?>(?P<prostornina_motorja>[\d\.]+?) <)?'
            r'(?:[\s\S]*?Menjalnik</span>[\s\S]*?'
            r'<span.*?>(?P<menjalnik>.+?)</span>)?'
            r'(?:[\s\S]*?Število prestav</span>[\s\S]*?'
            r'<span.*?>(?P<stevilo_prestav>\d+?) stopenj)?'
            r'(?:[\s\S]*?Oblika karoserije: (?P<tip>[^\n]*?)\s+?</li)?'
            r'(?:[\s\S]*?Število vrat: (?P<stevilo_vrat>\d))?'
            ,
            html,
            re.MULTILINE
        )
        if p is None: return None
        
        a = RabljenAvtomobil(
            ime_znamke = p["znamka"],
            ime_modela = p["model"],
            ime_razlicice = p["razlicica"],
            tip_modela = p["tip"],
            menjalnik = p["menjalnik"],
            vrsta_motorja = p["pogon"],
            stevilo_vrat = int(p["stevilo_vrat"]) if p["stevilo_vrat"] else None,
            stevilo_prestav = int(p["stevilo_prestav"]) if p["stevilo_prestav"] else None,
            konjske_moci = None,
            kilovati = int(p["moc_motorja"]) if p["moc_motorja"] else None,
            prostornina_motorja = float(p["prostornina_motorja"]) if p["prostornina_motorja"] else None,
            povezava = url,
            naslov_oglasa = p["naslov_oglasa"],
            leto_izdelave = int(p["leto_izdelave"]) if p["leto_izdelave"] else None,
            stevilo_kilometrov = int(p["prevozeni_kilometri"]) if not p["prevozeni_kilometri"] is None else None,
            platforma = self._ime_platforme,
            cena = p["cena"],
        )
        return a

    def _obdelaj_najden_avtomobil(self, a: RabljenAvtomobil):
        super()._obdelaj_najden_avtomobil(a)
        match a.menjalnik:
            case "Mehanski menjalnik":
                a.menjalnik = Menjalnik.ROČNI
            case "Avtomatski":
                a.menjalnik = Menjalnik.AVTOMATSKI
            case "Avtomatski sekvenčni":
                a.menjalnik = Menjalnik.AVTOMATSKI
            case None:
                a.menjalnik = None
            case _:
                raise NotImplementedError(f'ne poznam menjalnika: {a.menjalnik}, {a.povezava}')
        match a.vrsta_motorja:
            case "Bencin":
                a.vrsta_motorja = Motor.BENCIN
            case "Diezel":
                a.vrsta_motorja = Motor.DIEZEL
            case "Hibrid":
                a.vrsta_motorja = Motor.HIBRID
            case None:
                a.vrsta_motorja = None
            case _:
                raise NotImplementedError(f'ne poznam motorja: {a.vrsta_motorja}, {a.povezava}')
        match a.tip_modela:
            case "limuzina":
                a.tip_modela = TipVozila.SPREMENLJIV
            case "karavan":
                a.tip_modela = TipVozila.KARAVAN
            case "enoprostorec":
                a.tip_modela = TipVozila.KOMBI
            case "coupe":
                a.tip_modela = TipVozila.COUPÉ
            case "kabriolet":
                a.tip_modela = TipVozila.SPREMENLJIV
            case "terensko vozilo – SUV":
                a.tip_modela = TipVozila.SUV
            case "kombibus":
                a.tip_modela = TipVozila.KOMBI
            case "hatchback":
                a.tip_modela = TipVozila.HATCHBACK
            case None:
                a.tip_modela = None
            case _:
                raise NotImplementedError(f'ne poznam tipa: {a.tip_modela}, {a.povezava}')
        if not a.cena is None:
            a.cena = float(a.cena.replace(".", "").replace(",", "."))

    def _število_strani(self):
        oglasov = re.search(
            r'<div class="entity-list-meta">[\S\s]+?-count">(\d+?)</strong>',
            requests.get(self._poln_url()).text
        ).group(1)
        return math.ceil(int(oglasov) / 25)
    
    def _poln_url(self, stran=1):
        return (self._url + "?"
            + self._filter.kriterijski_niz()
            + f"&page={stran}")
    
    def išči(self, podrobno=True, strani=None, identificiraj_in_obdelaj: bool=True):
        povezave = [
            self._poln_url(s+1) for s in range(self._število_strani())
        ]
        if not strani is None: povezave = povezave[:strani]
        n = []
        rs = (grequests.get(u) for u in povezave)
        print("Listam strani na bolhi:")
        for r in grequests.map(rs):
            html = r.text
            n.extend(self._poišči_avtomobile(html))
        if podrobno:
            a = self._odpri_oglase_in_poišči_podatke([self._osnovni_url + a.povezava for a in n])
            self.najdeni_avtomobili = a
        else:
            self.najdeni_avtomobili = n
        
        if identificiraj_in_obdelaj:
            self._obdelaj_in_poišči_v_bazi_vse_avtomobile()
        

    
    