"""Controlled AI UI lifecycle regression; never sends data to an external provider."""
import os
os.environ['SUPPLYCHAIN_PROVIDER']='verified'
import json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from services import ai_narration
from components.navigation import ROUTES
checks=[];calls=[]
original=ai_narration.narrate
original_status=ai_narration.status

def app(route,**state):
 a=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90)
 for k,v in dict(authenticated=True,route=route,route_initialized=True,developer_mode=True,**state).items():a.session_state[k]=v
 a.run();assert not a.exception,[e.message for e in a.exception]
 return a

def response(payload):
 calls.append(payload)
 return {'summary':'Controlled transport response based on computed evidence.','insights':[{'title':'Coverage','observation':'Review the selected historical measurements.','next_step':'Review model limitations and the cited evidence.','evidence_ids':[payload['evidence'][0]['id']]}]}

panels=[('overview','live_ai_overview',{}),('delivery','live_ai_delivery',{}),('demand','live_ai_demand',{}),('profitability','live_ai_profitability',{}),('delivery','live_ai_final_delivery',{'delivery_final_experiment':True}),('insights','live_ai_insight_center',{}),('copilot','live_ai_copilot',{'copilot_engine':'Live AI'}),('comparison','comparison',{}),('settings','settings',{'settings_section':'Copilot'})]
try:
 ai_narration.narrate=response
 for route in ['landing','login',*ROUTES]:
  before=len(calls);a=app(route);assert len(calls)==before,'Unexpected automatic AI request'
  unexpected=[e.value for e in a.error if route!='diagnostics' or 'Error-state preview' not in e.value]
  assert not unexpected,unexpected
 checks.append({'check':'All public and authenticated routes, no automatic AI requests','routes':len(ROUTES)+2,'passed':True})
 for route,key,state in panels:
  a=app(route,**state);before=len(calls)
  button={'comparison':'comparison_generate_ai','settings':'check_live_ai'}.get(key,key+'_generate')
  a.button(key=button).click().run();assert not a.exception and not a.error
  assert len(calls)==before+1
  if key=='settings':assert any('connection succeeded' in s.value for s in a.success)
  else:
   store='comparison_narration' if key=='comparison' else key
   assert a.session_state[store]['answer']['insights']
   a.run();assert len(calls)==before+1 and a.button(key=button).disabled
  checks.append({'check':key+' result rendering and request lifecycle','passed':True,'transport':'controlled mock'})
 def failure(payload):raise ai_narration.NarrationUnavailable('Provider temporarily unavailable. Local evidence remains available.')
 ai_narration.narrate=failure
 for route,key,state in panels:
  a=app(route,**state);button={'comparison':'comparison_generate_ai','settings':'check_live_ai'}.get(key,key+'_generate')
  a.button(key=button).click().run();assert not a.exception
  assert any('temporarily unavailable' in e.value for e in a.error)
  assert not a.button(key=button).disabled
 checks.append({'check':'All nine AI panels gracefully render provider errors and permit explicit retry','passed':True})
 ai_narration.narrate=response
 for source in ['delivery','demand','profitability','delivery_final']:
  for route,key in [('insights','live_ai_insight_center'),('copilot','live_ai_copilot'),('comparison','comparison')]:
   a=app(route,**{route+'_dataset':source,'copilot_engine':'Live AI'})
   button='comparison_generate_ai' if key=='comparison' else key+'_generate'
   a.button(key=button).click().run();assert not a.exception and not a.error
 checks.append({'check':'Comparison, Insight Center and Copilot operate on all four registered datasets','passed':True,'transport':'controlled mock'})
 a=app('comparison');a.button(key='comparison_generate_ai').click().run();a.run();assert a.button(key='comparison_generate_ai').disabled
 base_status=original_status()
 ai_narration.status=lambda:dict(base_status,model='openai/gpt-oss-120b:fastest')
 a.run();assert not a.button(key='comparison_generate_ai').disabled
 ai_narration.status=original_status
 checks.append({'check':'Changing AI model invalidates cached comparison narration without replacing trained inference','passed':True})
 a=app('delivery');a.toggle(key='delivery_final_experiment').set_value(True).run();assert a.session_state.active_filter_dataset=='delivery_final'
 a.toggle(key='delivery_final_experiment').set_value(False).run();assert a.session_state.active_filter_dataset=='delivery'
 assert not a.exception
 checks.append({'check':'Final delivery toggle restores independent filter and evidence scope','passed':True})
finally:ai_narration.narrate=original;ai_narration.status=original_status
report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':True,'live_external_ai_verified':False,'checks':checks}
(ROOT/'metadata/hf_ui_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
