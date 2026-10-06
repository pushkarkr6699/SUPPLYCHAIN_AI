"""Live browser AI connection QA; synthetic connection evidence only, no business data."""
import sys,json
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from unified_experience_qa import ready
from playwright.sync_api import sync_playwright
from services.ai_provider import configuration
DEMO='--demo-operation' in sys.argv
BASE='http://127.0.0.1:'+('8502' if DEMO else '8501')
assert urlopen(BASE+'/_stcore/health',timeout=10).read()==b'ok'
token=configuration().token
findings=[];requests=[];errors=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
 page=browser.new_page(viewport={'width':1512,'height':1060},reduced_motion='reduce')
 page.on('request',lambda req: requests.append(req.url))
 def scan(value):
  data=value.decode('utf-8',errors='ignore') if isinstance(value,bytes) else str(value)
  if token and token in data:findings.append('private credential detected')
 def ws(socket):
  socket.on('framereceived',scan);socket.on('framesent',scan)
 page.on('websocket',ws)
 page.on('pageerror',lambda e:errors.append('browser JavaScript error'))
 page.goto(BASE+'/?page=landing');ready(page)
 page.locator('.st-key-landing_open_platform button').click();ready(page)
 if DEMO:
  assert 'synthetic' in page.inner_text('body').lower(),'Refuse demo AI test unless synthetic source is shown'
  exp=page.get_by_test_id('stExpander').filter(has=page.get_by_text('Live AI insights for this view',exact=True))
  exp.locator('summary').first.click()
  page.locator('.st-key-live_ai_overview_generate button').click();ready(page)
  success=page.get_by_text('Hugging Face interpretation',exact=False).count()>0
  assert success,'Demo live AI did not display a validated result'
  with page.expect_download() as event:page.get_by_role('button',name='Download AI insight brief',exact=True).click()
  answer=json.loads(Path(event.value.path()).read_text(encoding='utf-8'))
  from services.ai_narration import validate_narration
  validate_narration(answer['answer'],{f['id'] for f in answer['evidence']})
  page.locator('.st-key-nav_overview button').click();ready(page)
  exp=page.get_by_test_id('stExpander').filter(has=page.get_by_text('Live AI insights for this view',exact=True))
  if not page.locator('.st-key-live_ai_overview_generate button').is_visible():exp.locator('summary').first.click()
  assert page.locator('.st-key-live_ai_overview_generate button').is_disabled()
 else:
  button=page.locator('.st-key-nav_settings button')
  if not button.is_visible():
   exp=page.get_by_test_id('stSidebar').get_by_test_id('stExpander').filter(has=button)
   exp.locator('summary').first.click()
  button.click();ready(page)
  radio=page.get_by_role('radio',name='Copilot',exact=True)
  radio.focus();radio.press('Space');ready(page)
  page.locator('.st-key-check_live_ai button').click();ready(page)
  success=page.get_by_text('Live AI connection succeeded.',exact=True).count()>0
  assert success,'Settings connection check did not display success'
 scan(page.content())
 assert not findings and not errors
 assert not any('router.huggingface.co' in u or 'api.groq.com' in u for u in requests)
 (ROOT/'tmp/screenshots/huggingface').mkdir(parents=True,exist_ok=True)
 page.screenshot(path=str(ROOT/'tmp/screenshots/huggingface'/('demo-overview-live-insights.png' if DEMO else 'settings-live-connection.png')))
 browser.close()
report={'passed':True,'live_operation':('Executive Overview' if DEMO else 'Settings connection check'),'live_result_displayed':success,'payload':('synthetic demo fixtures' if DEMO else 'synthetic connection check; no dataset sent'),'browser_credential_findings':len(findings),'browser_external_ai_requests':0,'browser_js_errors':len(errors)}
(ROOT/('metadata/hf_demo_live_qa.json' if DEMO else 'metadata/hf_browser_qa.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
