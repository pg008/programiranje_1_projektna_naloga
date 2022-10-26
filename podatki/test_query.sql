SELECT razlicice.id, razlicice.ime, razlicice.opis,
modeli.ime, modeli.id, znamke.ime, znamke.id, razlicice.zacetno_leto, razlicice.koncno_leto,
razlicice.vrsta_motorja
FROM razlicice INNER JOIN
(modeli INNER JOIN znamke ON modeli.znamka_id=znamke.id)
ON razlicice.model_id=modeli.id
WHERE znamke.ime LIKE "%RENAULT%" AND
( modeli.ime LIKE "%KANGOO%" OR razlicice.ime LIKE "%KANGOO%" )
-- AND razlicice.vrsta_motorja LIKE "%diesel%"
-- AND razlicice.opis LIKE "%6MT%"
AND (2010 BETWEEN razlicice.zacetno_leto AND razlicice.koncno_leto)