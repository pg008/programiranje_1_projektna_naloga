-- SQLite
SELECT * FROM razlicice WHERE
(2018 BETWEEN razlicice.zacetno_leto
AND razlicice.koncno_leto)
AND razlicice.vrsta_motorja="diesel"
AND
razlicice.ime LIKE "%Superb%"
AND razlicice.opis LIKE "%6MT%"
AND razlicice.opis LIKE "%150 HP%"
AND razlicice.model_id IN
(SELECT modeli.id FROM modeli
WHERE modeli.znamka_id IN
(SELECT znamke.id FROM znamke
WHERE znamke.ime = "SKODA"));