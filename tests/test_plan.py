"""Navigační plán: trojúhelník rychlostí, časy úseků, zadávání větru jako na iPadu."""
import math

PTS = [(50.41622, 15.83778), (50.51609, 15.22703), (50.55283, 15.55092), (50.70928, 15.42612)]


def _brg(a, b):
    f1, f2 = map(math.radians, (a[0], b[0])); dl = math.radians(b[1] - a[1])
    return (math.degrees(math.atan2(math.sin(dl) * math.cos(f2),
            math.cos(f1) * math.sin(f2) - math.sin(f1) * math.cos(f2) * math.cos(dl))) + 360) % 360


def _dist(a, b):
    f1, f2 = map(math.radians, (a[0], b[0])); dl = math.radians(b[1] - a[1])
    return 2 * 3440.065 * math.asin(math.sqrt(math.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2))


def _open_plan(page):
    page.click("#bLegs")
    page.wait_for_timeout(250)


def test_wind_triangle_matches_independent_calc(page):
    _open_plan(page)
    for sel, val in (("#pTas", "90"), ("#pWd", "270"), ("#pWs", "20"), ("#pDep", "10:00")):
        page.fill(sel, val)
        page.dispatch_event(sel, "change")
    page.click('[data-ed="1"]'); page.fill("#legSpd", "70"); page.click("#nameOk")   # vlastní rychlost 1. úseku
    plan = page.evaluate("(()=>{const q=legPlan(); return [1,2,3].map(i=>[q[i].th,q[i].gs,q[i].t])})()")
    for i, tas in zip(range(1, 4), (70, 90, 90)):
        tc = _brg(PTS[i - 1], PTS[i]); L = _dist(PTS[i - 1], PTS[i])
        wca = math.degrees(math.asin(20 / tas * math.sin(math.radians(270 - tc))))
        gs = math.sqrt(tas ** 2 + 20 ** 2 - 2 * tas * 20 * math.cos(math.radians(tc + wca - 270)))  # kosinová věta
        th, gs_app, t_app = plan[i - 1]
        assert abs(((tc + wca) % 360) - th) < 0.05
        assert abs(gs - gs_app) < 0.05
        assert abs(L / gs * 60 - t_app) < 0.01
    # ETA zaokrouhlená na minuty souhlasí se součtem
    row = page.inner_text("#legRows .leg:nth-child(2)")
    assert "Σ 0:29" in row and "ETA 10:29" in row


def test_wind_entry_by_tapping_recalculates(page):
    """Regrese: klepnutí do dalšího pole nesmí zahodit zadanou hodnotu."""
    _open_plan(page)
    summary = lambda: page.inner_text("#planSum")
    assert "1:16" in summary() and "bez větru" in summary()
    page.tap("#pWd"); page.keyboard.type("270")
    page.tap("#pWs"); page.keyboard.type("20")
    page.tap("#planSum")
    assert page.evaluate("[__PPL.S.cfg.wd, __PPL.S.cfg.ws]") == [270, 20]
    assert "1:19" in summary() and "270°/20" in summary()
    page.tap("#pWs"); page.keyboard.press("ControlOrMeta+A"); page.keyboard.type("30")   # přepočet už při psaní
    assert "1:24" in summary()
    page.tap("#pWs"); page.keyboard.press("ControlOrMeta+A"); page.keyboard.press("Backspace"); page.tap("#planSum")
    assert "bez větru" in summary() and page.input_value("#pWd") == "270"
    page.reload()
    assert page.evaluate("__PPL.S.cfg.wd") == 270
