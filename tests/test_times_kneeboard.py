"""Zápis časů letu (pojíždění, vzlet, přistání, stání) a tisk navigačního štítku A5."""
import re

MIN = 60000


def _times(page):
    return page.evaluate("__PPL.S.blk")


def test_button_records_events_in_order(page):
    btn = page.locator("#bBlk")
    assert btn.inner_text() == "⏱ Pojíždění"
    labels = []
    for _ in range(4):
        btn.click()
        labels.append(btn.inner_text())
    assert labels[:3] == ["⏱ Vzlet", "⏱ Přistání", "⏱ Stání"] and re.fullmatch(r"Blok 0:0[01]", labels[3])
    t = _times(page)
    assert list(t) == ["out", "off", "on", "in"] and all(v % MIN == 0 for v in t.values())
    assert "Stání" in page.inner_text("#banner")
    # časy přežijí obnovení stránky
    page.reload()
    page.click("#bGo")
    assert page.locator("#bBlk").inner_text() == labels[3]
    # další klepnutí po skončení letu nic nepřepíše, jen otevře panel s časy
    page.locator("#bBlk").click()
    assert _times(page) == t
    assert "open" in page.get_attribute("#dLegs", "class")


def test_correct_times_and_durations_in_drawer(page):
    page.click("#bLegs")
    for k, v in (("out", "09:50"), ("off", "10:02"), ("on", "11:14"), ("in", "11:21")):
        page.fill(f"#bk_{k}", v)
    summary = page.inner_text("#blkSum")
    assert "blok 1:31" in summary and "let 1:12" in summary and "UTC" in summary
    assert page.locator("#bBlk").inner_text() == "Blok 1:31"
    # zapsaný vzlet je výchozí čas pro ETA v plánu
    assert "vzlet 10:02" in page.inner_text("#legRows")
    # smazání času → tlačítko nabídne znovu tutéž událost
    page.fill("#bk_on", "")
    assert page.locator("#bBlk").inner_text() == "⏱ Přistání"
    assert "on" not in _times(page)


def test_new_flight_needs_confirmation(page):
    page.locator("#bBlk").click()
    page.click("#bLegs")
    new = page.locator("#bBlkNew")
    new.click()
    assert new.inner_text() == "Opravdu smazat časy?" and _times(page)
    new.click()
    assert _times(page) == {} and page.locator("#bBlk").inner_text() == "⏱ Pojíždění"


def test_kneeboard_a5_print(page):
    page.evaluate("""() => { const c=__PPL.S.cfg; c.ws=15; c.wd=240; c.dep='10:00'; }""")
    page.click("#bLegs")
    page.fill("#bk_out", "09:50")
    page.fill("#bk_off", "10:05")
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
