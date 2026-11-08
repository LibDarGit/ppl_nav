"""Navigace: načtení GPX, automatické přepínání bodů, jednotky, orientace mapy."""
import math

from conftest import FLY_LEG_JS


def test_gpx_loaded(page):
    pts = page.evaluate("__PPL.S.route.pts")
    assert len(pts) == 10
    assert pts[0]["name"] == "WP01"
    assert "114.1 NM" in page.inner_text("#routeinfo")


def test_auto_sequencing_whole_route(page):
    """Simulovaný let po celé trase s kličkováním – všech 8 přepnutí bodů, konec na posledním bodu."""
    log = page.evaluate("""() => {
      const P=__PPL, S=P.S, pts=S.route.pts, log=[]; let pos={...pts[0]}, t=Date.now(), tgt=1;
      for (let i=0; i<4000 && tgt<pts.length; i++){
        const step=100/3600*2;
        if (P.gDist(pos,pts[tgt])<step) tgt++; if (tgt>=pts.length) break;
        const hd=(P.gBrg(pos,pts[tgt])+8*Math.sin(i/20)+360)%360, R=3440.065, d=step/R, th=hd*Math.PI/180,
              f1=pos.lat*Math.PI/180, l1=pos.lon*Math.PI/180,
              f2=Math.asin(Math.sin(f1)*Math.cos(d)+Math.cos(f1)*Math.sin(d)*Math.cos(th)),
              l2=l1+Math.atan2(Math.sin(th)*Math.sin(d)*Math.cos(f1),Math.cos(d)-Math.sin(f1)*Math.sin(f2));
        pos={lat:f2*180/Math.PI, lon:l2*180/Math.PI}; t+=2000;
        const before=S.active; P.onFix(pos.lat,pos.lon,457,100/1.9438,hd,10,t);
        if (S.active!==before) log.push(S.active);
      }
      return {log, final:S.active};
    }""")
    assert log["log"] == list(range(2, 10))
    assert log["final"] == 9


def test_units_km_kmh(page):
    page.evaluate(FLY_LEG_JS, [6, 7, 0.25, 8, 0.0004, 100])
    assert "kt" in page.inner_text("#vGs") and "NM" in page.inner_text("#vDist")
    page.click("#bSet")
    page.select_option("#sDu", "km")
    page.select_option("#sSu", "kmh")
    gs = page.inner_text("#vGs")
    assert "km/h" in gs and abs(int(gs.split("km/h")[0].strip().split()[0]) - 185) <= 2
    assert "km" in page.inner_text("#vDist")
    page.fill("#sTas", "180")
    page.dispatch_event("#sTas", "change")
    assert math.isclose(page.evaluate("__PPL.S.cfg.tas"), 180 / 1.852, rel_tol=1e-6)


def test_orientation_modes(page):
    page.evaluate(FLY_LEG_JS, [6, 7, 0.25, 10, 0.0006, 100])  # snos doprava → TRK ≠ DTK
    page.wait_for_timeout(800)
    rot = lambda: page.evaluate("Math.round(__PPL.S.view.rot)")
    trk = page.evaluate("Math.round(__PPL.S.trk)")
    assert page.evaluate("__PPL.S.cfg.orient") == "trk" and abs(rot() - trk) <= 1
    page.click("#bOrient"); page.wait_for_timeout(800)
    dtk = page.evaluate("Math.round(__PPL.gBrg(__PPL.S.route.pts[6], __PPL.S.route.pts[7]))")
    assert abs(rot() - dtk) <= 1 and dtk != trk
    page.click("#bOrient"); page.wait_for_timeout(800)
    assert rot() == 0
    page.reload()
    assert page.evaluate("__PPL.S.cfg.orient") == "north"
