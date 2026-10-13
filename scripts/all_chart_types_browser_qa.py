"""Exercise every chart with valid fields in an isolated synthetic test app.

No model, registered dataset, user upload or external AI request is involved.
The actual shared builder/style/toolbar code is used. Geo boundaries may be
downloaded by Plotly; fixture coordinates are confined to tests.
"""
import json
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from playwright.sync_api import expect, sync_playwright
from services.visualization_service import CHART_TYPES

expect.set_options(timeout=60000)
OUTPUT = ROOT / "tmp/screenshots/all-chart-types"
OUTPUT.mkdir(parents=True, exist_ok=True)


def select(page, label, value):
    box = page.get_by_test_id("stSelectbox").filter(has=page.get_by_text(label, exact=True))
    box.get_by_role("combobox").focus()
    box.get_by_role("combobox").press("ArrowDown")
    page.get_by_role("option", name=value, exact=True).click()


def ready(page, kind):
    expect(page.get_by_role("heading", name=kind, exact=True)).to_be_visible()
    expect(page.get_by_test_id("stApp")).to_have_attribute("data-test-script-state", "notRunning")
    expect(page.locator('[data-stale="true"]')).to_have_count(0)
    expect(page.get_by_test_id("stException")).to_have_count(0)
    expected_type = {
        "Vertical bars": "bar", "Horizontal bars": "bar", "Grouped bars": "bar",
        "Stacked bars": "bar", "Pareto": "bar", "Histogram": "histogram",
        "Box plot": "box", "Violin plot": "violin", "Correlation heatmap": "heatmap",
        "Grouped heatmap": "heatmap", "Density heatmap": "histogram2d", "Treemap": "treemap",
        "Sunburst": "sunburst", "Pie": "pie", "Donut": "pie", "Scatter matrix": "splom",
        "Coordinate map": "scattergeo", "KPI indicators": "indicator", "Ordered funnel": "funnel",
    }.get(kind, "scatter")
    page.wait_for_function("""()=>{const p=document.querySelector('.js-plotly-plot');
      return p?._fullLayout&&p.data.length&&document.querySelector('.modebar-btn');}""")
    page.wait_for_function("type=>document.querySelector('.js-plotly-plot').data[0].type===type", arg=expected_type)
    page.wait_for_timeout(400)


