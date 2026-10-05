"""Rendered dashboard audit and functional QA against the 18-issue usability brief.

Run with the project virtualenv while the local Streamlit preview uses verified data.
Uses a fresh, isolated Chrome session; never accesses a personal browser profile.
"""
import csv
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tmp/screenshots/workspace-experience"
REPORT = ROOT / "metadata/workspace_usability_qa.json"
BASE = os.environ.get("SUPPLYCHAIN_PREVIEW_URL", "http://127.0.0.1:8501").rstrip("/")

MEASURE = r'''() => {
 const root=document.querySelector('.stApp');
 const scopes=[root,...document.querySelectorAll('[data-testid="stPopoverBody"]')];
 const visible=e=>{if(!e.getClientRects().length||e.closest('[aria-hidden="true"],script,style,defs,[data-testid="stIconMaterial"]'))return false;for(let p=e;p;p=p.parentElement){const s=getComputedStyle(p);if(s.display==='none'||s.visibility==='hidden'||s.opacity==='0')return false}return true};
 const canvas=document.createElement('canvas');canvas.width=canvas.height=1;const ctx=canvas.getContext('2d'),cache={};
 const rgba=c=>{if(cache[c])return cache[c];ctx.clearRect(0,0,1,1);ctx.fillStyle=c;ctx.fillRect(0,0,1,1);return cache[c]=[...ctx.getImageData(0,0,1,1).data].map((v,i)=>i===3?v/255:v)};
 const blend=(a,b)=>a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3]));
 const lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
 const nodes=[],contrast=[];
 for(const scope of scopes){const walker=document.createTreeWalker(scope,NodeFilter.SHOW_TEXT);while(walker.nextNode()){
  const n=walker.currentNode,e=n.parentElement;
  if(!n.textContent.trim()||!visible(e)||(e.closest('svg')&&!e.closest('.js-plotly-plot text')))continue;
  const s=getComputedStyle(e),color=e.closest('svg')?s.fill:s.color;
  const node={text:n.textContent.trim().slice(0,100),size:s.fontSize,family:s.fontFamily,color};nodes.push(node);
  if(e.closest('button:disabled,[aria-disabled="true"],.modebar'))continue;
  const chain=[];for(let p=e;p;p=p.parentElement)chain.unshift(p);
  let bg=[255,255,255],opacity=1;
  for(const p of chain){const ps=getComputedStyle(p);bg=blend(rgba(ps.backgroundColor),bg);opacity*=parseFloat(ps.opacity)}
  const ink=rgba(color).slice();ink[3]*=opacity;const fg=blend(ink,bg);
  const l=[lum(fg),lum(bg)].sort((a,b)=>a-b),ratio=(l[1]+.05)/(l[0]+.05);
  const minimum=parseFloat(s.fontSize)>=24||(parseFloat(s.fontSize)>=18.66&&parseInt(s.fontWeight)>=700)?3:4.5;
  if(ratio+.01<minimum)contrast.push({...node,ratio:Math.round(ratio*100)/100,minimum});
 }}
 const elements=scopes.flatMap(r=>[...r.querySelectorAll('*')]).filter(visible);
 const buttons=scopes.flatMap(r=>[...r.querySelectorAll('button')]).filter(visible).map(e=>{const s=getComputedStyle(e),b=e.getBoundingClientRect();return {text:e.innerText,label:e.getAttribute('aria-label'),style:[s.backgroundColor,s.color,s.borderWidth,s.borderColor,s.borderRadius,s.fontSize].join('|'),width:b.width,height:b.height}});
 return {families:[...new Set(nodes.map(n=>n.family))],sizes:[...new Set(nodes.map(n=>n.size))],colors:[...new Set(nodes.map(n=>n.color))],radii:[...new Set(elements.map(e=>getComputedStyle(e).borderRadius))],button_styles:[...new Set(buttons.map(b=>b.style))],small:nodes.filter(n=>parseFloat(n.size)<12),contrast_failures:contrast,short_buttons:buttons.filter(b=>b.width<43.9||b.height<43.9),overflow:{width:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth}};
}'''


def capture(page, name, full=False):
    original = page.viewport_size
    if full:
        height = page.locator('[data-testid="stMain"]').evaluate("e=>e.scrollHeight")
        page.set_viewport_size({"width": original["width"], "height": height + 30})
    page.screenshot(path=str(OUTPUT / f"{name}.png"), full_page=True)
    if full:
        page.set_viewport_size(original)


