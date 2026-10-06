"""Actual floating chat QA. Live request uses public help only; supplied data stays local."""
import sys,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from playwright.sync_api import sync_playwright,expect
from workspace_usability_qa import settled
from workspace_usability_qa import theme
from services.ai_provider import configuration
OUTPUT=ROOT/'tmp/screenshots/sevika';OUTPUT.mkdir(parents=True,exist_ok=True)
secret=configuration().token
findings=[];network=[];js_errors=[];checks=[]

LOCAL_ONLY='--local-only' in sys.argv

def ready(page):
 settled(page);page.wait_for_timeout(300)
 # Hidden native popover portals can retain suspended animations.
 page.wait_for_function("()=>document.getAnimations().filter(a=>['sc-enter','sc-surface'].includes(a.animationName)&&a.effect?.target?.checkVisibility()).every(a=>a.playState!=='running')")
 assert page.get_by_test_id('stException').count()==0

def wait_answer(page):
 page.wait_for_function("()=>[...document.querySelectorAll('.st-key-sevika_panel')].some(p=>p.checkVisibility()&&(p.querySelectorAll('[data-testid=stChatMessage]').length>=2||p.querySelector('[data-testid=stAlertContentError]')))",timeout=40000)
 ready(page)
 errors=page.locator('.st-key-sevika_panel:visible [data-testid=stAlertContentError]').all_text_contents()
 assert not secret or secret not in json.dumps(errors)
 assert not errors,errors

def ask(page,text):
 panel=page.locator('.st-key-sevika_panel:visible')
 panel.get_by_role('textbox',name='Ask Sevika',exact=True).fill(text)
 panel.get_by_role('button',name='Ask',exact=True).click();wait_answer(page)

def open_chat(page):
 if not page.locator('.st-key-sevika_panel:visible').is_visible():
  button=page.get_by_role('button',name='forum Sevika',exact=True)
  expect(button).to_be_visible(timeout=15000)
  button.click(timeout=15000)
 page.get_by_role('heading',name='Sevika',exact=True).wait_for()

def close_chat(page):
 page.keyboard.press('Escape');expect(page.locator('.st-key-sevika_panel:visible')).not_to_be_visible()

def navigate(page,route):
 close_chat(page) if page.locator('.st-key-sevika_panel:visible').is_visible() else None
 button=page.locator('.st-key-nav_'+route+' button')
 if not button.is_visible():page.get_by_test_id('stSidebar').get_by_test_id('stExpander').filter(has=button).locator('summary').first.click()
 button.click();ready(page)

