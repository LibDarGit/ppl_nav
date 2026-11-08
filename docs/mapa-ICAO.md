# Mapa ICAO 1:500 000 v PPL Nav

PPL Nav nemá mapu ICAO přibalenou. Je to autorské dílo ŘLP ČR, s.p. a ŘLP ji nenabízí jako
veřejnou mapovou službu pro jiné aplikace. Aplikace proto načte **tvůj vlastní soubor** s mapou
ve formátu **MBTiles**. Uloží si ho do iPadu a pak funguje offline.

## 1. Získej digitální mapu ICAO

Potřebuješ mapu jako obrázek ve velkém rozlišení:
- **georeferencovaný GeoTIFF / GeoPDF** – nejjednodušší, převod je automatický,
- **PDF nebo obrázek (PNG/JPG) bez souřadnic** – potřebuješ 8–15 vlícovacích bodů (průsečíky zeměpisné sítě).

O digitální verzi se zeptej přímo ŘLP – Středisko AIM, Navigační 787, 252 61 Jeneč, aim@ans.cz.
Mapu používej v souladu s licencí, se kterou jsi ji získal.

## 2a. Převod skriptem (macOS / Linux Mint)

```bash
brew install gdal            # macOS
sudo apt install gdal-bin    # Linux Mint

chmod +x tools/icao2mbtiles.sh
./tools/icao2mbtiles.sh ICAO_CR_2026.tif                 # GeoTIFF / GeoPDF
./tools/icao2mbtiles.sh ICAO_CR_2026.pdf body.txt        # PDF/obrázek + vlícovací body
```

Formát `body.txt` (pixel x, pixel y, zeměpisná délka, šířka – desetinně):
```
# px    py     lon   lat
1204   873    15.0  51.0
3418   902    16.0  51.0
...
```
Pixelové souřadnice průsečíků zjistíš v libovolném prohlížeči obrázků (např. GIMP ukazuje
polohu kurzoru). Body rozmísti rovnoměrně po celé mapě, včetně okrajů. Při 6 a více bodech
skript použije polynom 2. řádu, který zvládne Lambertovo zobrazení mapy ICAO. V testu vyšla
odchylka 60–100 m, což odpovídá tloušťce čáry na papírové mapě.

## 2b. Alternativa v QGIS (bez příkazové řádky)

1. *Raster › Georeferencer* → otevři mapu → klikej na průsečíky sítě a zadávej lon/lat.
2. Nastavení transformace: **Polynomial 2**, cílový SRS **EPSG:3857**, převzorkování *Cubic* → spustit.
3. Načti výsledný GeoTIFF do projektu.
4. *Processing Toolbox › Generate XYZ tiles (MBTiles)*: Min zoom **7**, Max zoom **11**,
   formát JPG, kvalita 85 → uložit `.mbtiles`.

## 3. Nahrání do iPadu

1. Pošli `.mbtiles` do iPadu (AirDrop, iCloud Drive, Soubory).
2. PPL Nav → ⚙︎ Nastavení → **Mapa ICAO 1:500 000 › Nahrát .mbtiles**.
3. Mapový podklad se přepne na *Mapa ICAO (vlastní)*. Volba *Okolí mimo mapu ICAO doplnit
   OpenTopoMap* doplní okolí mimo mapu, pokud je dostupný internet.

Mapa zůstane uložená v iPadu, dokud ji nesmažeš. Aplikaci spouštěj z ikony na ploše. Safari
data webů otevíraných jen v prohlížeči po čase maže, ale aplikace přidané na plochu se to netýká.
Mapa ICAO se vydává jednou ročně a mezitím se opravuje ručními opravami v AIP AMDT (GEN 3.2).
Novou verzi nahraj stejně, starou nahradí.
