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
from html import escape
import pickle
import time


req_head = {
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'sl-SI,sl;q=0.7',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
}

class Filter:
    def __init__(
        self,
        model: tuple=(None, None),
        cena: tuple=None,
        leto_izdelave: tuple=None,
        prevoženi_kilometri: tuple=None,
        motor: Motor=None,
        moč_motorja: int=None,
        menjalnik: Menjalnik=None,
        število_vrat: int=None,

    ):
        self._znamka, self._model = model
        self._cena = cena
        self._leto_izdelave = leto_izdelave
        self._prevoženi_kilometri = prevoženi_kilometri
        self._motor = motor
        self._moč_motorja = moč_motorja
        self._menjalnik = menjalnik
        self._število_vrat = število_vrat
    
    def _poln_url(self, stran=1):
        return (self._url + "?"
            + self.kriterijski_niz()
            + f"&{self.stran()}={stran}")
    
    def kriterijski_niz(self):
        raise NotImplementedError
    
    def znamke_str(self):
        raise NotImplementedError
    
    def stran(self):
        raise NotImplementedError
    
    def _nastavi_urlje(self):
        raise NotImplementedError

class FilterBolha(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _nastavi_urlje(self):
        self._url = "https://www.bolha.com/rabljeni-avtomobili",
        self._osnovni_url = "https://www.bolha.com",

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

    def stran(self):
        return "page"

class FilterAvtoNet(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _nastavi_urlje(self):
        self._url = "https://www.avto.net/Ads/results.asp"
        self._osnovni_url = "https://www.avto.net"
    
    @property
    def znamka(self): return escape(self._znamka) if self._znamka else ""

    @property
    def model(self): return escape(self._model) if self._model else ""

    def kriterijski_niz(self):
        return (f'znamka={self.znamka}&model={self.model}&modelID=&tip=&'
                'znamka2=&model2=&tip2=&znamka3=&model3=&tip3='
                '&cenaMin=0&cenaMax=999999&letnikMin=0&letnikMax=2090&bencin=0'
                '&starost2=999&oblika=&ccmMin=0&ccmMax=99999&mocMin=&mocMax=&kmMin=0'
                '&kmMax=9999999&kwMin=0&kwMax=999&motortakt=&motorvalji=&lokacija=0'
                '&sirina=&dolzina=&dolzinaMIN=&dolzinaMAX=&nosilnostMIN=&nosilnostMAX='
                '&lezisc=&presek=&premer=&col=&vijakov=&EToznaka=&vozilo=&airbag=&barva='
                '&barvaint=&EQ1=1000000000&EQ2=1000000000&EQ3=1000000000&EQ4='
                '100000000&EQ5=1000000000&EQ6=1000000000&EQ7=1000100020&EQ8='
                '101000000&EQ9=1000000000&KAT=1010000000&PIA=&PIAzero=&PIAOut=&PSLO='
                '&akcija=&paketgarancije=0&broker=&prikazkategorije=&kategorija='
                '&ONLvid=&ONLnak=&zaloga=10&arhiv=&presort=&tipsort='
        )

    def stran(self):
        return "stran"


class Iskalnik:
    def __init__(
        self, 
        filter: Filter=None,
        ime_platforme: str=None,
    ):
        self.nastavi_filter(filter)
        self._ime_platforme = ime_platforme
        self.najdeni_avtomobili: list[RabljenAvtomobil] = []
        self.obdelani_avtomobili = []
    
    def išči(self, podrobno=True, strani=None, identificiraj_in_obdelaj: bool=True, zamenjaj_imena=False, čakaj_med_requesti: float=0.5):
        """Poišče oglase avtomobilov in jih shrani v objekte"""
        povezave = self._urlji_iskalnih_strani()
        if not povezave: return
        if not strani is None: povezave = povezave[:strani]
        n = []
        # rs = (grequests.get(u, headers=req_head) for u in povezave)
        # for r in grequests.map(rs):
        for u in povezave:
            r = requests.get(u, headers=req_head)
            if isinstance(self, IskalnikAvtoNet):
                r.encoding = 'windows-1250'
            html = r.text
            n.extend(self._poišči_avtomobile(html))
            time.sleep(čakaj_med_requesti)
        print(f"Najdenih {len(n)} avtomobilov.")
        if len(n) == 0: return
        if podrobno:
            n = self._odpri_oglase_in_poišči_podatke([a.povezava for a in n])
        self.najdeni_avtomobili.extend(n)
        if identificiraj_in_obdelaj:
            self._obdelaj_in_poišči_v_bazi_vse_avtomobile(n, zamenjaj_imena)
              
    def shrani_iskalnik(self, datoteka: str):
        with open(datoteka, "wb") as f:
            pickle.dump(self, f)

    def naloži_iskalnik(datoteka: str):
        with open(datoteka, "rb") as f:
            return pickle.load(f)

    def _obdelaj_in_poišči_v_bazi_vse_avtomobile(self, avti: list, zamenjaj_imena=False):
        print("Identificiram najdene avtomobile.")
        avti1 = copy.deepcopy(avti)
        for a in progressbar(avti1):
            self._obdelaj_najden_avtomobil(a)
            self._poišči_v_bazi(a, zamenjaj_imena)
        self.obdelani_avtomobili.extend(avti1)
    
    def _obdelaj_najden_avtomobil(self, a):
        pass

    def _poišči_v_bazi(self, a: RabljenAvtomobil, zamenjaj_imena=False):
        zadetek: ModelAvtomobila = identificiraj(a)
        if zadetek is None:
            return
        a.id_modela, a.id_razlicice = zadetek.id_modela, zadetek.id_razlicice
        if zamenjaj_imena:
            a.ime_znamke = zadetek.ime_znamke,
            a.ime_modela = zadetek.ime_modela,
            a.ime_razlicice = zadetek.ime_razlicice
        if a.tip_modela is None: a.tip_modela = zadetek.tip_modela
        if a.vrsta_motorja is None: a.vrsta_motorja = zadetek.vrsta_motorja
        if a.ime_razlicice is None: a.ime_razlicice = zadetek.ime_razlicice
        if a.kilovati is None: a.kilovati = zadetek.kilovati
        if a.menjalnik is None: a.menjalnik = zadetek.menjalnik
        if a.konjske_moci is None: a.konjske_moci = zadetek.konjske_moci
        if a.stevilo_prestav is None: a.stevilo_prestav = zadetek.stevilo_prestav


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

    def _shrani_podatke_o_avtomobilu_v_objekt(self, p: dict, url=None):
        if p is None: return None
        a = RabljenAvtomobil(
            ime_znamke = p.get("znamka", None),
            ime_modela = p.get("model", None),
            ime_razlicice = p.get("razlicica", None),
            tip_modela = p.get("tip", None),
            menjalnik = p.get("menjalnik", None),
            vrsta_motorja = p.get("pogon", None),
            stevilo_vrat = int(p.get("stevilo_vrat", None)) if p.get("stevilo_vrat", None) else None,
            stevilo_prestav = int(p.get("stevilo_prestav", None)) if p.get("stevilo_prestav", None) else None,
            konjske_moci = int(p.get("konjske_moci", None)) if p.get("konjske_moci", None) else None,
            kilovati = int(p.get("kilovati", None)) if p.get("kilovati", None) else None,
            prostornina_motorja = float(p.get("prostornina_motorja", None)) if p.get("prostornina_motorja", None) else None,
            povezava = p.get("povezava", url),
            naslov_oglasa = p.get("naslov_oglasa", None),
            leto_izdelave = int(p.get("leto_izdelave", None)) if p.get("leto_izdelave", None) else None,
            stevilo_kilometrov = int(p.get("stevilo_kilometrov", None)) if not p.get("stevilo_kilometrov", None) is None else None,
            platforma = self._ime_platforme,
            cena = p.get("cena", None),
        )
        return a

    def _število_strani(self):
        raise NotImplementedError

    def nastavi_filter(self, f: Filter=None):
        self._filter = f if f else Filter()
        if isinstance(self, IskalnikBolha):
            self._filter.__class__ = FilterBolha
        elif isinstance(self, IskalnikAvtoNet):
            self._filter.__class__ = FilterAvtoNet
        self._filter._nastavi_urlje()

    def _urlji_iskalnih_strani(self):
        return [
            self._filter._poln_url(s+1) for s in range(self._število_strani())
        ]

class IskalnikBolha(Iskalnik):
    def __init__(self, filter: Filter=None, *args, **kwargs):
        super().__init__(
            filter,
            ime_platforme = "bolha",
            *args, **kwargs)
    
    def _poišči_avtomobile(self, html) -> list:
        iskalnik_avtomobilov = re.compile(
            r'<li class=" EntityList-item EntityList-item--Regular[\s\S]*?<article[\S\s]*?</article>',
            re.MULTILINE
        )
        iskalnik_podatkov = re.compile(
            r'<h3 class="entity-title"><a (?:name="(?P<id>\d+?)")?.*?'
            r'href="(?P<povezava>.*?)">(?P<naslov_oglasa>.*?)</a>'
            r'(:?[\S\s]*?Rabljeno vozilo.\s(?P<stevilo_kilometrov>\d+?)\skm)?'
            r'(:?[\S\s]*?Leto izdelave.\s(?P<leto_izdelave>\d+?)\.)?',
            re.MULTILINE
        )
        najdeni = iskalnik_avtomobilov.findall(html)
        return [
            self._shrani_podatke_o_avtomobilu_v_objekt(
                iskalnik_podatkov.search(a).groupdict()
            )
            for a in najdeni
        ]

    def _podatki_o_avtomobilu(self, html, url=None) -> RabljenAvtomobil:
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
            r'<span.*?>(?P<stevilo_kilometrov>\d+?)\skm</span>)?'
            r'(?:[\s\S]*?Motor</span>[\s\S]*?'
            r'<span.*?>(?P<pogon>.*?)</span>)?'
            r'(?:[\s\S]*?Moč motorja</span>[\s\S]*?'
            r'<span.*?>(?P<kilovati>\d+?) <)?'
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
        ).groupdict()
        a = self._shrani_podatke_o_avtomobilu_v_objekt(p, url)
        a.povezava = self._filter._osnovni_url + a.povezava
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
            case "Sekvenčni menjalnik":
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
            case "Električni":
                a.vrsta_motorja = Motor.ELEKTRIČNI
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
            requests.get(self._filter._poln_url()).text
        ).group(1)
        return math.ceil(int(oglasov) / 25)      

