#!/usr/bin/env bash
# Převod letecké mapy ICAO 1:500 000 do MBTiles pro PPL Nav.
#
# Použití:
#   ./icao2mbtiles.sh mapa.tif                  # georeferencovaný GeoTIFF nebo GeoPDF
#   ./icao2mbtiles.sh mapa.pdf body.txt         # PDF / PNG / JPG + vlícovací body
#   ./icao2mbtiles.sh mapa.png body.txt vystup.mbtiles
#
# body.txt = vlícovací body (průsečíky zeměpisné sítě na mapě), jeden na řádek:
#   pixel_x  pixel_y  zem_delka  zem_sirka     (desetinné stupně, # = komentář)
#   např.:   1204  873  15.0  51.0
# Stačí 4 body (lineárně), doporučeno 8–15 bodů rovnoměrně po celé mapě (polynom 2. řádu).
#
# Volitelné proměnné: DPI=254 (rozlišení při rasterizaci PDF), QUALITY=85 (JPEG kvalita)
# Požadavky: GDAL  (macOS: brew install gdal   |   Linux Mint: sudo apt install gdal-bin)
set -euo pipefail

IN="${1:?Zadej vstupní soubor (GeoTIFF/PDF/PNG/JPG)}"
GCP="${2:-}"
OUT="${3:-${IN%.*}.mbtiles}"
DPI="${DPI:-254}"
QUALITY="${QUALITY:-85}"

command -v gdalwarp >/dev/null || { echo "Chybí GDAL (brew install gdal / sudo apt install gdal-bin)"; exit 1; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
SRC="$IN"
lower="$(printf '%s' "$IN" | tr '[:upper:]' '[:lower:]')"

# 1) PDF -> raster
if [[ "$lower" == *.pdf ]]; then
  echo "• Rasterizuji PDF při ${DPI} dpi…"
  gdal_translate -q --config GDAL_PDF_DPI "$DPI" -of GTiff -co TILED=YES -co COMPRESS=DEFLATE -co BIGTIFF=IF_SAFER "$IN" "$TMP/pdf.tif"
  SRC="$TMP/pdf.tif"
fi

# 2) paleta -> RGB (aby převzorkování nedělalo artefakty)
if gdalinfo "$SRC" | grep -q "Color Table"; then
  gdal_translate -q -expand rgb -of GTiff -co TILED=YES -co BIGTIFF=IF_SAFER "$SRC" "$TMP/rgb.tif"; SRC="$TMP/rgb.tif"
fi

# 3) georeference
ORDER=()
if [[ -n "$GCP" ]]; then
  args=(); n=0
  while read -r px py lon lat _; do
    [[ -z "${px:-}" || "$px" == \#* ]] && continue
    args+=(-gcp "$px" "$py" "$lon" "$lat"); n=$((n+1))
  done < "$GCP"
  (( n >= 3 )) || { echo "Potřebuji alespoň 3 vlícovací body (mám $n)."; exit 1; }
  echo "• Vlícovací body: $n"
  gdal_translate -q -of VRT -a_srs EPSG:4326 "${args[@]}" "$SRC" "$TMP/gcp.vrt"
  SRC="$TMP/gcp.vrt"
  if (( n >= 6 )); then ORDER=(-order 2); else ORDER=(-order 1); fi
elif ! gdalinfo "$SRC" | grep -qE "Coordinate System is:|GCP Projection"; then
  echo "Soubor není georeferencovaný. Přidej soubor s vlícovacími body (viz hlavička skriptu)."; exit 1
fi

# 4) přepočet do Web Mercator
echo "• Přepočítávám do Web Mercator…"
gdalwarp -q -overwrite -t_srs EPSG:3857 -r bilinear -dstalpha "${ORDER[@]}" \
  -of GTiff -co TILED=YES -co COMPRESS=DEFLATE -co BIGTIFF=IF_SAFER "$SRC" "$TMP/merc.tif"

# 5) MBTiles + nižší úrovně přiblížení
echo "• Vytvářím MBTiles…"
rm -f "$OUT"
gdal_translate -q -of MBTILES -co TILE_FORMAT=JPEG -co QUALITY="$QUALITY" \
  -co NAME="ICAO 1:500 000" -co TYPE=baselayer "$TMP/merc.tif" "$OUT"
gdaladdo -q -r average "$OUT" 2 4 8 16

echo "✓ Hotovo: $OUT ($(du -h "$OUT" | cut -f1))"
echo "  Zkopíruj soubor do iPadu (AirDrop / Soubory) a v PPL Nav: Nastavení › Nahrát .mbtiles"
