-- SQLite
SELECT razlicice.id, razlicice.ime, razlicice.opis,
modeli.ime, znamke.ime, razlicice.zacetno_leto, razlicice.koncno_leto,
razlicice.vrsta_motorja
FROM razlicice INNER JOIN
(modeli INNER JOIN znamke ON modeli.znamka_id=znamke.id)
ON razlicice.model_id=modeli.id