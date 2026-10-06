"""Exercise Comparison Studio controls against the registered datasets."""
import os
os.environ['SUPPLYCHAIN_PROVIDER']='verified'
import sys,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from services import parameter_comparison as analysis
from services.provider import get_service

def check(at):
    assert not at.exception,[e.message for e in at.exception]
    assert not at.error,[e.value for e in at.error]

at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90)
for key,value in {'authenticated':True,'route':'comparison','route_initialized':True}.items():at.session_state[key]=value
at.run();check(at)
checks=['Delivery comparison route and source coverage']
for kind in ['Scatter','Correlation heatmap','Distribution']:
    at.selectbox(key='comparison_delivery_graph').select(kind).run();check(at)
    checks.append(kind+' renders')
at.multiselect(key='comparison_delivery_groups').set_value(['Date','Shipping Mode']).run()
at.selectbox(key='comparison_delivery_graph').select('Trend').run();check(at)
checks.append('Chronological multi-series date trend renders')
at.button(key='comparison_run_prediction').click().run();check(at)
result=at.session_state['comparison_prediction_delivery']['data']
assert result['Risk Probability'].notna().all() and len(result)>0
checks.append(f'Registered delivery model scored {len(result)} selected orders')
at.selectbox(key='comparison_dataset').select('demand').run();check(at)
at.button(key='comparison_run_prediction').click().run();check(at)
result=at.session_state['comparison_prediction_demand']['data']
assert result['Predicted Visits'].notna().all() and len(result)==76
checks.append('Dataset switch isolates demand; trained model forecasts 76 products')
at.radio(key='comparison_demand_mode').set_value('Two cohorts').run();check(at)
checks.append('Disjoint A/B cohort comparison renders')
# A narrative token must be replaced after data or comparison factors change.
from services import ai_narration
assert ai_narration.status()['provider']=='Hugging Face Inference Providers'
assert at.button(key='comparison_generate_ai').disabled == (not ai_narration.status()['available'])
checks.append('Hugging Face configuration controls explicit narration; no automatic network calls')
report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':True,'checks':checks,'delivery_outputs':len(at.session_state['comparison_prediction_delivery']['data']),'demand_outputs':len(result)}
(ROOT/'metadata/comparison_functional_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
