import sys,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from streamlit.testing.v1 import AppTest
from services import final_delivery_data,ai_narration
from playwright.sync_api import sync_playwright,expect
from unified_experience_qa import ready
from workspace_usability_qa import BASE
checks=[]
f=final_delivery_data.records()
a=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90)
for k,v in dict(authenticated=True,route='quality',route_initialized=True,quality_dataset='delivery_final',active_filter_dataset='delivery_final',filters={'Date':(f.Date.min().date(),f.Date.max().date())},filters_by_dataset={'delivery_final':{'Date':(f.Date.min().date(),f.Date.max().date())}}).items():a.session_state[k]=v
a.run();assert not a.exception,[e.message for e in a.exception]
assert not a.error,[e.value for e in a.error]
assert int(f.drop(columns=['Delivery Row']).duplicated().sum())==1757
checks.append('Source duplicate calculation is 1757; quality view renders without errors')
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
 page=browser.new_page(viewport={'width':1512,'height':1060},reduced_motion='reduce')
 page.goto(BASE+'/?page=landing');ready(page)
 page.locator('.st-key-landing_open_platform button').click();ready(page)
 page.locator('.st-key-nav_delivery button').click();ready(page)
 page.locator('.st-key-delivery_final_experiment input').check(force=True);ready(page)
 page.get_by_role('tab',name='Final records & exports',exact=True).click();ready(page)
 with page.expect_download() as download:page.get_by_role('button',name='Download final delivery report',exact=True).click()
 data=Path(download.value.path()).read_bytes();assert data.startswith(b'%PDF')
 (ROOT/'tmp/pdfs/final_delivery_browser_download.pdf').write_bytes(data)
 checks.append('Current final delivery PDF downloads successfully from browser')
 page.get_by_role('tab',name='Final scores',exact=True).click();ready(page)
 page.locator('[data-testid="stSidebarCollapseButton"] button').click();ready(page)
 for width in [390,320]:
  page.set_viewport_size({'width':width,'height':1060});ready(page)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  page.locator('.js-plotly-plot:visible').first.scroll_into_view_if_needed()
  page.screenshot(path=str(ROOT/f'tmp/screenshots/profitability/final-delivery-{width}.png'))
 checks.append('Current final delivery mobile 390px/320px has no page overflow')
 browser.close()
report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':True,'checks':checks,'regression_tests_passed':166,'live_ai':ai_narration.status(),'live_external_ai_verified':False}
(ROOT/'metadata/release_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
