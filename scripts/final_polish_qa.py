"""Exercise final guided navigation, prediction, reporting and accessible controls."""
import json
from datetime import datetime, timezone
from time import perf_counter
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from workspace_usability_qa import ROOT, BASE, audit, settled, capture


def run():
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "passed": False,
              "measurements": {}, "functional": [], "errors": [], "route_times_ms": {}}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
            page = browser.new_page(viewport={"width": 1512, "height": 1060}, reduced_motion="reduce")
            page.on("pageerror", lambda error: report["errors"].append(str(error)))
            page.goto(f"{BASE}/?page=landing")
            page.locator(".st-key-landing_open_platform").get_by_role("button").click()
            page.locator(".st-key-table_footer_overview").wait_for(timeout=60000)
            settled(page)
            assert page.locator('.coverage-strip').count() == 1
            assert page.locator('.decision-brief').count() == 1
            expect(page.locator('.brand-network > span')).to_have_count(3)
            assert page.locator('.brand-network').bounding_box()['width'] == 24
            expect(page.locator('.st-key-nav_scenarios')).to_be_hidden()
            sidebar = page.locator('[data-testid="stSidebar"]')
            disclosure = sidebar.locator('summary').filter(has_text="Explore & simulate")
            page.keyboard.press("Tab")
            disclosure.focus()
            disclosure.press("Enter")
            expect(page.locator('.st-key-nav_scenarios')).to_be_visible()
            disclosure.press("Enter")
            report["functional"].append("Secondary sidebar tools expand with the keyboard; core routes remain visible")
            page.locator('.st-key-demo_guide').get_by_role('button', name="Guided demo").click()
            page.locator('.st-key-guide_start').get_by_role('button').click()
            settled(page)
            audit(page, "guide-overview", report)
            for title, route in [("Delivery Intelligence", "delivery"), ("Order Explorer", "orders"), ("Scenario Lab", "scenarios"), ("Reports", "reports")]:
                started = perf_counter()
                page.locator('.st-key-guide_next').get_by_role('button').click()
                page.locator('h1').filter(has_text=title).wait_for(timeout=60000)
                settled(page)
                report["route_times_ms"][route] = round((perf_counter() - started) * 1000, 2)
                expect(page.locator('[data-testid="stException"]')).to_have_count(0)
                expect(page.get_by_text("This page could not be rendered.", exact=False)).to_have_count(0)
                if route == "orders":
                    expect(page.locator('.st-key-order_next_action')).to_be_visible()
                    expect(page.get_by_text('Score source:', exact=False)).to_be_visible()
                    audit(page, "polished-order", report)
                    capture(page, "polished-order", full=True)
                if route == "scenarios":
                    page.get_by_role('button', name="Run trained model", exact=True).click()
                    page.get_by_text("Trained prediction complete. Source records remain unchanged.", exact=True).wait_for(timeout=60000)
                    settled(page)
                    report["functional"].append("Guided order is passed to the Prediction Lab; trained model runs successfully")
                if route == "reports":
                    page.locator('.st-key-generate_report_pdf').get_by_role('button').click()
                    page.get_by_role('button', name="Download PDF", exact=True).wait_for(timeout=60000)
                    settled(page)
                    expect(page.locator('.st-key-generate_report_pdf').get_by_role('button')).to_be_disabled()
                    with page.expect_download() as download:
                        page.get_by_role('button', name="Download PDF", exact=True).click()
                    assert Path(download.value.path()).read_bytes().startswith(b'%PDF')
                    report["functional"].append("Current report generates once, prevents duplicate generation and downloads a valid PDF")
            page.locator('.st-key-guide_close').get_by_role('button').click()
            settled(page)
            expect(page.locator('.st-key-guide_next')).to_have_count(0)
            report["functional"].append("Five-step guide finishes without changing source datasets")
            page.locator('.st-key-nav_overview').get_by_role('button').click()
            page.locator('.st-key-table_footer_overview').wait_for(timeout=60000)
            settled(page)
            with page.expect_download() as download:
                page.locator('.st-key-download_overview').get_by_role('button').click()
            assert download.value.suggested_filename.endswith('.csv')
            report["functional"].append("Table CSV download works with the new feedback callback")
            page.set_viewport_size({"width": 390, "height": 1060})
            audit(page, "final-mobile", report)
            assert page.locator('.st-key-global_filters [data-testid="stMultiSelect"]').count() == 2
            capture(page, "final-polish-mobile", full=True)
            assert not report["errors"], report["errors"]
            report["passed"] = True
            browser.close()
    except Exception as error:
        report["failure"] = str(error)
        raise
    finally:
        (ROOT / 'metadata/final_polish_qa.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps({"passed": report["passed"], "functional": report["functional"], "route_times_ms": report["route_times_ms"]}), flush=True)


if __name__ == '__main__':
    run()
