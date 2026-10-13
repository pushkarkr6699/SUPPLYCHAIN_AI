"""Verify actual profitability across shared workspace sections; no external AI calls."""
from pathlib import Path
from datetime import datetime, timezone
import json
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from playwright.sync_api import sync_playwright,expect
from master_browser_qa import navigate,settled

OUT=ROOT/'tmp/screenshots/profitability-connected'
OUT.mkdir(parents=True,exist_ok=True)


def ready(page):
    settled(page)
    page.wait_for_timeout(400)
    settled(page)
    expect(page.get_by_text('This page could not be rendered',exact=False)).to_have_count(0)
    expect(page.get_by_text('The data service is unavailable',exact=False)).to_have_count(0)
    text=page.locator('body').inner_text()
    assert not re.search(r'DEMO UI DATA|Demo state|Demo response|Demo Analyst|Guided demo',text), 'Synthetic content in connected mode'


def choose_profit(page,route):
    box=page.locator('.st-key-'+route+'_dataset').get_by_role('combobox')
    if 'Profitability' not in box.inner_text():
        box.focus();box.press('ArrowDown')
        page.get_by_role('option',name=re.compile('Profitability')).click()
    ready(page)


def main():
    report={'passed':False,'checked_at':datetime.now(timezone.utc).isoformat(),
            'scope':'Actual registered profitability; independent filters and grain; no external AI request',
            'checks':[],'browser_errors':[]}
    try:
        with sync_playwright() as engine:
            browser=engine.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1100},reduced_motion='reduce')
            page.on('pageerror',lambda error:report['browser_errors'].append(str(error)))
            page.goto('http://127.0.0.1:8501')
            ready(page)
            expect(page.get_by_text('Registered historical sources',exact=False)).to_be_visible()
            report['checks'].append('Landing uses real aggregate summaries without individual records or synthetic previews')
            page.locator('.st-key-landing_open_platform button').click();ready(page)
            expect(page.get_by_role('heading',name='Profitability Overview',exact=True)).to_be_visible()
            expect(page.get_by_role('heading',name='Profitability scored outputs',exact=True)).to_be_visible()
            report['checks'].append('Overview includes independent profitability metrics and full model status')
            page.screenshot(path=str(OUT/'overview.png'))
            for route in ['profitability','insights','alerts','comparison','visualizations','copilot','explorer','quality','data','downloads','explainability','threshold','drift']:
                navigate(page,route)
                if route!='profitability':choose_profit(page,route)
                ready(page)
                if route in {'insights','alerts'}:
                    expect(page.get_by_text('Observed losing line items',exact=True).first).to_be_visible()
                    expect(page.get_by_text('High loss probability band',exact=True).first).to_be_visible()
                report['checks'].append('Registered profitability renders in '+route)
                print(route+': passed',flush=True)
                page.screenshot(path=str(OUT/(route+'.png')))
                if route=='downloads':
                    with page.expect_download() as result:
                        page.get_by_role('button',name='Filtered data · CSV',exact=True).click()
                    import pandas as pd
                    exported=pd.read_csv(result.value.path())
                    assert len(exported)>0 and 'Profitability Probability' in exported
                    assert not any('password' in c.casefold() for c in exported)
                    report['checks'].append('Profitability CSV download has actual scored lines and safe fields')
            navigate(page,'insights');choose_profit(page,'insights')
            page.locator('.st-key-insight_filter_feed_0_Profitability button').click();ready(page)
            expect(page.get_by_role('heading',name='Profitability Intelligence',exact=True)).to_be_visible()
            expect(page.locator('.st-key-filter_active_summary')).to_contain_text('Actual Profitable')
            report['checks'].append('Losing-line insight applies the real Boolean outcome filter to Profitability')
            page.set_viewport_size({'width':390,'height':1100});ready(page)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.screenshot(path=str(OUT/'profitability-mobile.png'))
            report['checks'].append('Filtered profitability mobile layout has no horizontal document overflow')
            assert not report['browser_errors'],report['browser_errors']
            report['passed']=True
            browser.close()
    except Exception as error:
        report['failure']=str(error)
        raise
    finally:
        (ROOT/'metadata/profitability_connected_browser_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'checks':len(report['checks']),'browser_errors':len(report['browser_errors'])}))


if __name__=='__main__':main()