def audit(page, name, report):
    settled(page)
    page.locator('[data-testid="stStatusWidget"]').wait_for(state="hidden", timeout=60000)
    page.wait_for_function("""() => ![...document.querySelectorAll('[data-testid="stElementContainer"]')].some(e => {const opacity=+getComputedStyle(e).opacity; return opacity>0 && opacity<1;})""", timeout=60000)
    page.wait_for_timeout(250)  # Allow responsive Plotly layout to finish.
    measured = page.evaluate(MEASURE)
    report["measurements"][name] = measured
    for metric, maximum in [("families", 4), ("sizes", 10), ("colors", 12), ("radii", 6), ("button_styles", 5)]:
        assert len(measured[metric]) <= maximum, (name, metric, measured[metric])
    assert not measured["small"], (name, "small text", measured["small"])
    assert not measured["contrast_failures"], (name, "contrast", measured["contrast_failures"])
    assert not measured["short_buttons"], (name, "targets", measured["short_buttons"])
    assert measured["overflow"]["doc"] <= measured["overflow"]["width"] + 1, (name, "horizontal overflow")
    print(name, {k: len(measured[k]) for k in ["families", "sizes", "colors", "radii", "button_styles"]}, flush=True)


def settled(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute("data-test-script-state", "notRunning", timeout=60000)
    expect(page.locator('[data-stale="true"]')).to_have_count(0, timeout=60000)


def theme(page, choice):
    page.locator('.st-key-top_header [data-testid="stPopoverButton"]:visible').nth(1).click()
    # Native React Aria radios use a decorated label above the hidden input.
    page.locator('[data-testid="stPopoverBody"]').get_by_text(choice, exact=True).click()
    expect(page.get_by_role("radio", name=choice, exact=True)).to_be_checked()
    expected = "#52627a" if choice == "Light" else "#d3dcec"
    page.wait_for_function("expected=>getComputedStyle(document.querySelector('.stApp')).getPropertyValue('--wa-muted').trim()===expected", arg=expected)
    page.keyboard.press("Escape")


def run():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "url": BASE,
              "scope": "Verified Executive Command Center, sidebar, Plotly text and open native popovers; button Material glyphs excluded, native markdown symbol font retained",
              "issue_numbers": list(range(1, 19)), "measurements": {}, "functional": [], "errors": [], "passed": False}
    try:
        with sync_playwright() as p:
            chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
            browser = p.chromium.launch(executable_path=str(chrome) if chrome.exists() else None, headless=True)
            page = browser.new_page(viewport={"width": 1512, "height": 1060}, reduced_motion="reduce", color_scheme="light")
            page.on("pageerror", lambda error: report["errors"].append(str(error)))
            page.goto(f"{BASE}/?page=landing", wait_until="networkidle")
            page.locator(".st-key-landing_open_platform").get_by_role("button").click()
            page.locator(".workspace-greeting h2").wait_for()
            expect(page.locator(".st-key-public_header")).to_have_count(0, timeout=30000)
            page.locator(".st-key-table_footer_overview").wait_for()
            settled(page)
            expect(page.get_by_role("heading", name="Executive Command Center", exact=True)).to_have_count(1)
            headings = page.locator('[data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3').evaluate_all("es=>es.map(e=>({tag:e.tagName,text:e.innerText}))")
            assert headings[0]["tag"] == "H1" and headings[1]["tag"] == "H2", headings[:2]
            expect(page.locator(".workspace-greeting a")).to_have_count(0)
            expect(page.locator(".workspace-greeting h3")).to_have_count(0)
            assert page.locator(".demo-notice span").last.evaluate("e=>getComputedStyle(e).fontSize") == "14px"
            assert page.get_by_text("2,280 product/day rows · supplied forecasts and bounds", exact=True).evaluate("e=>getComputedStyle(e).fontSize") == "14px"
            assert page.get_by_text("Review orders with supplied high-risk scores.", exact=True).evaluate("e=>getComputedStyle(e).fontSize") == "14px"
            labels = page.locator(".insight-card .eyebrow")
            assert labels.count() == 3
            for label in labels.all():
                assert "supplied records" in label.inner_text() and "SUPPLIED RECORDS" not in label.inner_text()
                assert label.evaluate("e=>getComputedStyle(e).fontSize") == "12px"
            report["functional"].append("Semantic H1→H2 greeting without anchor; disclosures/subtitles/insight copy 14px; record labels 12px and sentence case")

            for width in [1512, 1366, 820, 390, 320]:
                page.set_viewport_size({"width": width, "height": 1060})
                if width == 390:
                    collapse = page.locator('[data-testid="stSidebarCollapseButton"]')
                    box = collapse.bounding_box()
                    # Responsive Streamlit keeps the off-screen sidebar mounted.
                    if collapse.is_visible() and box and box["x"] >= 0 and box["x"] < width:
                        collapse.click()
                audit(page, f"light-{width}", report)
                panel = page.locator(".st-key-global_filters").bounding_box()
                count_text = page.locator(".st-key-filter_record_summary p").bounding_box()
                assert count_text["y"] + count_text["height"] <= panel["y"] + panel["height"] - 5, (panel, count_text)
                capture(page, f"final-light-{width}")
                if width in [1512, 390]:
                    capture(page, f"final-light-{width}-full", full=True)
            page.set_viewport_size({"width": 1512, "height": 1060})
            expand = page.locator('[data-testid="stExpandSidebarButton"]')
            if expand.is_visible():
                expand.click()

            centers = [page.locator('.st-key-filter_more_control [data-testid="stPopoverButton"]:visible').bounding_box(),
                       page.locator(".st-key-filter_active_summary").get_by_role("button").first.bounding_box(),
                       page.locator(".st-key-filter_record_summary p").bounding_box()]
            y = [box["y"] + box["height"] / 2 for box in centers]
            assert max(y) - min(y) <= 25, centers
            risk = page.locator(".js-plotly-plot").nth(1)
            distribution = risk.evaluate("e=>({labels:Array.from(e._fullData[0].labels),values:Array.from(e._fullData[0].values)})")
            assert set(distribution["labels"]) == {"Low", "Medium", "High"}
            assert sum(distribution["values"]) == 1918, distribution
            legend = risk.locator(".legend").bounding_box()
            pie = risk.locator(".pielayer").bounding_box()
            assert legend["y"] >= pie["y"] + pie["height"] - 10, (legend, pie)
            assert legend["y"] - (pie["y"] + pie["height"]) < 45, (legend, pie)
            category = page.locator(".js-plotly-plot").nth(3)
            labels_bottom = max(e.bounding_box()["y"] + e.bounding_box()["height"] for e in category.locator(".xtick text").all())
            assert category.locator(".annotation-text").last.bounding_box()["y"] >= labels_bottom
            report["functional"].append("Compact filter row aligned; donut legend immediately below chart; original three-band counts total 1,918 scored orders")

            page.locator(".st-key-filter_more_control").get_by_role("button").click()
            expect(page.locator(".st-key-advanced_filter_controls")).to_be_visible()
            audit(page, "advanced-filters-open", report)
            capture(page, "advanced-filters-desktop")
            country = page.locator(".st-key-advanced_filter_controls").get_by_role("combobox", name="Country", exact=True)
            country.click()
            # The first native multiselect option is the "Select all" action.
            choice = page.get_by_role("option").nth(1)
            selected_country = choice.inner_text().strip()
            choice.click()
            page.keyboard.press("Escape")
            page.keyboard.press("Escape")
            expect(page.locator(".st-key-filter_active_summary")).to_contain_text(selected_country)
            page.locator('.st-key-global_filters').get_by_role("button", name="Reset", exact=True).click()
            page.locator(".st-key-table_footer_overview").wait_for()
            report["functional"].append(f"Advanced Country filter accepts {selected_country}; active chip updates; Reset restores results and compact row")

            previous = page.locator(".st-key-previous_page_overview").get_by_role("button")
            following = page.locator(".st-key-next_page_overview").get_by_role("button")
            expect(page.locator(".table-page-status")).to_have_text("Page 1 of 43")
            expect(previous).to_be_disabled()
            expect(page.locator('.st-key-table_footer_overview input[type="number"]')).to_have_count(0)
            following.click()
            expect(page.locator(".table-page-status")).to_have_text("Page 2 of 43")
            following.click()
            expect(page.locator(".table-page-status")).to_have_text("Page 3 of 43")
            previous.click()
            expect(page.locator(".table-page-status")).to_have_text("Page 2 of 43")
            previous.click()
            expect(page.locator(".table-page-status")).to_have_text("Page 1 of 43")
            page.locator(".st-key-table_pagination_overview").get_by_role("button", name="Jump").click()
            number = page.get_by_role("spinbutton", name="Page", exact=True)
            expect(number).to_have_attribute("max", "43")
            number.fill("43")
            number.press("Enter")
            expect(page.locator(".table-page-status")).to_have_text("Page 43 of 43")
            expect(following).to_be_disabled()
            audit(page, "jump-open", report)
            page.keyboard.press("Escape")
            search = page.locator(".st-key-table_search_overview").get_by_role("textbox")
            search.fill("76194")
            search.press("Enter")
            expect(page.locator(".table-page-status")).to_have_text("Page 1 of 1")
            expect(page.locator(".st-key-table_investigation_overview").get_by_role("heading", name="Order investigation")).to_have_count(1)
            search.fill("does-not-match-any-record-qa")
            search.press("Enter")
            page.get_by_text("No records match these table filters.", exact=True).wait_for()
            search.fill("")
            search.press("Enter")
            expect(page.locator(".table-page-status")).to_have_text("Page 1 of 43")
            report["functional"].append("Previous/Next and bounded Jump work at both boundaries; narrowing results clamps page; empty search recovers")

            with page.expect_download() as downloaded:
                page.locator(".st-key-download_overview").get_by_role("button").click()
            exported = downloaded.value
            text = Path(exported.path()).read_text(encoding="utf-8-sig")
            rows = list(csv.DictReader(io.StringIO(text)))
            assert len(rows) == 636 and all(row["Risk"] == "High" for row in rows)
            risks = [float(row["Risk Probability"]) for row in rows]
            assert risks == sorted(risks, reverse=True)
            report["functional"].append("Table download contains all 636 matching High-risk rows in descending supplied risk order")

            page.locator(".st-key-open_overview").get_by_role("button").click()
            page.get_by_role("heading", name="Order Explorer", exact=True).wait_for()
            page.locator(".st-key-nav_overview").get_by_role("button").click()
            page.locator(".workspace-greeting h2").wait_for()
            report["functional"].append("Titled order investigation opens Order Explorer and returns to overview")

            trigger = page.locator('.st-key-workspace_search_trigger [data-testid="stPopoverButton"]:visible')
            assert trigger.bounding_box()["width"] < 150
            wrapper = page.locator(".st-key-workspace_search_trigger")
            assert wrapper.bounding_box()["width"] < 150
            assert wrapper.evaluate("e=>getComputedStyle(e).backgroundColor") == "rgba(0, 0, 0, 0)"
            expect(trigger).to_have_attribute("aria-haspopup", "dialog")
            page.keyboard.press("Tab")
            trigger.focus()
            assert trigger.evaluate("e=>getComputedStyle(e).outlineStyle") != "none"
            trigger.press("Enter")
            universal = page.get_by_role("textbox", name="Universal search", exact=True)
            expect(universal).to_be_visible()
            audit(page, "search-open", report)
            universal.fill("76194")
            universal.press("Enter")
            page.get_by_role("heading", name="Universal Explorer", exact=True).wait_for()
            page.locator(".st-key-nav_overview").get_by_role("button").click()
            page.locator(".workspace-greeting h2").wait_for()
            report["functional"].append("Compact Search button has visible keyboard focus, opens real search input and submits to Universal Explorer")

            presentation = page.locator(".st-key-overview_presentation").get_by_role("button")
            expect(presentation.locator('[data-testid="stIconMaterial"]')).to_have_text("fullscreen")
            presentation.click()
            page.locator(".presentation-banner").wait_for()
            expect(page.locator('[data-testid="stSidebar"]')).to_be_hidden()
            audit(page, "presentation", report)
            page.locator(".st-key-presentation_button").get_by_role("button").click()
            expect(page.locator(".presentation-banner")).to_have_count(0)
            report["functional"].append("Presentation Mode uses fullscreen icon, hides sidebar, and exits without changing selected data")

            for choice in ["Dark", "System"]:
                if choice == "System":
                    page.emulate_media(color_scheme="dark")
                theme(page, choice)
                for width in [1512, 390]:
                    page.set_viewport_size({"width": width, "height": 1060})
                    audit(page, f"{choice.lower()}-{width}", report)
                    capture(page, f"final-{choice.lower()}-{width}")
                page.set_viewport_size({"width": 1512, "height": 1060})
            theme(page, "Light")
            page.set_viewport_size({"width": 320, "height": 1060})
            page.locator(".st-key-filter_more_control").get_by_role("button").click()
            audit(page, "advanced-filters-mobile", report)
            body = page.locator('[data-testid="stPopoverBody"]')
            assert body.bounding_box()["width"] <= 320
            capture(page, "advanced-filters-mobile")
            page.keyboard.press("Escape")
            report["functional"].append("Light, Dark and System dark remain readable and responsive; mobile advanced filters fit 320px")
            assert not report["errors"], report["errors"]
            report["passed"] = True
            browser.close()
    except Exception as error:
        report["failure"] = str(error)
        raise
    finally:
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"passed": report["passed"], "measurements": len(report["measurements"]), "functional_groups": len(report["functional"]), "browser_errors": len(report["errors"])}), flush=True)


if __name__ == "__main__":
    run()
