"""Rendered profitability/final-delivery upload, charts and responsive checks."""
import json
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from unified_experience_qa import ready,contrast
from workspace_usability_qa import ROOT,BASE,theme
import sys
sys.path.insert(0,str(ROOT))
OUTPUT=ROOT/'tmp/screenshots/profitability';OUTPUT.mkdir(parents=True,exist_ok=True)
report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':False,'checks':[],'errors':[],'live_external_ai_verified':False}


def select(page,label,value):
    widget=page.get_by_test_id('stSelectbox').filter(has=page.get_by_text(label,exact=True)).first
    widget.get_by_role('combobox').focus();widget.get_by_role('combobox').press('ArrowDown')
    page.get_by_role('option',name=value,exact=True).click();page.wait_for_timeout(300);ready(page)


def navigate(page,route):
    button=page.locator('.st-key-nav_'+route+' button')
    if not button.is_visible():
        exp=page.get_by_test_id('stSidebar').get_by_test_id('stExpander').filter(has=button)
        exp.locator('summary').click()
    button.click();ready(page)


try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        page=browser.new_page(viewport={'width':1512,'height':1060},reduced_motion='reduce')
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(BASE+'/?page=landing');ready(page)
        page.locator('.st-key-landing_open_platform button').click();ready(page)
        navigate(page,'profitability')
        expect(page.get_by_text('Scored line items',exact=True)).to_be_visible()
        expect(page.locator('.js-plotly-plot:visible')).to_have_count(2)
        report['checks'].append('Profitability source KPIs and two overview charts')
        page.get_by_role('tab',name='Trained prediction',exact=True).click();ready(page)
        upload=page.locator('.st-key-profit_main_upload input[type=file]')
        upload.set_input_files(str(ROOT/'data/profitability/final/DataCo_Final_Scored_Orders.csv'));ready(page)
        page.locator('.st-key-profit_main_run button').click();ready(page)
        expect(page.get_by_text('Missing trained profitability inputs:',exact=False)).to_be_visible()
        upload.set_input_files(str(ROOT/'data/cache/profitability_conversion_probe.csv'));ready(page)
        page.locator('.st-key-profit_main_run button').click();ready(page)
        expect(page.get_by_text('32 trained profitability predictions generated.',exact=True)).to_be_visible()
        with page.expect_download() as d:page.get_by_role('button',name='Download trained profitability predictions',exact=True).click()
        d.value.save_as(OUTPUT/'profitability_probe_predictions.csv')
        report['checks'].append('Incomplete inputs refused; 32 synthetic conversion probes score and download')
        page.get_by_role('tab',name='AI insights',exact=True).click();ready(page)
        from services.ai_narration import status
        if not status()['available']:expect(page.get_by_role('button',name='Generate live AI insights',exact=True)).to_be_disabled()
        else:expect(page.get_by_role('button',name='Generate live AI insights',exact=True)).to_be_enabled()
        report['checks'].append('AI configuration state reflects local token availability')
        page.get_by_role('tab',name='Overview',exact=True).click();ready(page)
        for choice in ['Light','Dark']:
            theme(page,choice);ready(page)
            page.locator('[data-testid="stSidebarCollapseButton"] button').click();ready(page)
            for width in [1512,390,320]:
                page.set_viewport_size({'width':width,'height':1060});ready(page)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                contrast(page)
                page.locator('.js-plotly-plot:visible').first.scroll_into_view_if_needed();page.wait_for_timeout(300)
                chart=page.locator('[data-testid="stPlotlyChart"]:visible').first
                assert chart.locator('.modebar-btn').count()>=4
                page.screenshot(path=str(OUTPUT/f'{choice.lower()}-{width}.png'))
            page.set_viewport_size({'width':1512,'height':1060});ready(page)
            page.locator('[data-testid="stExpandSidebarButton"]').click();ready(page)
            report['checks'].append(choice+' profitability desktop/mobile: readable text, no page overflow, visible controls')
        navigate(page,'delivery')
        page.locator('.st-key-delivery_final_experiment input').check(force=True);ready(page)
        expect(page.get_by_text('Scored line observations',exact=True)).to_be_visible()
        page.get_by_role('tab',name='Final trained prediction',exact=True).click();ready(page)
        page.locator('.st-key-final_delivery_upload input[type=file]').set_input_files(str(ROOT/'data/cache/final_delivery_conversion_probe.csv'));ready(page)
        page.locator('.st-key-final_delivery_run button').click();ready(page)
        expect(page.get_by_text('32 trained final delivery predictions generated.',exact=True)).to_be_visible()
        report['checks'].append('Final delivery experiment and 31-feature trained upload path')
        navigate(page,'comparison');select(page,'Comparison dataset','Final delivery line observations')
        expect(page.locator('.js-plotly-plot:visible')).to_have_count(1)
        report['checks'].append('Final delivery source available in Comparison Studio')
        assert not report['errors'],report['errors'];report['passed']=True;browser.close()
except Exception as exc:
    report['failure']=str(exc);raise
finally:
    (ROOT/'metadata/profitability_browser_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
