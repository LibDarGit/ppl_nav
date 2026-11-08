"""Zápis časů letu po úsecích (pojíždění, vzlet, přistání, stání), mezipřistání a tisk navigačního štítku A5."""
import re

MIN = 60000


def _log(page):
    return page.evaluate("__PPL.S.log")


def _tap(page, n):
    labels = []
    for _ in range(n):
        page.locator("#bBlk").click()
        labels.append(page.locator("#bBlk").inner_text())
    return labels


def _mark_stop(page, idx):
    page.click("#bLegs")
    page.click(f"[data-ed='{idx}']")
    page.check("#ptStop")
    page.click("#nameOk")


def test_button_records_events_in_order(page):
    assert page.locator("#bBlk").inner_text() == "⏱ Pojíždění"
    labels = _tap(page, 4)
    assert labels[:3] == ["⏱ Vzlet", "⏱ Přistání", "⏱ Stání"] and re.fullmatch(r"Blok 0:0[01]", labels[3])
    c = _log(page)
    assert len(c) == 1 and c[0]["from"] == 0 and c[0]["to"] == 9 and c[0]["toName"] == "WP10"
    assert all(c[0][k] % MIN == 0 for k in ("out", "off", "on", "in"))
    assert "Stání" in page.inner_text("#banner")
    # časy přežijí obnovení stránky
    page.reload()
    page.click("#bGo")
    assert page.locator("#bBlk").inner_text() == labels[3]
    # po stání v cíli trasy klepnutí nic nepřepíše, jen otevře panel s časy
    page.locator("#bBlk").click()
    assert _log(page) == c
    assert "open" in page.get_attribute("#dLegs", "class")


def test_correct_times_and_durations_in_drawer(page):
    page.locator("#bBlk").click()
    page.click("#bLegs")
    for k, v in (("out", "09:50"), ("off", "10:02"), ("on", "11:14"), ("in", "11:21")):
        page.fill(f"#bk_{k}_0", v)
        page.locator(f"#bk_{k}_0").blur()
    summary = page.inner_text("#blkSum")
    assert "blok 1:31" in summary and "let 1:12" in summary and "přistání 1" in summary
    assert "UTC" in page.inner_text("#blkRows")
    assert page.locator("#bBlk").inner_text() == "Blok 1:31"
    assert "vzlet 10:02" in page.inner_text("#legRows")  # zapsaný vzlet je výchozí čas pro ETA
    # smazání času → tlačítko nabídne znovu tutéž událost
    page.fill("#bk_on_0", "")
    page.locator("#bk_on_0").blur()
    assert page.locator("#bBlk").inner_text() == "⏱ Přistání"
    assert "on" not in _log(page)[0]


def test_intermediate_landing_starts_new_sector(page):
    _mark_stop(page, 4)  # WP05 = plánované mezipřistání
    assert "mezipřistání" in page.inner_text("#legRows")
    page.click("#dLegs [data-close]")
    labels = _tap(page, 4)
    assert labels == ["⏱ Vzlet", "⏱ Přistání", "⏱ Stání", "⏱ Pojíždění"]  # na mezipřistání pokračuje dalším úsekem
    c = _log(page)[0]
    assert c["to"] == 4 and c["toName"] == "WP05"
    _tap(page, 2)  # pojíždění a vzlet 2. úseku
    # přistání podle GPS: nejbližší bod trasy do 3 NM (WP08), ne plánovaný cíl
    page.evaluate("() => { const P=__PPL, p=P.S.route.pts[7]; P.S.pos={lat:p.lat+0.01, lon:p.lon}; }")
    assert _tap(page, 1) == ["⏱ Stání"]
    log = _log(page)
    assert [(x["from"], x.get("to")) for x in log] == [(0, 4), (4, 7)]
    assert "WP08" in page.inner_text("#banner")
    # oprava letiště přistání v panelu Trasa
    page.click("#bLegs")
    page.select_option("#bt_1", "9")
    assert _log(page)[1]["to"] == 9
    page.click("#dLegs [data-close]")
    assert re.fullmatch(r"Blok 0:0[0-2]", _tap(page, 1)[0])  # stání v cíli trasy = konec letu
    assert "přistání 2" in page.inner_text("#blkSum")


