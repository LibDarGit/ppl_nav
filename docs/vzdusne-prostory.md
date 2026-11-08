# Vzdušné prostory (openAIP)

Aplikace kreslí do mapy vzdušné prostory z [openAIP](https://www.openaip.net) a varuje před vstupem
do nich. Data si stáhneš jednou na zemi s internetem, v letu pak fungují offline.

## Jednorázové nastavení

1. Zaregistruj se na [openaip.net](https://www.openaip.net) (zdarma).
2. V profilu otevři **API Clients** a založ nového klienta. Zkopíruj jeho API klíč.
3. V PPL Nav otevři **⚙︎ Nastavení**, vlož klíč do pole *API klíč openAIP* a zadej země
   (výchozí `CZ`, u letů k hranicím třeba `CZ, SK, AT, DE, PL`).
4. Klepni na **Stáhnout**. Data se uloží do iPadu, klíč zůstane jen v iPadu.

Data stahuj znovu před letem, když se mění AIP (cyklus AIRAC) nebo po delší době.
Datum stažení je vidět v Nastavení.

## Co aplikace dělá

- **Mapa:** CTR/ATZ modře s výplní, TMA/CTA modře, P červeně s výplní, R/D červeně čárkovaně,
  TRA/TSA oranžově čárkovaně, TMZ/RMZ zeleně čárkovaně. FIR, ACC/FIS sektory a airways se
  nekreslí. Prostory s dolní hranicí nad nastavenou výškou (výchozí 9500 ft) se nekreslí.
- **Klepnutí do mapy:** seznam prostorů v daném místě s výškovými hranicemi a třídou.
- **Varování:** pokud podle traťového úhlu a GS vletíš do CTR, TMA, ATZ, TMZ, RMZ, P, R, D
  nebo TRA/TSA do nastaveného počtu minut (výchozí 3), ukáže se oranžový pruh a hlas
  ohlásí „Pozor, za 2 minuty …“. Při vstupu ohlásí „Vstup do …“. Každý prostor ohlásí jednou.
  Znovu ho ohlásí až minutu poté, co přestane být v dosahu.
- **Výška:** varuje jen před prostory, do jejichž výškového rozsahu spadá výška z GPS
  (±300 ft). Mez nad terénem (AGL) neumí přepočítat na MSL: dolní mez AGL bere jako MSL a horní
  mez AGL navýší o 3000 ft. Obojí je s rezervou, aplikace tedy spíš varuje víc než míň.
  Bez výšky z GPS varuje před všemi zobrazenými prostory.

## Omezení

- Data openAIP jsou komunitní, nejsou to oficiální data ŘLP a nemusí být aktuální.
- Aplikace nezná **aktivaci** prostorů (AUP/UUP, NOTAM). U R, D, TRA/TSA a prostorů
  aktivovaných na vyžádání píše „aktivitu ověř (AUP/NOTAM)“. Aktivaci zjistíš v AisView.
- Kruhové a obloukové hranice jsou v openAIP rozložené na body. To pro VFR stačí.
- Licence dat CC BY-NC 4.0: jen nekomerční použití, s uvedením zdroje (je v Nastavení).