class IskalnikAvtoNet(Iskalnik):   
    def __init__(self, filter: Filter=None, *args, **kwargs):
        super().__init__(
            filter,
            ime_platforme = "avtonet", 
            *args, **kwargs)
    
    def _število_strani(self):
        html = requests.get(self._filter._poln_url(stran=1000), headers=req_head).text
        try:
            i = re.search(
                r'<li class="page-item current">[\s\S]+?>(\d{1,3})</a>',
                html,
                re.MULTILINE
            ).group(1)
        except AttributeError:
            if re.search("Na tej strani so .e prikazani vsi zadetki iskanja", html):
                return 1
            elif re.search("Ni zadetkov", html):
                return 0
            raise Exception(f"Ne najdem števila strani, {self._filter._poln_url(stran=1000)}")
        return int(i)

    def _poišči_avtomobile(self, html) -> list:
        iskalnik_avtomobilov = re.compile(
            r'<div.*?>'
            r'\s*?<a class="stretched-link" href="\.\.(?P<povezava>.*?)"></a>'
            r'[\s\S]+?<span>(?P<naslov_oglasa>.*?)</span>[\s\S]+?<table'
            r'[\s\S]+?<tr>\s+?<td class=".+?d-md-block pl-3">1.registracija</td>'
            r'\s+?<td class=".*?pl-3">(?P<leto_izdelave>\d{4})</td>'
            r'[\s\S]+?<tr>\s+?<td class=".+?d-md-block pl-3">Prevo.enih</td>'
            r'\s+?<td class=".*?pl-3">(?P<stevilo_kilometrov>\d+?) km</td>'
            r'[\s\S]+?<tr>\s+?<td class=".+?d-md-block pl-3">Gorivo</td>'
            r'\s+?<td class=".*?pl-3">(?P<pogon>.+?)</td>'
            r'(?:[\s\S]+?<tr>\s+?<td class=".+?d-md-block pl-3">Menjalnik</td>'
            r'\s+?<td class=".*?pl-3.*?">(?P<menjalnik>.+?)</td>)?[\s\S]+?<tr.*?>'
            r'\s+?<td class=".+?d-md-block pl-3">Motor</td>\s+?<td class=".*?pl-3.*?">'
            r'(?:\s+?(?P<prostornina_motorja>\d{2,4}) ccm, '
            r'(?P<kilovati>\d{2,3}) kW / (?P<konjske_moci>\d{2,3}) KM)?'
            r'[\s\S]+?<div.*?-Price-.*?">(?P<cena>[\d\.,]+?)\s',
            re.MULTILINE
        )
        avtomobili = [
            self._shrani_podatke_o_avtomobilu_v_objekt(
                a.groupdict()
            )
            for a in iskalnik_avtomobilov.finditer(html)
        ]
        for a in avtomobili:
            a.povezava = self._filter._osnovni_url + a.povezava
        return avtomobili
    
    def _obdelaj_najden_avtomobil(self, a: RabljenAvtomobil):
        super()._obdelaj_najden_avtomobil(a)
        match a.menjalnik:
            case "ročni menjalnik":
                a.menjalnik = Menjalnik.ROČNI
            case "avtomatski menjalnik":
                a.menjalnik = Menjalnik.AVTOMATSKI
            case "polavtomatski menjalnik":
                a.menjalnik = Menjalnik.AVTOMATSKI
            case None:
                a.menjalnik = None
            case _:
                raise NotImplementedError(f'ne poznam menjalnika: {a.menjalnik}, {a.povezava}')
        match a.vrsta_motorja:
            case "bencinski motor":
                a.vrsta_motorja = Motor.BENCIN
            case "diesel motor":
                a.vrsta_motorja = Motor.DIEZEL
            case "elektro pogon":
                a.vrsta_motorja = Motor.ELEKTRIČNI
            case "LPG avtoplin":
                a.vrsta_motorja = Motor.PLIN
            case None:
                a.vrsta_motorja = None
            case _:
                raise NotImplementedError(f'ne poznam motorja: {a.vrsta_motorja}, {a.povezava}')
        match a.tip_modela:
            case "limuzina":
                a.tip_modela = TipVozila.SPREMENLJIV
            case "kombilimuzina":
                a.tip_modela = TipVozila.SPREMENLJIV
            case "karavan":
                a.tip_modela = TipVozila.KARAVAN
            case "enoprostorec":
                a.tip_modela = TipVozila.KOMBI
            case "coupe":
                a.tip_modela = TipVozila.COUPÉ
            case "cabrio":
                a.tip_modela = TipVozila.SPREMENLJIV
            case "SUV":
                a.tip_modela = TipVozila.SUV
            case "pick-up":
                a.tip_modela = TipVozila.KOMBI
            case "hatchback":
                a.tip_modela = TipVozila.HATCHBACK
            case None:
                a.tip_modela = None
            case _:
                raise NotImplementedError(f'ne poznam tipa: {a.tip_modela}, {a.povezava}')
        if not a.ime_modela and not a.ime_znamke and not a.ime_razlicice:
            if (
                a.naslov_oglasa.startswith(self._filter._znamka + " "+ self._filter._model)
                or
                a.naslov_oglasa.startswith(self._filter._znamka + " - "+ self._filter._model)
            ):
                a.ime_modela = self._filter._model
                a.ime_znamke = self._filter._znamka
            pass
        a.prostornina_motorja = a.prostornina_motorja / 1000 if a.prostornina_motorja else None
        if not a.cena is None:
            a.cena = float(a.cena.replace(".", "").replace(",", "."))
        
    # iz naslova oglasa pridobi znamko in ime modela