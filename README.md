# PPL Nav

Navigace pro VFR lety na iPadu, podobně jako SkyDemon: trasu načte z GPX souboru a vede tě po ní.
Je to webová aplikace (PWA). Spouští se z ikony na ploše iPadu a funguje i offline.

**Funkce:**
- mapa, která se pohybuje s letadlem a natáčí se podle směru letu (TRK UP / DTK UP / N UP)
- kurz k bodu, vzdálenost, čas k bodu a příletu (ETE/ETA), GS a odchylka od trati (CDI)
- automatické přepínání bodů, přímý let na bod (Direct To), hlasová upozornění česky
- navigační plán s větrem: kurz s opravou na vítr, GS, časy úseků, ETA
- zápis časů letu (pojíždění, vzlet, přistání, stání) a tisk navigačního štítku na nákoleník A5 (viz [docs/casy-a-stitek.md](docs/casy-a-stitek.md))
- podklad mapa ICAO 1:500 000 z vlastního souboru MBTiles (viz [docs/mapa-ICAO.md](docs/mapa-ICAO.md))
- vzdušné prostory z openAIP s varováním před vstupem (viz [docs/vzdusne-prostory.md](docs/vzdusne-prostory.md))
- pojmenování bodů (letiště, obce) a export trasy do GPX
- volba jednotek NM/km a kt/km/h, simulace letu pro test na zemi

> Pomocná navigační pomůcka. Není certifikovaná, nenahrazuje mapu ani plánování letu.
> Nezobrazuje NOTAM ani aktuální aktivaci prostorů (TRA/TSA, R/D) – ty ověř v AisView.

## Struktura

```
app/                 aplikace (to, co se nasazuje na web)
  index.html         celá aplikace (HTML + CSS + JS)
  sw.js              service worker – offline provoz, ukládání mapových dlaždic
  sql-wasm.*         SQLite pro import MBTiles
tests/               automatické testy (pytest + Playwright)
tools/               převod mapy ICAO do MBTiles (GDAL)
docs/                návody
.github/workflows/   testy a nasazení na GitHub Pages
.run/                spouštěcí konfigurace pro PyCharm
```

## Vývoj v PyCharmu

1. Otevři složku jako projekt a nastav Python interpreter (stačí běžné venv).
2. V terminálu PyCharmu nainstaluj závislosti pro testy:
   ```bash
   pip install -r requirements-dev.txt
   python -m playwright install chromium
   ```
3. Spouštěcí konfigurace (vpravo nahoře):
   - **Lokální server** – aplikace na http://localhost:8000. GPS na počítači nemáš, proto
     v ⚙︎ Nastavení zapni *Simulaci letu*.
   - **Testy** – spustí všechny automatické testy.
4. Commit a push (⌘K / ⌘⇧K, na Linuxu Ctrl+K / Ctrl+Shift+K) → GitHub spustí testy a když
   projdou, nasadí novou verzi. Do 1–2 minut je na webu.

## Nasazení (jednorázové nastavení)

Na GitHubu v repozitáři otevři **Settings › Pages › Build and deployment › Source: GitHub Actions**.
Aplikace pak poběží na `https://<uživatel>.github.io/ppl_nav/`.

Verzi buildu doplní GitHub Action automaticky (je vidět v ⚙︎ Nastavení dole). Číslo verze
v `sw.js` proto neměň ručně. Při spuštění s internetem si iPad novou verzi stáhne sám.
Pokud se nová verze neobjeví, zavři aplikaci a otevři ji znovu.

## iPad

1. Otevři adresu aplikace v Safari → **Sdílet › Přidat na plochu**.
2. Spouštěj z ikony. Polohu povol při prvním spuštění.
3. Potřebuješ GPS: iPad s mobilními daty (Cellular), nebo externí GPS přijímač.

## Data a licence

- Mapové podklady: © přispěvatelé OpenStreetMap, OpenTopoMap (CC-BY-SA)
- Seznam letišť: OurAirports (public domain)
- Názvy obcí: Nominatim / OpenStreetMap
- Mapa ICAO: © ŘLP ČR, s.p. – jen vlastní soubor uživatele, není součástí repozitáře
- Vzdušné prostory: [openAIP](https://www.openaip.net) (CC BY-NC 4.0) – stahuje si je uživatel s vlastním API klíčem
