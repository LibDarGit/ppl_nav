"""Vzdušné prostory z openAIP: stažení (napodobené API), vykreslení, informace po klepnutí, varování před vstupem."""
import json

from conftest import FLY_LEG_JS

KEY = "test-klic-123"


def _poly(lon0, lat0, lon1, lat1):
    return {"type": "Polygon", "coordinates": [[[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]]]}


def _lim(value, unit=1, ref=1):
    return {"value": value, "unit": unit, "referenceDatum": ref}


# CTR a TMA leží na prvním úseku trasy (WP01 → WP02), R u WP07, FIR přes celou ČR (skrytá)
ITEMS = [
    {"_id": "ctr1", "name": "CTR TESTOV", "type": 4, "icaoClass": 3, "geometry": _poly(15.50, 50.44, 15.56, 50.49),
     "lowerLimit": _lim(0, 1, 0), "upperLimit": _lim(4000)},
    {"_id": "tma1", "name": "TMA TESTOV", "type": 7, "icaoClass": 3, "geometry": _poly(15.40, 50.40, 15.66, 50.53),
     "lowerLimit": _lim(105, 6, 2), "upperLimit": _lim(125, 6, 2)},
    {"_id": "r99", "name": "LKR99 KOPEC", "type": 1, "icaoClass": 8, "onDemand": True,
     "geometry": _poly(16.30, 50.56, 16.38, 50.61), "lowerLimit": _lim(0, 1, 0), "upperLimit": _lim(65, 6, 2)},
    {"_id": "fir", "name": "PRAHA FIR", "type": 10, "icaoClass": 6, "geometry": _poly(12.0, 48.5, 19.0, 51.1),
     "lowerLimit": _lim(0, 1, 0), "upperLimit": _lim(660, 6, 2)},
]


def _mock_openaip(page, status=200):
    calls = []

    def handler(route):
        req = route.request
        calls.append({"url": req.url, "key": req.headers.get("x-openaip-api-key")})
        page_no = int(req.url.split("page=")[1].split("&")[0])
        body = {"page": page_no, "limit": 1000, "totalCount": 4, "totalPages": 2,
                "items": ITEMS[:2] if page_no == 1 else ITEMS[2:]}
        route.fulfill(status=status, content_type="application/json", headers={"Access-Control-Allow-Origin": "*"},
                      body=json.dumps(body if status == 200 else {"message": "forbidden"}))
    page.route("**/api.core.openaip.net/api/airspaces**", handler)
    return calls


def _download(page):
    calls = _mock_openaip(page)
    page.click("#bSet")
    page.fill("#aspKey", KEY)
    page.fill("#aspCountries", "cz")
    page.click("#bAspGet")
    page.wait_for_function("__PPL.ASP.meta && __PPL.ASP.list.length", timeout=10000)
    page.click("#dSet [data-close]")
    return calls


def test_download_paginated_and_kept_offline(page):
    calls = _download(page)
    assert [c["key"] for c in calls] == [KEY, KEY]
    assert "country=CZ" in calls[0]["url"] and "page=1" in calls[0]["url"] and "page=2" in calls[1]["url"]
    assert page.evaluate("__PPL.ASP.meta.count") == 4
    assert "4 prostorů · CZ" in page.inner_text("#aspInfo")
    page.reload()  # data zůstávají v IndexedDB, klíč v localStorage
    page.wait_for_function("__PPL.ASP.list.length===4", timeout=5000)
    assert page.evaluate("localStorage.getItem('pplnav.aspKey')") == json.dumps(KEY)


def test_download_rejected_key(page):
    _mock_openaip(page, status=403)
    page.click("#bSet")
    page.fill("#aspKey", "spatny")
    page.click("#bAspGet")
    page.wait_for_function("document.getElementById('banner').textContent.includes('API klíč')", timeout=5000)
    assert page.evaluate("__PPL.ASP.meta") is None
    assert "nestažená" in page.inner_text("#aspInfo")


