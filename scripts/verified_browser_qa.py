"""Browser QA in a fresh headless profile; no personal browser state accessed."""
from pathlib import Path
import json
import re
from playwright.sync_api import sync_playwright, expect

OUTPUT = Path("tmp/screenshots/verified")
OUTPUT.mkdir(parents=True, exist_ok=True)

def settled(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute("data-test-script-state", "notRunning", timeout=60000)
    expect(page.locator('[data-stale="true"]')).to_have_count(0, timeout=60000)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
    page.goto("http://127.0.0.1:8501", wait_until="networkidle")
    page.get_by_role("button", name=re.compile("Open platform")).first.wait_for()
    settled(page)
    page.screenshot(path=str(OUTPUT / "landing.png"), full_page=True)
    page.get_by_role("button", name=re.compile("Open platform")).first.click()
    page.get_by_role("heading", name="Executive Command Center", exact=True).wait_for()
    page.get_by_text("DataCo primary orders", exact=False).first.wait_for()
    settled(page)
    page.screenshot(path=str(OUTPUT / "overview.png"), full_page=True)
    for route, name in [("demand", "Demand Intelligence"), ("scenarios", "Scenario Lab"), ("copilot", "SupplyChain Copilot")]:
        page.get_by_test_id("stSidebar").get_by_role("button", name=re.compile(name)).click()
        page.get_by_role("heading", name=name, exact=True).wait_for()
        settled(page)
        if route == "scenarios":
            page.get_by_role("button", name="Run trained model", exact=True).click()
            page.get_by_text("Trained model inference", exact=True).wait_for()
            settled(page)
        page.screenshot(path=str(OUTPUT / f"{route}.png"), full_page=True)
    page.get_by_test_id("stSidebar").get_by_role("button", name=re.compile("Settings")).click()
    page.get_by_text("Dark", exact=True).last.click()
    page.get_by_test_id("stSidebar").get_by_role("button", name=re.compile("Executive Overview")).click()
    page.get_by_role("heading", name="Executive Command Center", exact=True).wait_for()
    page.get_by_text("DataCo primary orders", exact=False).first.wait_for()
    settled(page)
    page.screenshot(path=str(OUTPUT / "dark.png"), full_page=True)
    collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
    if collapse.is_visible():
        collapse.click()
    page.set_viewport_size({"width": 390, "height": 844})
    page.screenshot(path=str(OUTPUT / "mobile.png"), full_page=True)
    errors = page.get_by_test_id("stException").count()
    assert errors == 0
    browser.close()
Path("metadata/browser_qa.json").write_text(json.dumps({"surface": "isolated headless Chrome", "screenshots": [str(path) for path in OUTPUT.glob("*.png")], "prediction_control": "passed", "exception_panels": errors}, indent=2) + "\n")
print("Verified browser screenshots and delivery prediction interaction passed.")
