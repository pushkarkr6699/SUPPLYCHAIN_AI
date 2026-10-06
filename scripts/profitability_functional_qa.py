"""Functional profitability and live-AI UI checks against registered source artifacts."""
import os
os.environ['SUPPLYCHAIN_PROVIDER']='verified'
from pathlib import Path
import sys,json
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from services import ai_narration
checks=[]

def app(route,**extra):
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90)
    for key,value in dict(authenticated=True,route=route,route_initialized=True,**extra).items():at.session_state[key]=value
    at.run();verify(at,route);return at

def verify(at,label):
    assert not at.exception,[e.message for e in at.exception]
    assert not at.error,[e.value for e in at.error]
    checks.append(label)

at=app('profitability')
assert at.session_state.active_filter_dataset=='profitability'
assert any('0.4978' in w.value for w in at.warning)
for route in ['comparison','data','quality','downloads','explorer','insights','explainability','threshold','drift','copilot']:
    at=app(route,**{route+'_dataset':'profitability'})
    assert at.session_state.active_filter_dataset=='profitability'
    if route=='downloads':
        for kind in ['Predictions','Model Metrics','Reports','Charts']:
            next(r for r in at.radio if r.label=='Download category').set_value(kind).run();verify(at,'Profitability download '+kind)
    if route=='copilot':at.radio(key='copilot_engine').set_value('Live AI').run();verify(at,'Copilot live-AI panel')
at=app('reports')
for report in ['Profitability','Cross-Risk']:
    at.selectbox(key='report_type').select(report).run();verify(at,report+' report configuration')
    at.button(key='generate_report_pdf').click().run();verify(at,report+' PDF generation')
    assert at.session_state.generated_report[1].startswith(b'%PDF')
at=app('settings',settings_section='Copilot')
assert any(b.key=='check_live_ai' for b in at.button)
# Test the complete new AI button/result/stale-result lifecycle with a mocked API.
original_status,original_narrate=ai_narration.status,ai_narration.narrate
try:
    ai_narration.status=lambda:{'available':True,'provider':'Test transport','model':'synthetic-model','reason':'Mocked API for UI lifecycle verification.'}
    ai_narration.narrate=lambda payload:{'summary':'Test response from aggregate evidence','insights':[{'title':'Coverage','observation':'The selected rows provide the evidence.','next_step':'Review source coverage.','evidence_ids':['E1']}]}
    at=app('copilot',copilot_dataset='profitability',copilot_engine='Live AI')
    at.button(key='live_ai_copilot_generate').click().run();verify(at,'Live AI generated response renders with cited evidence (mocked API)')
    assert 'live_ai_copilot' in at.session_state
    at.text_area(key='copilot_live_question').set_value('Compare reliability instead').run();verify(at,'Changed AI question invalidates the prior answer')
    assert not at.button(key='live_ai_copilot_generate').disabled
finally:ai_narration.status,ai_narration.narrate=original_status,original_narrate
report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':True,'checks':checks,'live_external_ai_verified':False,'ai_configuration':ai_narration.status()}
(ROOT/'metadata/profitability_functional_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