def test_warns_before_entering_and_inside(page):
    _download(page)
    page.evaluate("""() => { window.__said=[]; __PPL.S.cfg.voice=true;
      speechSynthesis.speak = u => __said.push(u.text); }""")
    # 1500 ft, 100 kt, kousek před CTR: varování „Za … min“, jen jednou i při dalších fixech
    page.evaluate(FLY_LEG_JS, [0, 1, 0.30, 6, 0, 100])
    warn = page.locator("#aspWarn")
    assert warn.get_attribute("class") == "ahead"
    assert "CTR TESTOV" in warn.inner_text() and "GND – 4000 ft MSL" in warn.inner_text()
    assert "TMA" not in warn.inner_text()  # TMA začíná na FL105, letím 1500 ft
    page.evaluate(FLY_LEG_JS, [0, 1, 0.32, 3, 0, 100])
    said = [t for t in page.evaluate("__said") if "C T R" in t]
    assert len(said) == 1 and said[0].startswith("Pozor, za") and said[0].endswith("C T R Testov.")
    # uvnitř CTR
    page.evaluate(FLY_LEG_JS, [0, 1, 0.50, 6, 0, 100])
    assert warn.get_attribute("class") == "in"
    assert warn.inner_text().startswith("V prostoru CTR TESTOV")
    assert "Vstup do C T R Testov." in page.evaluate("__said")


def test_vertical_filter_uses_gps_altitude(page):
    _download(page)
    # 11 000 ft: pod CTR (do 4000 ft) není co hlásit, TMA (FL105–FL125) ano
    page.evaluate("""() => { const P=__PPL, S=P.S, a=S.route.pts[0], b=S.route.pts[1]; let t=Date.now();
      for (let k=0;k<=6;k++){ const f=0.3*k/6; P.onFix(a.lat+(b.lat-a.lat)*f, a.lon+(b.lon-a.lon)*f, 11000/3.28084, 100/1.943844, null, 10, t+k*2000); } }""")
    txt = page.inner_text("#aspWarn")
    assert "TMA TESTOV" in txt and "CTR" not in txt


def test_tap_shows_airspaces_at_point(page):
    _download(page)
    page.evaluate("__PPL.S.follow=false; __PPL.S.view={lat:50.465, lon:15.53, z:11, rot:0}")
    page.wait_for_timeout(100)
    box = page.locator("#map").bounding_box()
    pt = page.evaluate("__PPL.toScreen(50.465, 15.53)")
    page.mouse.click(box["x"] + pt["x"], box["y"] + pt["y"])
    pop = page.locator("#aspPop")
    assert pop.get_attribute("class") == "open"
    text = pop.inner_text()
    assert text.index("CTR TESTOV") < text.index("TMA TESTOV")  # podle dolní hranice
    assert "GND – 4000 ft MSL · třída D" in text and "FL105 – FL125" in text
    assert "FIR" not in text
    # omezený prostor s aktivací
    page.evaluate("__PPL.S.view={lat:50.585, lon:16.34, z:11, rot:30}")
    page.wait_for_timeout(100)
    pt = page.evaluate("__PPL.toScreen(50.585, 16.34)")
    page.mouse.click(box["x"] + pt["x"], box["y"] + pt["y"])
    text = pop.inner_text()
    assert "R LKR99 KOPEC" in text and "aktivace dle AUP/NOTAM" in text


def test_layer_toggle_and_formatting(page):
    _download(page)
    page.evaluate("__PPL.S.view={lat:50.465, lon:15.53, z:10, rot:0}")
    page.wait_for_timeout(100)
    page.click("#bSet")
    page.uncheck("#sAsp")
    page.click("#dSet [data-close]")
    box = page.locator("#map").bounding_box()
    pt = page.evaluate("__PPL.toScreen(50.465, 15.53)")
    page.mouse.click(box["x"] + pt["x"], box["y"] + pt["y"])
    assert page.locator("#aspPop").get_attribute("class") in ("", None)
    fmt = page.evaluate("""[__PPL.fmtLim({v:0,u:1,r:0}), __PPL.fmtLim({v:1000,u:1,r:0}),
                            __PPL.fmtLim({v:65,u:6,r:2}), __PPL.fmtLim({v:900,u:0,r:1})]""")
    assert fmt == ["GND", "1000 ft AGL", "FL65", "900 m MSL"]
