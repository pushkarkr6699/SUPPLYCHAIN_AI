"""Rendered Comparison Studio QA in an isolated Chrome profile."""
import json
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from unified_experience_qa import ready,contrast
from workspace_usability_qa import ROOT,BASE,theme
OUTPUT=ROOT/'tmp/screenshots/comparison';OUTPUT.mkdir(parents=True,exist_ok=True)
REPORT=ROOT/'metadata/comparison_browser_qa.json'
report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':False,'checks':[],'errors':[]}

def select(page,label,value):
    widget=page.get_by_test_id('stSelectbox').filter(has=page.get_by_text(label,exact=True)).first
    widget.get_by_role('combobox').focus()
    widget.get_by_role('combobox').press('ArrowDown')
    page.get_by_role('option',name=value,exact=True).click();page.wait_for_timeout(300);ready(page)

def apply(page):
    page.get_by_role('button',name='Apply comparison',exact=True).click();ready(page)

try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        page=browser.new_page(viewport={'width':1512,'height':1060})
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(BASE+'/?page=landing');ready(page)
        page.locator('.st-key-landing_open_platform button').click();ready(page)
        page.locator('.st-key-nav_comparison button').click();ready(page)
        expect(page.get_by_role('heading',name='Comparison Studio',exact=True)).to_be_visible()
        expect(page.locator('.js-plotly-plot:visible')).to_have_count(1)
        report['checks'].append('Landing -> dashboard -> Comparison Studio connected')
        for kind in ['Scatter','Correlation heatmap','Distribution','Comparison bars']:
            select(page,'Graph type',kind);apply(page)
            expect(page.locator('.js-plotly-plot:visible')).to_have_count(1)
            toolbar=page.locator('.modebar:visible');expect(toolbar).to_have_count(1)
            assert toolbar.locator('.modebar-btn').count()>=4
            report['checks'].append(kind+' and visible chart controls')
        page.get_by_role('tab',name='Key insights',exact=True).click();ready(page)
        expect(page.get_by_role('button',name='Generate AI insights',exact=True)).to_be_disabled()
        expect(page.get_by_text('OpenAI analyst narrative',exact=True)).to_be_visible()
        report['checks'].append('Evidence insights and clear missing-key state')
        page.get_by_role('tab',name='Predictions',exact=True).click();ready(page)
        page.get_by_role('button',name='Run trained predictions',exact=True).click();ready(page)
        expect(page.get_by_role('button',name='Download trained predictions',exact=True)).to_be_visible()
        report['checks'].append('Delivery trained prediction action and download')
        page.get_by_role('tab',name='Evidence & export',exact=True).click();ready(page)
        for label in ['Download comparison CSV','Download evidence brief']:
            with page.expect_download() as download:
                page.get_by_role('button',name=label,exact=True).click()
            target=OUTPUT/download.value.suggested_filename;download.value.save_as(target)
            assert target.stat().st_size>100
        manifest=json.loads((OUTPUT/'comparison_evidence.json').read_text())
        assert manifest['parameters']['metrics']==['Risk Probability','Sales'] and manifest['records']>0
        report['checks'].append('CSV and JSON contain current parameters and complete evidence')
        select(page,'Comparison dataset','Demand forecasts')
        expect(page.locator('.st-key-comparison_demand_metrics')).to_be_visible(timeout=30000)
        page.get_by_role('tab',name='Predictions',exact=True).click();ready(page)
        page.get_by_role('button',name='Run trained predictions',exact=True).click();ready(page)
        expect(page.get_by_text('76 trained-model outputs',exact=False)).to_be_visible()
        report['checks'].append('Demand source switch and 76-product trained forecast')
        page.get_by_role('tab',name='Graphs',exact=True).click();ready(page)
        for choice in ['Light','Dark']:
            theme(page,choice);ready(page)
            page.locator('[data-testid="stSidebarCollapseButton"] button').click();ready(page)
            for width in [1512,390,320]:
                page.set_viewport_size({'width':width,'height':1060});ready(page)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                contrast(page)
                page.screenshot(path=str(OUTPUT/f'{choice.lower()}-{width}.png'))
                page.locator('.js-plotly-plot:visible').scroll_into_view_if_needed();page.wait_for_timeout(300)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.screenshot(path=str(OUTPUT/f'{choice.lower()}-chart-{width}.png'))
            report['checks'].append(choice+' theme: desktop, 390px and 320px with no page overflow')
            page.set_viewport_size({'width':1512,'height':1060});ready(page)
            page.locator('[data-testid="stExpandSidebarButton"]').click();ready(page)
        assert not report['errors'],report['errors']
        report['passed']=True;browser.close()
except Exception as exc:
    report['failure']=str(exc);raise
finally:
    REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
