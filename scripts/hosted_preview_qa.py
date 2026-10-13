"""Read-only review of the configured public preview; no uploaded data or AI calls."""
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

expect.set_options(timeout=90000)

ROOT = Path(__file__).resolve().parents[1]
URL = "https://supplychain-ai-er9a.onrender.com/"
OUTPUT = ROOT / "tmp/screenshots/hosted-preview"
OUTPUT.mkdir(parents=True, exist_ok=True)


def main():
    report = {"passed": False, "checked_at": datetime.now(timezone.utc).isoformat(),
              "url": URL, "checks": [], "browser_errors": [], "scope": "Read-only public landing, demo entry and visible status; no uploads, credentials or provider calls."}
    try:
        with sync_playwright() as engine:
            browser = engine.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
            page.set_default_timeout(90000)
            page.on("pageerror", lambda error: report["browser_errors"].append(str(error)))
            response = page.goto(URL, wait_until="domcontentloaded", timeout=90000)
            report["http_status"] = response.status
            expect(page.locator(".hero h1")).to_be_visible()
            expect(page.get_by_test_id("stException")).to_have_count(0)
            report["checks"].append("Hosted landing rendered")
            page.screenshot(path=str(OUTPUT / "landing.png"))
            page.locator(".st-key-landing_open_platform button").click()
            expect(page.get_by_role("heading", name="Executive Command Center", exact=True)).to_be_visible()
            expect(page.get_by_test_id("stApp")).to_have_attribute("data-test-script-state", "notRunning")
            expect(page.locator('[data-stale="true"]')).to_have_count(0)
            expect(page.get_by_test_id("stPlotlyChart").first).to_be_visible()
            expect(page.get_by_test_id("stException")).to_have_count(0)
            report["checks"].append("Hosted Open platform enters dashboard")
            report["demo_data_visible"] = page.get_by_text("DEMO UI DATA", exact=False).count() > 0
            report["verified_data_visible"] = page.get_by_text("VERIFIED DATA MODE", exact=False).count() > 0
            report["unavailable_visible"] = page.get_by_text("unavailable", exact=False).count() > 0
            report["rendered_charts"] = page.get_by_test_id("stPlotlyChart").count()
            page.screenshot(path=str(OUTPUT / "dashboard.png"))
            assert report["rendered_charts"] > 0, "Hosted dashboard did not render charts."
            assert not report["browser_errors"], report["browser_errors"]
            report["passed"] = True
            browser.close()
    except Exception as error:
        report["failure"] = str(error)
        if "page" in locals():
            try:
                page.screenshot(path=str(OUTPUT / "failure.png"))
            except Exception:
                pass
        raise
    finally:
        (ROOT / "metadata/hosted_preview_qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