def test_eta_after_stop_counts_from_new_takeoff(page):
    _mark_stop(page, 4)
    page.click("#dLegs [data-close]")
    _tap(page, 5)  # 1. úsek celý + pojíždění 2. úseku
    page.click("#bLegs")
    for k, v in (("off_0", "10:00"), ("off_1", "12:00")):
        page.fill(f"#bk_{k}", v)
        page.locator(f"#bk_{k}").blur()
    page.locator("#bBlk").click()  # vzlet 2. úseku už je zapsaný ručně → další je přistání
    # čas od WP05 do WP06 podle plánu (bez větru, výchozí rychlost)
    eta = page.evaluate("() => { const p=__PPL.S.route.pts; return Math.round(__PPL.gDist(p[4],p[5])/__PPL.S.cfg.tas*60); }")
    rows = page.locator("#legRows .leg")
    txt6 = rows.nth(5).inner_text()
    assert f"ETA 12:{eta:02d}" in txt6
    assert "vzlet 12:00" in rows.nth(4).inner_text()


def test_new_flight_needs_confirmation(page):
    page.locator("#bBlk").click()
    page.click("#bLegs")
    new = page.locator("#bBlkNew")
    new.click()
    assert new.inner_text() == "Opravdu smazat časy?" and _log(page)
    new.click()
    assert _log(page) == [] and page.locator("#bBlk").inner_text() == "⏱ Pojíždění"


def test_kneeboard_a5_print(page):
    page.evaluate("""() => { const c=__PPL.S.cfg; c.ws=15; c.wd=240; c.dep='10:00'; }""")
    page.locator("#bBlk").click()
    page.click("#bLegs")
    page.fill("#bk_out_0", "09:50")
    page.fill("#bk_off_0", "10:05")
    page.locator("#bk_off_0").blur()
    page.evaluate("window.print = () => { window.__printed = true; }")
    page.click("#bPrint")
    assert page.evaluate("window.__printed")
    n_pts = page.evaluate("__PPL.S.route.pts.length")
    page.emulate_media(media="print")
    assert page.locator("#app").is_hidden() and page.locator("#print").is_visible()
    rows = page.locator("#print table:first-of-type tbody tr")
    assert rows.count() == n_pts
    head = page.inner_text("#print table:first-of-type thead")
    assert all(h in head for h in ("MK°", "Kurz°M", "GS", "ETA", "ATA"))
    meta = page.inner_text("#print .meta")
    assert "vítr 240°/15 kt" in meta and "vzlet 10:05" in meta
    assert rows.nth(0).inner_text().strip().endswith("10:05")  # ETA počítané od zapsaného vzletu
    assert re.search(r"09:50\s+10:05", page.inner_text("#print .times"))
    # štítek se vejde na jednu stranu A5
    pdf = page.pdf(format="A5", prefer_css_page_size=True, print_background=True)
    assert len(re.findall(rb"/Type\s*/Page[^s]", pdf)) == 1


def test_kneeboard_with_stop_has_sectors(page):
    _mark_stop(page, 4)
    page.evaluate("""() => { __PPL.S.cfg.dep='10:00'; document.getElementById('print').innerHTML=__PPL.kneeboardHTML(); }""")
    page.emulate_media(media="print")
    secs = page.locator("#print tr.sec")
    assert secs.count() == 2
    assert secs.nth(0).inner_text().startswith("1. WP01 → WP05") and secs.nth(1).inner_text().startswith("2. WP05 → WP10")
    times = page.inner_text("#print .times")
    assert "WP01 → WP05" in times and "WP05 → WP10" in times and "Celkem" in times
    assert page.locator("#print table:first-of-type tbody tr").count() == 10 + 1 + 2  # body + odlet z mezipřistání + 2 záhlaví
    # ETA za mezipřistáním se bez zapsaného vzletu nepočítá (pilot ho dopíše)
    body = page.locator("#print table:first-of-type tbody tr")
    assert body.nth(7).inner_text().split("\t")[-2].strip() == ""
