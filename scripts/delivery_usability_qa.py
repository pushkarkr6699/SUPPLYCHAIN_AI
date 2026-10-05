"""Rendered regression checks for the 16-issue Delivery usability audit."""
import json
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, expect
from workspace_usability_qa import ROOT, BASE, audit, capture, theme, settled


def run():
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "issue_numbers": list(range(1, 17)),
              "measurements": {}, "functional": [], "errors": [], "passed": False}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
            page = browser.new_page(viewport={"width": 1512, "height": 1060}, reduced_motion="reduce")
            page.on("pageerror", lambda error: report["errors"].append(str(error)))
            page.goto(f"{BASE}/?page=landing")
            page.locator(".st-key-landing_open_platform").get_by_role("button").click()
            page.locator(".st-key-table_footer_overview").wait_for(timeout=60000)
            page.wait_for_function("""() => ![...document.querySelectorAll('[data-testid="stElementContainer"]')].some(e => {const opacity=+getComputedStyle(e).opacity; return opacity>0 && opacity<1;})""", timeout=60000)
            page.locator(".st-key-nav_delivery").get_by_role("button").click()
            page.locator(".st-key-table_footer_delivery").wait_for(timeout=60000)
            assert page.get_by_role("heading", name="Risk Distribution", exact=True).evaluate("e=>e.tagName") == "H2"
            expect(page.locator(".st-key-chip_Date")).to_have_count(0)
            expect(page.get_by_role("button", name="Investigate an order", exact=True)).to_have_count(0)
            expect(page.locator(".st-key-open_delivery").get_by_role("button")).to_have_count(1)
            assert page.get_by_text("Order Data Connected", exact=True).evaluate("e=>getComputedStyle(e).fontSize") == "12px"
            assert page.get_by_text("Daily mean scored late-delivery probability", exact=True).evaluate("e=>getComputedStyle(e).fontSize") == "14px"
            for width in [1512, 1366, 820, 390, 320]:
                page.set_viewport_size({"width": width, "height": 1060})
                audit(page, f"delivery-light-{width}", report)
                capture(page, f"delivery-light-{width}")
            page.set_viewport_size({"width": 1512, "height": 1060})
            trend = page.locator(".js-plotly-plot:visible").nth(1).evaluate("e=>({x:Array.from(e._fullData[0].x),y:Array.from(e._fullData[0].y)})")
            assert 1 < len(trend["x"]) <= 28 and len(set(trend["x"])) == len(trend["x"]), trend
            assert all(0 <= risk <= 1 for risk in trend["y"])
            report["functional"].append("H2 section headings; readable disclosure/badge/subtitle; one investigation entry; daily risk means with unique dates")
            more = page.locator('.st-key-filter_more_control [data-testid="stPopoverButton"]:visible')
            assert more.bounding_box()["width"] < 220
            more.click()
            audit(page, "delivery-advanced-filters", report)
            page.keyboard.press("Escape")
            expect(page.locator('.st-key-table_footer_delivery input[type="number"]')).to_have_count(0)
            page.locator(".st-key-next_page_delivery").get_by_role("button").click()
            expect(page.locator(".table-page-status")).to_contain_text("Page 2 of", timeout=60000)
            page.locator(".st-key-previous_page_delivery").get_by_role("button").click()
            expect(page.locator(".table-page-status")).to_contain_text("Page 1 of", timeout=60000)
            page.locator(".st-key-open_delivery").get_by_role("button").click()
            page.get_by_role("heading", name="Order Explorer", exact=True).wait_for()
            page.locator(".st-key-nav_delivery").get_by_role("button").click()
            page.locator(".st-key-table_footer_delivery").wait_for()
            report["functional"].append("Compact advanced filters; previous/next pagination; selected-order investigation opens Order Explorer")
            for tab in ["Operational Segments", "Model Diagnostics", "Risk Overview"]:
                page.get_by_role("tab", name=tab, exact=True).click()
                settled(page)
                expect(page.locator('[data-testid="stException"]')).to_have_count(0)
            report["functional"].append("Operational Segments and Model Diagnostics tabs open without application exceptions")
            for choice in ["Dark", "System"]:
                if choice == "System":
                    page.emulate_media(color_scheme="dark")
                theme(page, choice)
                for width in [1512, 390]:
                    page.set_viewport_size({"width": width, "height": 1060})
                    audit(page, f"delivery-{choice.lower()}-{width}", report)
                page.set_viewport_size({"width": 1512, "height": 1060})
            assert not report["errors"], report["errors"]
            report["passed"] = True
            browser.close()
    except Exception as error:
        report["failure"] = str(error)
        raise
    finally:
        (ROOT / "metadata/delivery_usability_qa.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"passed": report["passed"], "measurements": len(report["measurements"]), "functional_groups": len(report["functional"])}), flush=True)


if __name__ == "__main__":
    run()
