# Rabljeni avtomobili
## Projektna naloga
*Programiranje 1*

### Vsebina projektne naloge
Analiziral bom podatke o rabljenih avtomobilih.  
(Vir podatkov: [Avto.net](https://www.avto.net), [Bolha](https://www.bolha.com))

Za vsak avtomobil bom zajel:
* ime modela
* leto proizvodnje
* število prevoženih kilometrov
* moč motorja (kW / KM)
* kapaciteta baterije (pri električnih avtomobilih)
* prostornino motorja
* vrsto pogona
* vrsto menjalnika
* število prestav
* število vrat
* tip avtomobila
* ceno

Delovne hipoteze:
* povezava med ceno in številom prevoženih kilometrov za isti model
* povezava med ceno in starostjo za isti model
* napoved cene iz podatkov o avtomobilu


### Zajem podatkov
Za zajem podatkov s strani *bolha* in *avto.net* sem napisal razred
`Iskalnik`, ki mu podamo iskalni filter (objekt razreda `Filter`).
Filter regulira parametre v http zahtevi, ki jo iskalnik pošlje
strežniku, da dobimo iste zadetke, kot če bi nastavili filtre iskanja
na spletni strani. Razred `Filter` ni dokončan, ker ga nisem potreboval
v celoti, deluje pa pri izbiri modela avtomobila na strani *avto.net*.

Najprej sem zajel [neodvisno bazo modelov avtomobilov](https://www.autoevolution.com/cars/), ki sem jo uporabil za referenco pri
identifikaciji modelov za uskladitev med stranema *avto.net* in *bolha*.
Koda za zajem s te strani se nahaja v datoteki
[src/modeli_avtomobilov.ipynb](), rezultati pa so shranjeni
v *sqlite* bazi *podatki/modeli_avtomobilov.db*.

Odpremo Jupyter zvezek *zajem.ipynb*, ki se nahaja v mapi *src*.

Ko poženemo prvo celico, iščemo po platformi *avto.net*.
    
    Pozor: strežnik je
    nesramen.

Spremenljivka ```izhodni_csv``` je pot datoteke, kamor
bodo shranjeni rezultati iskanja.

Vsi podatki se nahajajo v datoteki *rabljeni_avtomobili.csv*.

#### Obdelava podatkov
Analiza podatkov je izvedena v zvežčiču *analiza.ipynb*, klasifikacija
pa v *klasifikacija.ipynb*.
