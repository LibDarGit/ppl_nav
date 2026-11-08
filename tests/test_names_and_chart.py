"""Pojmenování bodů (letiště + obce z OSM), export GPX, import mapy ICAO z MBTiles."""
import io
import json
import math
import sqlite3

from PIL import Image

TOWNS = {"50.516": "Libuň", "50.709": "Jablonec nad Jizerou", "50.528": "Úpice", "50.425": "Dubenec"}


def test_suggest_names_rename_and_export(page):
    def nominatim(route):
        lat = route.request.url.split("lat=")[1][:6]
        route.fulfill(status=200, content_type="application/json", headers={"Access-Control-Allow-Origin": "*"},
                      body=json.dumps({"address": {"village": TOWNS.get(lat, "Obec")}}))
    page.route("**/nominatim.openstreetmap.org/**", nominatim)
    page.click("#bLegs")
    page.click("#bSuggest")
    page.wait_for_function("!__PPL.S.route.pts.some(p=>/^WP\\d+$/.test(p.name))", timeout=20000)
    names = page.evaluate("__PPL.S.route.pts.map(p=>p.name)")
    assert names == ["LKDK Dvůr Králové nad Labem", "Libuň", "Studenec", "Jablonec nad Jizerou", "Jilemnice",
                     "LKVR Vrchlabí", "LKBR Broumov", "Úpice", "Náchod Vysokov", "Dubenec"]
    page.click('[data-ed="3"]'); page.fill("#nameIn", "PASEKY"); page.click("#nameOk")
    with page.expect_download() as dl:
        page.click("#bExport")
    gpx = open(dl.value.path(), encoding="utf-8").read()
    assert "<name>PASEKY</name>" in gpx and "<name>LKVR Vrchlabí</name>" in gpx
    page.reload()
    assert page.evaluate("__PPL.S.route.pts[3].name") == "PASEKY"


def _make_mbtiles(path, z_levels=(9, 10)):
    """Malé MBTiles pokrývající trasu (barevné dlaždice) – bez GDAL."""
    def tile_xy(lat, lon, z):
        n = 2 ** z
        x = int((lon + 180) / 360 * n)
        y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
        return x, y
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE metadata (name text, value text)")
    db.execute("CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)")
    db.executemany("INSERT INTO metadata VALUES (?,?)", [("name", "Test ICAO"), ("format", "jpg"), ("bounds", "15.0,50.3,16.5,50.8")])
    count = 0
    for z in z_levels:
        x0, y0 = tile_xy(50.8, 15.0, z); x1, y1 = tile_xy(50.3, 16.5, z)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                buf = io.BytesIO(); Image.new("RGB", (256, 256), (200, 220, 180)).save(buf, "JPEG")
                db.execute("INSERT INTO tiles VALUES (?,?,?,?)", (z, x, 2 ** z - 1 - y, buf.getvalue())); count += 1
    db.commit(); db.close()
    return count


def test_import_icao_mbtiles(page, tmp_path):
    f = tmp_path / "icao.mbtiles"
    n = _make_mbtiles(f)
    page.set_input_files("#chartFile", str(f))
    page.wait_for_function("__PPL.CHART.meta", timeout=20000)
    meta = page.evaluate("__PPL.CHART.meta")
    assert meta["count"] == n and meta["minz"] == 9 and meta["maxz"] == 10
    assert page.evaluate("__PPL.S.cfg.map") == "icao"
    page.wait_for_timeout(800)   # vykreslení dlaždic z IndexedDB
    page.reload()
    assert "Test ICAO" in page.text_content("#chartInfo")   # mapa zůstala uložená
