"""Actual local studio controls, chart tools, exports and responsive rendering."""
import sys,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from playwright.sync_api import sync_playwright,expect
from workspace_usability_qa import settled,theme
from services.visualization_service import CHART_TYPES
OUT=ROOT/'tmp/screenshots/visualizations';OUT.mkdir(parents=True,exist_ok=True)
FINISH_ONLY='--finish-layout' in sys.argv
previous=json.loads((ROOT/'metadata/visualization_browser_qa.json').read_text(encoding='utf-8')) if FINISH_ONLY else None
report={'passed':False,'checked_at':datetime.now(timezone.utc).isoformat(),'checks':[],'javascript_errors':0,'network_ai_requests':0}


if FINISH_ONLY:
 report['checks']=previous['checks'][1:]
 report['resumed_from']=previous['checked_at']

def ready(page):
 settled(page);page.wait_for_timeout(300)
 assert page.get_by_test_id('stException').count()==0
 assert not page.get_by_text('This view could not be rendered',exact=False).count()


def multi(page,key,values):
 w=page.locator('.st-key-'+key)
 clear=w.get_by_role('button',name='Clear all',exact=True)
 if clear.count():clear.click()
 for value in values:
  field=w.get_by_role('combobox');field.fill(value);page.wait_for_timeout(150);field.press('ArrowDown')
  page.get_by_role('option',name=value,exact=True).click();page.keyboard.press('Escape')


def select(page,key,value):
 field=page.locator('.st-key-'+key).get_by_role('combobox');field.focus();field.press('ArrowDown')
 page.get_by_role('option',name=value,exact=True).click();ready(page)


def apply(page,kinds):
 multi(page,'viz_delivery_charts',kinds)
 page.get_by_role('button',name='Build visualizations',exact=True).click();ready(page)
 expect(page.get_by_test_id('stPlotlyChart')).to_have_count(len(kinds))
 print('Rendered',', '.join(kinds),flush=True)


