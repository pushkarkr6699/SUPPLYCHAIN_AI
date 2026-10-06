"""Explicitly approved anonymous dataset-summary live UI check; no raw rows."""
import sys,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from playwright.sync_api import sync_playwright,expect
from workspace_usability_qa import settled
from services.ai_provider import configuration
secret=configuration().token;leaks=[];requests=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
 page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
 def scan(value):
  content=value.decode('utf-8',errors='ignore') if isinstance(value,bytes) else str(value)
  if secret and secret in content:leaks.append('Credential exposed')
 def socket(ws):ws.on('framereceived',scan);ws.on('framesent',scan)
 page.on('websocket',socket);page.on('request',lambda r:requests.append(r.url))
 page.goto('http://127.0.0.1:8501/?page=landing');settled(page)
 page.locator('.st-key-landing_open_platform button').click();page.get_by_role('heading',name='Executive Command Center',exact=True).wait_for();settled(page);page.wait_for_timeout(500)
 page.locator('.st-key-sevika_launcher button:visible').first.click()
 panel=page.locator('.st-key-sevika_panel:visible')
 live=panel.get_by_role('radio',name='Live AI',exact=True)
 if not live.is_checked():live.focus();live.press('Space');settled(page)
 expect(live).to_be_checked(timeout=15000)
 question='Explain this selection, its predictions and model limitations.'
 panel.get_by_role('textbox',name='Ask Sevika',exact=True).fill(question)
 panel.get_by_role('button',name='Ask',exact=True).click()
 page.wait_for_function("()=>[...document.querySelectorAll('.st-key-sevika_panel')].some(p=>p.checkVisibility()&&(p.querySelectorAll('[data-testid=stChatMessage]').length>=2||p.querySelector('[data-testid=stAlertContentError]')))",timeout=40000)
 settled(page)
 errors=panel.locator('[data-testid=stAlertContentError]').all_text_contents();assert not errors,'Controlled live answer failure'
 assert panel.locator('[data-testid=stChatMessage]').count()==2
 with page.expect_download() as event:panel.get_by_role('button',name='Download conversation',exact=True).click()
 conversation=json.loads(Path(event.value.path()).read_text(encoding='utf-8'))
 assert conversation['dataset']=='delivery' and conversation['turns'][0]['engine']=='Live AI'
 assert conversation['turns'][0]['answer']['evidence_ids']
 scan(page.content());assert not leaks
 assert not any('router.huggingface.co' in u or 'api.groq.com' in u for u in requests)
 output=ROOT/'tmp/screenshots/sevika';output.mkdir(parents=True,exist_ok=True)
 page.screenshot(path=str(output/'verified-live.png'))
 browser.close()
report={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'dataset':'delivery','actual_api_response_rendered':True,'downloaded_conversation_validated':True,'evidence_references':len(conversation['turns'][0]['answer']['evidence_ids']),'credential_findings':len(leaks),'direct_browser_provider_requests':0,'authorization':'Explicit user approval for anonymous summaries to Hugging Face/Groq'}
(ROOT/'metadata/sevika_live_dataset_browser_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
