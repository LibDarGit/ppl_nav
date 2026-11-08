"""Společné fixtures: lokální HTTP server nad složkou app/ a stránka s načtenou testovací trasou."""
import functools
import http.server
import os
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
DATA = Path(__file__).parent / "data"
ROUTE_GPX = DATA / "aisview_route.gpx"


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def base_url():
    handler = functools.partial(_QuietHandler, directory=str(APP))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.fixture(scope="session")
def browser():
    # PW_CHROMIUM = cesta k vlastnímu Chrome/Chromium (nepovinné); jinak Chromium z `playwright install`
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("PW_CHROMIUM") or None, args=["--no-sandbox"])
        yield b
        b.close()


@pytest.fixture
def page(browser, base_url):
    """iPad na šířku, offline mapy vypnuté, hlas vypnutý, trasa načtená, navigace spuštěná."""
    ctx = browser.new_context(viewport={"width": 1180, "height": 820}, has_touch=True, accept_downloads=True)
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    # mapové dlaždice v testech nestahujeme
    pg.route("**/*.tile.opentopomap.org/**", lambda r: r.abort())
    pg.route("**/tile.openstreetmap.org/**", lambda r: r.abort())
    pg.goto(base_url + "/index.html")
    pg.evaluate("localStorage.clear()")
    pg.reload()
    pg.set_input_files("#file", str(ROUTE_GPX))
    pg.evaluate("__PPL.S.cfg.voice=false; __PPL.S.cfg.map='none'")
    pg.click("#bGo")
    pg.errors = errors
    yield pg
    assert not errors, f"JS chyby na stránce: {errors}"
    ctx.close()


# --- pomocné JS: přelet úseku s volitelným snosem ---
FLY_LEG_JS = """([from, to, frac, steps, latOffset, gsKt]) => {
  const P=__PPL, S=P.S, a=S.route.pts[from], b=S.route.pts[to]; let t=Date.now();
  S.active=to; S.directFrom=null;
  for (let k=0; k<=steps; k++){ const f=frac*k/steps;
    P.onFix(a.lat+(b.lat-a.lat)*f+latOffset*k, a.lon+(b.lon-a.lon)*f, 457, gsKt/1.943844, null, 10, t+k*2000); }
}"""
