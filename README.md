# Rabljeni avtomobili
## Projektna naloga
*Programiranje 1*

### Vsebina projektne naloge
Analiziral bom podatke o rabljenih avtomobilih.  
(Vir podatkov: [Avto.net](https://www.avto.net), [Bolha](https://www.bolha.com), [Mobile24](https://www.mobile24.de).)

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

### Navodila za uporabo
*Kloniramo repozitorij*

```bash
git clone https://github.com/pg008/programiranje_1_projektna_naloga.git
```

*Zajem podatkov*
Odpremo Jupyter zvezek *zajem.ipynb*, ki se nahaja v mapi *src*.

Ko poženemo prvo celico, iščemo po platformi *avto.net*. Pozor: strežnik je
nesramen. Spremenljivka ```izhodni_csv``` je pot datoteke, kamor
bodo shranjeni rezultati iskanja.

*Obdelava podatkov*
 . . .