try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
  page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
  errors=[];requests=[];page.on('pageerror',lambda e:errors.append('Browser JavaScript error'));page.on('request',lambda r:requests.append(r.url))
  page.goto('http://127.0.0.1:8501/?page=landing');ready(page)
  page.locator('.st-key-landing_open_platform button').click();page.get_by_role('heading',name='Executive Command Center',exact=True).wait_for();ready(page)
  expect(page.locator('.st-key-overview_visualizations_open button')).to_be_attached()
  page.locator('.st-key-nav_visualizations button').click();page.get_by_role('heading',name='Visualization Studio',exact=True).wait_for();ready(page)
  expect(page.get_by_test_id('stPlotlyChart')).to_have_count(3)
  report['checks'].append('Overview entry, sidebar navigation, and three default charts work')
  if not FINISH_ONLY:
   multi(page,'viz_delivery_groups',['Market','Region']);multi(page,'viz_delivery_metrics',['Sales','Profit','Risk Probability'])
   for offset in range(0,len(CHART_TYPES),6):apply(page,CHART_TYPES[offset:offset+6])
   report['checks'].append('All 18 chart types selected through actual controls and rendered in six-chart boards')
   apply(page,['Scatter'])
   chart=page.get_by_test_id('stPlotlyChart');chart.scroll_into_view_if_needed();plot=chart.locator('.js-plotly-plot')
   before=plot.evaluate('e=>e._fullLayout.yaxis.range[1]-e._fullLayout.yaxis.range[0]')
   chart.locator('.modebar-btn[data-title="Zoom in"]').click();page.wait_for_timeout(150)
   after=plot.evaluate('e=>e._fullLayout.yaxis.range[1]-e._fullLayout.yaxis.range[0]');assert after<before*.9
   chart.locator('.modebar-btn[data-title="Zoom out"]').click()
   chart.locator('.modebar-btn[data-title="Pan"]').click();assert plot.evaluate('e=>e._fullLayout.dragmode')=='pan'
   chart.locator('.modebar-btn[data-title="Autoscale"]').click();assert plot.evaluate('e=>e._fullLayout.yaxis.autorange')
   chart.locator('.modebar-btn[data-title="Reset axes"]').click()
   width=chart.bounding_box()['width'];chart.locator('.modebar-btn[data-title="Fullscreen"]').click();page.wait_for_timeout(500)
   assert chart.bounding_box()['width']>width+50
   page.keyboard.press('Escape');page.wait_for_timeout(300)
   with page.expect_download() as event:chart.locator('.modebar-btn[data-title="Download plot as a PNG"]').click()
   assert Path(event.value.path()).read_bytes()[:8]==b'\x89PNG\r\n\x1a\n'
   report['checks'].append('Zoom in/out, pan, autoscale, reset, fullscreen and PNG download work')
   page.get_by_test_id('stExpander').filter(has=page.get_by_text('Analysis table and downloads',exact=True)).locator('summary').click()
   for label in ['Download analysis CSV','Download chart settings']:
    with page.expect_download() as event:page.get_by_role('button',name=label,exact=True).click()
    content=Path(event.value.path()).read_bytes();assert len(content)>100
    if label.endswith('settings'):
     plan=json.loads(content);assert plan['dataset']=='delivery' and plan['charts']==['Scatter']
    else:assert b'Sales' in content and b'Records' in content
   report['checks'].append('Complete analysis CSV and source-specific chart-settings JSON download')
   apply(page,[])
   expect(page.get_by_text('Choose one or more visualizations and click Build visualizations.',exact=True)).to_be_visible()
   apply(page,['Vertical bars','Line','Histogram'])
   multi(page,'visualization_extra_sources',['Demand forecasts','Profitability line items','Final delivery line observations']);ready(page)
   expect(page.get_by_test_id('stPlotlyChart')).to_have_count(12,timeout=30000)
   assert page.locator('.st-key-viz_demand_period').count() and page.locator('.st-key-viz_profitability_period').count() and page.locator('.st-key-viz_delivery_final_period').count()
   report['checks'].append('All four sources render together in independent boards with their own additional periods; no merged rows')
   multi(page,'visualization_extra_sources',[]);ready(page)
  for dataset,label in [('demand','Demand forecasts'),('profitability','Profitability line items'),('delivery_final','Final delivery line observations'),('delivery','Delivery orders')]:
   select(page,'visualizations_dataset',label)
   expect(page.locator('.st-key-viz_'+dataset+'_metrics')).to_be_attached()
   expect(page.get_by_test_id('stPlotlyChart')).to_have_count(3)
  report['checks'].append('Primary source switching works for all four connected datasets and restores chart plans')
  for mode in ['Light','Dark']:
   theme(page,mode);ready(page)
   if page.get_by_test_id('stSidebar').get_attribute('aria-expanded')=='true':page.locator('[data-testid=stSidebarCollapseButton] button').click();ready(page)
   for width in [1440,390,320]:
    page.set_viewport_size({'width':width,'height':1000});ready(page)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    page.screenshot(path=str(OUT/(mode.lower()+'-'+str(width)+'.png')))
    first=page.get_by_test_id('stPlotlyChart').first;first.scroll_into_view_if_needed();page.wait_for_timeout(300)
    assert first.bounding_box()['width']<=width
    page.screenshot(path=str(OUT/(mode.lower()+'-chart-'+str(width)+'.png')))
   page.set_viewport_size({'width':1440,'height':1000});ready(page)
  report['checks'].append('Desktop and 390px/320px light/dark forms and charts fit the viewport')
  assert not errors;assert not any('router.huggingface.co' in u or 'api.groq.com' in u for u in requests)
  report['passed']=True;browser.close()
except Exception as exc:
 report['failure_type']=type(exc).__name__;raise
finally:
 (ROOT/'metadata/visualization_browser_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
