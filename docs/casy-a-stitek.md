# Časy letu a navigační štítek A5

## Časy letu

Tlačítko **⏱** ve spodní liště zapíše aktuální čas další události v pořadí:

1. **Pojíždění**: začátek pojíždění (off-block)
2. **Vzlet**
3. **Přistání**
4. **Stání**: konec pojíždění (on-block)

Popisek tlačítka ukazuje, co se zapíše při dalším klepnutí. Po zápisu se nahoře na chvíli ukáže
potvrzení s časem. Když jsou zapsané všechny čtyři časy, tlačítko ukazuje blokový čas a klepnutí
otevře panel Trasa.

Časy se zapisují na celé minuty, tak jak se píšou do zápisníku letů. Zůstanou uložené v iPadu
i po zavření aplikace.

V **Trasa** jsou pod plánem všechny čtyři časy. Spleteš-li se, čas tam opravíš, nebo ho smažeš
a zapíšeš znovu tlačítkem. Pod časy je blokový čas (pojíždění–stání), čas letu (vzlet–přistání)
a tytéž časy v UTC. Tlačítko **Nový let** časy smaže, potvrzuje se druhým klepnutím.

Jakmile zapíšeš vzlet, počítá plán ETA od skutečného vzletu místo plánovaného odletu.

## Mezipřistání

Let po trase s přistáním na letištích po cestě se zapisuje po úsecích (odlet → přistání):

- Po **Stání** na letišti, které není cílem trasy, nabídne tlačítko znovu **Pojíždění**: začne
  další úsek z tohoto letiště. Po stání v cíli trasy let končí.
- **Kde jsem přistál** pozná aplikace z GPS: bod trasy do 3 NM, jinak nejbližší letiště z databáze.
  Bez GPS vezme další plánované mezipřistání, jinak cíl trasy. Opravíš to v Trasa › *Přistání na*.
- **Plánovaná mezipřistání** označíš předem přes ✎ u bodu trasy (*Mezipřistání na tomto bodě*).
  V plánu je u bodu značka „mezipřistání“.
- **ETA** za mezipřistáním se počítá od vzletu z něj. Dokud ho nezapíšeš, zůstane prázdné.
- V Trasa je každý úsek zvlášť (časy, blok, let, UTC), pod nimi součet bloku, letu a počet přistání.

## Navigační štítek A5

**Trasa › Tisk štítku A5** otevře tisk (na iPadu přes AirPrint, nebo *Uložit do Souborů* jako PDF).
Na štítku je:

- název trasy, délka, celkový čas, TAS, vítr, deklinace a čas odletu nebo vzletu,
- tabulka bodů: magnetický kurz (MK), kurz s opravou na vítr (jen když je zadaný vítr), vzdálenost,
  GS, minuty úseku, součet, ETA a prázdný sloupec ATA pro ruční zápis,
- u trasy s mezipřistáním je tabulka rozdělená na úseky, každý má vlastní součet času (Σ) a ETA od
  svého vzletu,
- políčka pro pojíždění, vzlet, přistání, stání a blok/let (blokový čas a čas letu) po úsecích
  a jejich součet s počtem přistání; už zapsané časy jsou vyplněné,
- prázdná políčka pro datum, letadlo, ATIS/QNH, RWY, palivo a poznámky.

Na jednu stranu A5 se vejde zhruba 14 bodů. U delší trasy pokračuje tabulka na další straně
se záhlavím. V dialogu tisku zvol formát papíru A5, případně tisk na A4 se zmenšením.