def geometry(page):
    return page.locator('[data-testid="stPlotlyChart"]').evaluate("""e=>{
      const frame=e.getBoundingClientRect(),p=e.querySelector('.js-plotly-plot');
      return {width:frame.width,plot_width:p._fullLayout.width,
        overflow:document.documentElement.scrollWidth>innerWidth+1,
        controls:[...e.querySelectorAll('.modebar-btn')].map(b=>{const r=b.getBoundingClientRect();
          return {name:b.dataset.title,width:r.width,height:r.height,
            inside:r.left>=frame.left-1&&r.right<=frame.right+1&&r.top>=frame.top-1&&r.bottom<=frame.bottom+1};})};}""")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", choices=CHART_TYPES, help="Diagnose a suffix; full release uses the default complete list.")
    args = parser.parse_args()
    report = {"passed": False, "checked_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Actual shared chart runtime; isolated synthetic test fixture only",
              "full_chart_set": args.start is None,
              "charts": [], "browser_errors": [], "external_ai_requests": 0}
    log = (ROOT / "tmp/all-chart-fixture.log").open("w", encoding="utf-8")
    server = subprocess.Popen([str(ROOT / ".venv/Scripts/python.exe"), "-m", "streamlit", "run",
                               "tests/chart_gallery_fixture.py", "--server.address=127.0.0.1",
                               "--server.port=8502", "--server.headless=true"], cwd=ROOT,
                              stdout=log, stderr=subprocess.STDOUT,
                              creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                with urlopen("http://127.0.0.1:8502/_stcore/health", timeout=2) as response:
                    assert response.status == 200
                break
            except Exception:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.2)
        with sync_playwright() as engine:
            browser = engine.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1100}, reduced_motion="reduce")
            page.set_default_timeout(60000)
            current = {"type": "initial load"}
            def record_error(error):
                item = {"chart": current["type"], "message": str(error), "stack": error.stack}
                report["browser_errors"].append(item)
                print("Browser error: " + json.dumps(item), flush=True)
            page.on("pageerror", record_error)
            page.goto("http://127.0.0.1:8502")
            for index, kind in enumerate(CHART_TYPES):
                if args.start and index < CHART_TYPES.index(args.start):
                    continue
                current["type"] = kind
                if index:
                    select(page, "Chart type", kind)
                ready(page, kind)
                expect(page.get_by_text("Exact grouped record count: 72", exact=True)).to_be_visible()
                chart = page.get_by_test_id("stPlotlyChart")
                chart.scroll_into_view_if_needed()
                desktop = geometry(page)
                assert not desktop["overflow"] and desktop["plot_width"] <= desktop["width"] + 1, kind
                assert desktop["controls"] and all(c["inside"] and c["width"] >= 44 and c["height"] >= 44 for c in desktop["controls"]), kind
                plot = chart.locator(".js-plotly-plot")
                actions = []
                for name, mode in [("Pan", "pan"), ("Zoom", "zoom")]:
                    control = chart.locator('.modebar-btn[data-title="' + name + '"]')
                    if control.count():
                        control.click()
                        assert plot.evaluate("e=>e._fullLayout.dragmode") == mode, kind
                        actions.append(name)
                before = plot.evaluate("e=>e._fullLayout.yaxis?.range")
                for name in ["Zoom in", "Zoom out", "Autoscale", "Reset axes"]:
                    control = chart.locator('.modebar-btn[data-title="' + name + '"]')
                    if control.count():
                        control.click()
                        page.wait_for_timeout(80)
                        actions.append(name)
                if before:
                    after = plot.evaluate("e=>e._fullLayout.yaxis.range")
                    assert all(abs(a - b) < max(1, abs(b)) * 1e-6 for a, b in zip(after, before)), (kind, before, after)
                expand = chart.locator('.modebar-btn[data-title="Fullscreen"]')
                assert expand.count() == 1, kind
                original_width = chart.bounding_box()["width"]
                expand.click()
                page.wait_for_function("width=>document.querySelector('[data-testid=stPlotlyChart]').getBoundingClientRect().width>width+50", arg=original_width)
                page.keyboard.press("Escape")
                page.wait_for_timeout(200)
                if chart.bounding_box()["width"] > original_width + 50:
                    chart.locator('.modebar-btn').last.click()
                page.wait_for_function("width=>document.querySelector('[data-testid=stPlotlyChart]').getBoundingClientRect().width<=width+2", arg=original_width)
                actions.append("Fullscreen entry/exit")
                with page.expect_download(timeout=60000) as downloaded:
                    chart.locator('.modebar-btn[data-title="Download plot as a PNG"]').click()
                payload = Path(downloaded.value.path()).read_bytes()
                assert payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) > 1000, kind
                actions.append("Valid PNG export")
                select(page, "Theme", "Dark")
                ready(page, kind)
                page.set_viewport_size({"width": 320, "height": 1100})
                page.wait_for_timeout(350)
                page.wait_for_function("""()=>{const e=document.querySelector('[data-testid=stPlotlyChart]');
                  return e.querySelector('.js-plotly-plot')._fullLayout.width<=e.getBoundingClientRect().width+1;}""")
                narrow = geometry(page)
                assert not narrow["overflow"] and all(c["inside"] for c in narrow["controls"]), kind
                if kind == 'KPI indicators':
                    bounds = chart.locator('.numbers').evaluate_all("es=>es.map(e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom};})")
                    assert len(bounds) == 3
                    for first, second in zip(bounds, bounds[1:]):
                        assert first['bottom'] < second['top'], 'KPI values overlap on mobile'
                    assert all(16 <= b['left'] < b['right'] <= 304 for b in bounds), 'KPI value clips on mobile'
                    narrow['kpi_values_separated'] = True
                page.screenshot(path=str(OUTPUT / (str(index + 1) + "-dark-320.png")))
                page.set_viewport_size({"width": 1440, "height": 1100})
                select(page, "Theme", "Light")
                ready(page, kind)
                page.screenshot(path=str(OUTPUT / (str(index + 1) + "-light-desktop.png")))
                report["charts"].append({"type": kind, "passed": True, "desktop": desktop,
                                         "dark_320": narrow, "actions": actions})
                assert not report["browser_errors"], report["browser_errors"]
                print(kind + ": passed", flush=True)
            assert not report["browser_errors"], report["browser_errors"]
            report["passed"] = True
            browser.close()
    except Exception as error:
        report["failure"] = str(error)
        raise
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        (ROOT / "metadata/all_chart_types_browser_qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
