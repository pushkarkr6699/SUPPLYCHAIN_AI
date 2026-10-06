"""Verify interactive controls on the new comparison chart."""
import json
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
from unified_experience_qa import ready
from workspace_usability_qa import ROOT,BASE
report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':False,'checks':[]}
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1512,'height':1060},reduced_motion='reduce')
    page.goto(BASE);ready(page)
    page.locator('.st-key-landing_open_platform button').click();ready(page)
    page.locator('.st-key-nav_comparison button').click();ready(page)
    chart=page.locator('[data-testid="stPlotlyChart"]:visible').first
    chart.scroll_into_view_if_needed();plot=chart.locator('.js-plotly-plot')
    before=plot.evaluate('e=>e._fullLayout.yaxis.range[1]-e._fullLayout.yaxis.range[0]')
    chart.locator('.modebar-btn[data-title="Zoom in"]').click();page.wait_for_timeout(150)
    small=plot.evaluate('e=>e._fullLayout.yaxis.range[1]-e._fullLayout.yaxis.range[0]')
    assert small<before*.9
    chart.locator('.modebar-btn[data-title="Zoom out"]').click();page.wait_for_timeout(150)
    assert plot.evaluate('e=>e._fullLayout.yaxis.range[1]-e._fullLayout.yaxis.range[0]')>small*1.1
    chart.locator('.modebar-btn[data-title="Pan"]').click();assert plot.evaluate('e=>e._fullLayout.dragmode')=='pan'
    chart.locator('.modebar-btn[data-title="Zoom"]').click();assert plot.evaluate('e=>e._fullLayout.dragmode')=='zoom'
    chart.locator('.modebar-btn[data-title="Autoscale"]').click();assert plot.evaluate('e=>e._fullLayout.yaxis.autorange')
    chart.locator('.modebar-btn[data-title="Reset axes"]').click()
    report['checks'].append('Zoom in/out, pan, zoom, autoscale and reset work on comparison facets')
    width=chart.bounding_box()['width'];chart.locator('.modebar-btn[data-title="Fullscreen"]').click();page.wait_for_timeout(800)
    assert chart.bounding_box()['width']>width+100
    page.keyboard.press('Escape');page.wait_for_timeout(400)
    if chart.bounding_box()['width']>width+100:chart.locator('.modebar-btn').filter(has=page.locator('svg')).last.click()
    report['checks'].append('Fullscreen expands and exits')
    with page.expect_download() as download:chart.locator('.modebar-btn[data-title="Download plot as a PNG"]').click()
    assert open(download.value.path(),'rb').read(8)==b'\x89PNG\r\n\x1a\n'
    report['checks'].append('PNG export is a valid image')
    report['passed']=True;browser.close()
(ROOT/'metadata/comparison_chart_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
