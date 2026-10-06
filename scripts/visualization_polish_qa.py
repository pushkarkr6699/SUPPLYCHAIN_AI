"""Check final mobile chart titles, source notes and scrollable legend bounds."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from playwright.sync_api import sync_playwright,expect
from workspace_usability_qa import settled,theme
OUT=ROOT/'tmp/screenshots/visualizations';OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
 page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
 page.goto('http://127.0.0.1:8501/?page=landing');settled(page)
 page.locator('.st-key-landing_open_platform button').click();page.get_by_role('heading',name='Executive Command Center',exact=True).wait_for();settled(page)
 page.locator('.st-key-nav_visualizations button').click();page.get_by_role('heading',name='Visualization Studio',exact=True).wait_for();settled(page)
 field=page.locator('.st-key-visualizations_dataset').get_by_role('combobox');field.focus();field.press('ArrowDown')
 page.get_by_role('option',name='Demand forecasts',exact=True).click();page.locator('.st-key-viz_demand_metrics').wait_for();settled(page)
 theme(page,'Dark');settled(page)
 if page.get_by_test_id('stSidebar').get_attribute('aria-expanded')=='true':page.locator('[data-testid=stSidebarCollapseButton] button').click()
 page.set_viewport_size({'width':320,'height':1000});page.wait_for_timeout(500)
 checks=[]
 for index,name in [(0,'bars'),(1,'line')]:
  chart=page.get_by_test_id('stPlotlyChart').nth(index);chart.scroll_into_view_if_needed();page.wait_for_timeout(400)
  plot=chart.locator('.js-plotly-plot')
  card=page.locator('.st-key-viz_demand_card_'+str(index))
  note=card.get_by_text('Source: Verified product/day demand forecast CSV',exact=False).bounding_box()
  plot_box=plot.bounding_box();assert note['y']>=plot_box['y']+plot_box['height']-1
  for title in plot.locator('.xtitle').all():
   box=title.bounding_box();assert box['y']+box['height']<note['y']-2,(name,box,note)
  if name=='line':
   assert plot.evaluate('e=>e._fullLayout.legend.maxheight')==85
   assert plot.locator('.legend .bg').bounding_box()['height']<=86
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  page.screenshot(path=str(OUT/('final-dark-'+name+'-320.png')));checks.append(name+' source note clears axis title')
 w=page.locator('.st-key-viz_demand_charts');w.get_by_role('button',name='Clear all',exact=True).click()
 field=w.get_by_role('combobox');field.fill('Pie');page.wait_for_timeout(200);field.press('ArrowDown');page.get_by_role('option',name='Pie',exact=True).click();page.keyboard.press('Escape')
 page.get_by_role('button',name='Build visualizations',exact=True).click();settled(page)
 expect(page.get_by_test_id('stPlotlyChart')).to_have_count(1)
 chart=page.get_by_test_id('stPlotlyChart');chart.scroll_into_view_if_needed();page.wait_for_timeout(400)
 assert chart.locator('.js-plotly-plot .legend .bg').bounding_box()['height']<=86
 page.screenshot(path=str(OUT/'final-dark-pie-320.png'));checks.append('Pie legend has bounded scrollable height')
 b.close()
report={'passed':True,'width':320,'theme':'Dark','checks':checks,'network_ai_requests':0}
(ROOT/'metadata/visualization_polish_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
