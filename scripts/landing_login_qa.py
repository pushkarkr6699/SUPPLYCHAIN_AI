"""Responsive browser review for only the public landing and login pages."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright.sync_api import expect

OUTPUT = Path("tmp/screenshots/public-experience")
OUTPUT.mkdir(parents=True, exist_ok=True)
ERRORS = []


def check_horizontal_overflow(page, label):
    dims = page.evaluate("({width:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth})")
    assert max(dims["doc"], dims["body"]) <= dims["width"] + 2, f"{label} horizontal overflow: {dims}"


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
    page = browser.new_page(viewport={"width": 1512, "height": 1060}, device_scale_factor=1, reduced_motion="reduce")
    page.on("pageerror", lambda error: ERRORS.append(str(error)))
    page.goto("http://127.0.0.1:8501", wait_until="networkidle")
    page.locator(".hero h1").wait_for()
    page.get_by_role("heading", name="Operations at a glance").wait_for()
    assert page.get_by_text("DEMO UI DATA").count() >= 2
    check_horizontal_overflow(page, "wide landing")

    page.locator(".public-links a[href='#platform']").click()
    assert page.evaluate("location.hash") == "#platform"
    page.locator("[data-testid='stMain']").evaluate("el => el.scrollTop = 900")
    header_top = page.locator("[data-testid='stLayoutWrapper']:has(> .stVerticalBlock.st-key-public_header)").evaluate("el => Math.round(el.getBoundingClientRect().top)")
    assert header_top == 0, f"Landing header is not sticky: {header_top}"
    page.locator("[data-testid='stMain']").evaluate("el => el.scrollTop = 0")

    for width, height, name in [(1512, 1060, "landing-wide"), (1366, 900, "landing-laptop"), (820, 980, "landing-tablet"), (390, 844, "landing-mobile")]:
        page.set_viewport_size({"width": width, "height": height})
        page.wait_for_timeout(250)
        check_horizontal_overflow(page, name)
        page.screenshot(path=str(OUTPUT / f"{name}.png"), full_page=True)

    page.set_viewport_size({"width": 1512, "height": 1060})
    page.locator(".st-key-public_header").get_by_role("button", name="Sign in", exact=True).click()
    page.get_by_role("heading", name="Sign in to continue.").wait_for()
    page.get_by_text("Demo authentication is enabled for this preview.").wait_for()
    page.get_by_role("heading", name="Your supply chain intelligence workspace.").wait_for()
    for width, height, name in [(1512, 1060, "login-wide"), (1366, 900, "login-laptop"), (820, 980, "login-tablet"), (390, 844, "login-mobile")]:
        page.set_viewport_size({"width": width, "height": height})
        page.wait_for_timeout(250)
        check_horizontal_overflow(page, name)
        page.screenshot(path=str(OUTPUT / f"{name}.png"), full_page=True)

    password = page.get_by_role("textbox", name="Password")
    assert password.get_attribute("type") == "password"
    page.get_by_role("button", name="Show", exact=True).click()
    page.get_by_role("button", name="Hide", exact=True).wait_for()
    expect(page.get_by_role("textbox", name="Password")).to_have_attribute("type", "text")
    page.get_by_role("button", name="Hide", exact=True).click()
    page.get_by_role("button", name="Show", exact=True).wait_for()
    expect(page.get_by_role("textbox", name="Password")).to_have_attribute("type", "password")
    page.locator(".st-key-login_submit").get_by_role("button").click()
    page.get_by_text("Enter a demo username and password, or continue in Demo Mode.").wait_for()
    page.get_by_role("button", name="Forgot password?").click()
    page.get_by_text("Password recovery will be available when an authentication provider is connected.").wait_for()
    page.get_by_role("button", name="Continue in Demo Mode").click()
    page.get_by_role("heading", name="Executive Command Center").wait_for()
    assert not ERRORS, f"Browser JavaScript errors: {ERRORS}"
    print("Public QA passed: landing/login at 1512, 1366, 820 and 390 px; sticky navigation, overflow, password visibility, validation, recovery and demo entry.")
    print(f"Screenshots: {OUTPUT.resolve()}")
    browser.close()
