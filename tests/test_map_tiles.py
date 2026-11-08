"""Vykreslování podkladové mapy při přibližování a oddalování (kolečko myši / touchpad na počítači)."""
import struct
import zlib

import pytest


def _png(rgb):
    raw = b"".join(b"\x00" + bytes(rgb) * 256 for _ in range(256))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 256, 256, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


TILE = _png((120, 170, 90))
# podíl plochy mapy bez dlaždic (barva pozadí; dlaždice je zelená) po vykreslení snímku
BLANK_JS = """() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => {
  const cv=document.getElementById('map'), c=cv.getContext('2d'), W=cv.width, H=cv.height; let bl=0;
  for (let y=0;y<10;y++) for (let x=0;x<10;x++){ const d=c.getImageData(Math.floor((x+.5)*W/10), Math.floor((y+.5)*H/10),1,1).data;
    if (Math.abs(d[0]-226)<10 && Math.abs(d[1]-233)<10 && Math.abs(d[2]-240)<10) bl++; }  // pozadí #dfe6ee pod bílým závojem
  r(bl/100); })))"""


@pytest.fixture
def desk(browser, base_url):
    """Velký monitor počítače, podklad OpenTopoMap z napodobeného serveru."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.tiles = []
    pg.hold = set()   # zoomy, jejichž dlaždice server zatím nepošle (pomalá síť)
    pg.held = []

    def handler(route):
        z = int(route.request.url.split("/tiles/")[1].split("/")[0])
        pg.tiles.append(route.request.url)
        if z in pg.hold:
            pg.held.append(route)
            return
        route.fulfill(status=200, content_type="image/png", body=TILE)
    pg.route("**/tiles/**", handler)
    pg.goto(base_url + "/index.html")
    pg.evaluate("localStorage.clear()")
    pg.reload()
    # dlaždice ze stejného původu jako aplikace, jinak by canvas nešel číst (getImageData) kvůli CORS
    pg.evaluate("TILE_SRC.otm = (z,x,y) => '/tiles/'+z+'/'+x+'/'+y+'.png'")
    pg.set_input_files("#file", "tests/data/aisview_route.gpx")
    pg.evaluate("__PPL.S.cfg.voice=false; __PPL.S.cfg.map='otm'")
    pg.click("#bGo")
    pg.evaluate("__PPL.S.follow=false; __PPL.S.view.z=9; __PPL.requestRender()")
    pg.wait_for_function("document.getElementById('map').width>0")
    yield pg
    for r in pg.held:
        try:
            r.abort()
        except Exception:
            pass
    assert not errors, f"JS chyby na stránce: {errors}"
    ctx.close()


def _view(pg, js):
    """Změna pohledu z testu + překreslení (jako po gestu)."""
    pg.evaluate(f"() => {{ {js}; __PPL.requestRender(); }}")


def _settle(pg, limit=0.02):
    for _ in range(40):
        if pg.evaluate(BLANK_JS) <= limit:
            return True
        pg.wait_for_timeout(100)
    return False


def test_requests_only_visible_tiles(desk):
    assert _settle(desk)
    # z = 9,5 → dlaždice z13 zmenšené na 0,71: 1600×1000 px pokryje ~10×7 dlaždic, ne stovky
    n0 = len(desk.tiles)
    _view(desk, "__PPL.S.view.z=9.5")
    assert _settle(desk)
    assert len(desk.tiles) - n0 <= 90


def test_zoom_back_uses_cache_and_never_blank(desk):
    assert _settle(desk)
    box = desk.locator("#map").bounding_box()
    desk.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    blank = []
    for dy in [-100] * 6 + [100] * 6:   # tam a zpátky přes dvě úrovně dlaždic
        desk.mouse.wheel(0, dy)
        blank.append(desk.evaluate(BLANK_JS))
    assert _settle(desk)
    assert abs(desk.evaluate("__PPL.S.view.z") - 9) < 1e-6
    n0 = len(desk.tiles)
    _view(desk, "__PPL.S.view.z=9.3")  # stejné dlaždice z9 jako na začátku: musí být v mezipaměti
    assert _settle(desk) and len(desk.tiles) == n0
    assert max(blank) < 0.3, blank


def test_pending_tiles_replaced_by_coarser_level(desk):
    assert _settle(desk)
    desk.hold.add(10)                    # dlaždice z10 „ještě jdou po síti“
    _view(desk, "__PPL.S.view.z=10")
    assert desk.evaluate(BLANK_JS) < 0.02  # místo prázdné plochy zvětšený výřez z9
    desk.hold.clear()
    for r in desk.held:
        r.fulfill(status=200, content_type="image/png", body=TILE)
    desk.held.clear()
    assert _settle(desk)


def test_failed_tile_is_retried(desk):
    desk.unroute("**/tiles/**")
    desk.route("**/tiles/**", lambda r: r.abort())  # offline
    _view(desk, "__PPL.S.view={lat:40.4, lon:-3.7, z:8, rot:0}")  # místo, kde ještě nic načteného není
    desk.wait_for_timeout(300)
    assert desk.evaluate(BLANK_JS) > 0.9
    desk.unroute("**/tiles/**")
    desk.route("**/tiles/**", lambda r: r.fulfill(status=200, content_type="image/png", body=TILE))
    _view(desk, "")
    desk.wait_for_timeout(300)
    assert desk.evaluate(BLANK_JS) > 0.9  # chybná dlaždice se hned nezkouší znovu (nezahltí server)
    # po 20 s se chybné dlaždice zkusí znovu (posun hodin místo čekání)
    _view(desk, "const now=Date.now(); Date.now = () => now + 21000")
    assert _settle(desk)


def test_wheel_zooms_towards_cursor(desk):
    box = desk.locator("#map").bounding_box()
    x, y = 400, 300   # mimo střed mapy
    desk.mouse.move(box["x"] + x, box["y"] + y)
    g0 = desk.evaluate(f"__PPL.fromScreen({x}, {y})")
    for _ in range(3):
        desk.mouse.wheel(0, -150)
    desk.wait_for_timeout(100)
    assert desk.evaluate("__PPL.S.view.z") > 10
    p = desk.evaluate(f"__PPL.toScreen({g0['lat']}, {g0['lon']})")
    assert abs(p["x"] - x) < 1 and abs(p["y"] - y) < 1   # bod pod kurzorem zůstal pod kurzorem
    # při sledování polohy zůstává zoom ke středu (letadlo na kotvě)
    _view(desk, "__PPL.S.follow=true")
    c0 = desk.evaluate("[__PPL.S.view.lat, __PPL.S.view.lon]")
    desk.mouse.wheel(0, 150)
    desk.wait_for_timeout(100)
    assert desk.evaluate("[__PPL.S.view.lat, __PPL.S.view.lon]") == c0
