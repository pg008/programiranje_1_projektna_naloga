SELECT razlicice.id, razlicice.ime, razlicice.opis,
modeli.ime, modeli.id, znamke.ime, znamke.id, razlicice.zacetno_leto, razlicice.koncno_leto,
razlicice.vrsta_motorja
FROM razlicice INNER JOIN
(modeli INNER JOIN znamke ON modeli.znamka_id=znamke.id)
ON razlicice.model_id=modeli.id
WHERE znamke.ime LIKE "%Land Rover%"
AND modeli.ime LIKE "%Discovery sport%";
--AND razlicice.vrsta_motorja LIKE "%diesel%"
--AND (2016 BETWEEN razlicice.zacetno_leto-1 AND razlicice.koncno_leto+1);