def fit(page,name):
 open_chat(page)
 rect=page.get_by_test_id('stPopoverBody').filter(has=page.locator('.st-key-sevika_panel:visible')).bounding_box()
 viewport=page.viewport_size
 assert rect['x']>=0 and rect['y']>=0 and rect['x']+rect['width']<=viewport['width']+1 and rect['y']+rect['height']<=viewport['height']+1,rect
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 page.screenshot(path=str(OUTPUT/(name+'.png')))

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
 page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
 page.on('request',lambda req:network.append(req.url));page.on('pageerror',lambda err:js_errors.append('Browser JavaScript error'))
 def scan(value):
  text=value.decode('utf-8',errors='ignore') if isinstance(value,bytes) else str(value)
  if secret and secret in text:findings.append('Private credential')
 def ws(socket):socket.on('framereceived',scan);socket.on('framesent',scan)
 page.on('websocket',ws)
 page.goto('http://127.0.0.1:8501/?page=landing');ready(page);open_chat(page)
 assert not page.locator('.st-key-sevika_predict button:visible').count()
 if not LOCAL_ONLY:
  # Only public product-help context is sent externally.
  ask(page,'How do I enter the platform and use demo sign-in?')
  assert page.locator('.st-key-sevika_messages:visible').get_by_text('Live AI',exact=True).count()==1
  with page.expect_download() as event:page.get_by_role('button',name='Download conversation',exact=True).click()
  conversation=json.loads(Path(event.value.path()).read_text(encoding='utf-8'))
  assert conversation['dataset']=='public' and len(conversation['turns'])==1
  checks.append('Actual public-help AI conversation, validated evidence and JSON download')
  (ROOT/'metadata/sevika_live_qa.json').write_text(json.dumps({'passed':True,'payload':'public workflow only; zero supplied rows','actual_response_rendered':True,'validated_download':True,'engine':'Live AI'},indent=2)+'\n',encoding='utf-8')
  fit(page,'public-live')
 # All dataset-bearing operations below explicitly use local analysis.
 local=page.get_by_role('radio',name='Local analysis',exact=True);local.focus();local.press('Space');ready(page)
 close_chat(page);page.locator('.st-key-landing_open_platform button').click();ready(page)
 width=page.get_by_test_id('stMain').bounding_box()['width'];open_chat(page)
 assert page.get_by_role('radio',name='Local analysis',exact=True).is_checked()
 ask(page,'What is the total sales in the current selection?')
 messages=page.locator('.st-key-sevika_messages:visible')
 assert 'Sum Sales' in messages.inner_text()
 # No second answer on an ordinary rerun.
 close_chat(page);page.locator('.st-key-nav_overview button').click();ready(page);open_chat(page)
 assert page.locator('.st-key-sevika_messages:visible [data-testid=stChatMessage]').count()==2
 assert abs(page.get_by_test_id('stMain').bounding_box()['width']-width)<1
 checks.append('Local dataset totals, per-context conversation persistence and no reserved main width')
 page.locator('.st-key-sevika_clear button:visible').click();ready(page)
 assert page.locator('.st-key-sevika_messages:visible [data-testid=stChatMessage]').count()==0
 page.locator('.st-key-sevika_predict button:visible').click()
 page.get_by_text('50 trained outputs ready to explain.',exact=True).wait_for(timeout=40000);ready(page)
 ask(page,'Explain the new trained predictions and their mean risk.')
 assert 'New trained' in page.locator('.st-key-sevika_messages:visible').inner_text()
 checks.append('Registered delivery model produces 50 outputs and chat explains measured predictions')
 for route,phrase in [('demand','web-visit'),('profitability','profitability'),('comparison','compare')]:
  print("Checking",route,flush=True);navigate(page,route);open_chat(page)
  assert phrase in page.locator('.st-key-sevika_panel:visible').inner_text().lower()
  assert page.locator('.st-key-sevika_messages:visible [data-testid=stChatMessage]').count()==0
 checks.append('Suggestions and isolated conversations follow demand, profitability and comparison pages')
 for choice in ['Light','Dark']:
  print('Checking theme',choice,flush=True);close_chat(page);theme(page,choice);ready(page)
  fit(page,'desktop-'+choice.lower());close_chat(page)

  collapse=page.locator('[data-testid=stSidebarCollapseButton] button')
  if page.get_by_test_id('stSidebar').get_attribute('aria-expanded')=='true':collapse.click();ready(page)
  for width in [390,320]:
   page.set_viewport_size({'width':width,'height':844});ready(page);fit(page,str(width)+'-'+choice.lower());close_chat(page)
  page.set_viewport_size({'width':1440,'height':1000});ready(page)
 checks.append('Light/dark desktop and 390px/320px panels stay within viewport; Escape closes accessibly')
 scan(page.content());assert not findings and not js_errors
 assert not any('router.huggingface.co' in url or 'api.groq.com' in url for url in network)
 browser.close()
report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':True,'checks':checks,'live_ai_payload':'No external requests (local-only run)' if LOCAL_ONLY else 'Public workflow only; no supplied dataset summaries','private_credential_findings':len(findings),'browser_direct_ai_requests':0,'javascript_errors':len(js_errors),'live_request_in_this_run':not LOCAL_ONLY}
(ROOT/'metadata/sevika_browser_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
