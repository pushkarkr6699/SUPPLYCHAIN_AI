"""Review aggregate payloads locally; --execute runs bounded live UI tests after transfer approval."""
import argparse,json,os,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['SUPPLYCHAIN_PROVIDER']='verified'
from services import ai_narration,live_insights
from services.provider import get_service


def privacy_check(payload):
 allowed={'id','metric','value','segment','kind','details'}
 assert isinstance(payload.get('evidence'),list) and payload['evidence']
 for fact in payload['evidence']:
  assert set(fact)<=allowed
  assert fact.get('segment') is None or fact['segment'].startswith('Segment ')
  assert fact.get('value') is None or isinstance(fact['value'],(int,float))
  assert set(fact.get('details',{}))<={'groups','missing','records','lowest_value','paired_records'}
  assert all(isinstance(v,(int,float)) for v in fact.get('details',{}).values())
 encoded=json.dumps(payload,allow_nan=False)
 assert len(encoded.encode())<24000
 return {'evidence_items':len(payload['evidence']),'payload_bytes':len(encoded.encode()),'raw_rows':0,'anonymous_segments':True}


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--execute',action='store_true',help='Send anonymized supplied-data summaries to Hugging Face/Groq. Obtain explicit transfer approval first.')
 args=parser.parse_args()
 manifest={}
 for source in ['delivery','demand','profitability','delivery_final']:
  _,payload,_=live_insights.context(get_service().records(dataset=source))
  manifest[source]=privacy_check(payload)
 if not args.execute:
  print(json.dumps({'network_calls':0,'destination':'Hugging Face router / Groq','preflight':manifest},indent=2));return
 from streamlit.testing.v1 import AppTest
 panels=[('overview','live_ai_overview',{}),('delivery','live_ai_delivery',{}),('demand','live_ai_demand',{}),('profitability','live_ai_profitability',{}),('delivery','live_ai_final_delivery',{'delivery_final_experiment':True}),('insights','live_ai_insight_center',{}),('copilot','live_ai_copilot',{'copilot_engine':'Live AI'}),('comparison','comparison',{}),('settings','settings',{'settings_section':'Copilot'})]
 panels += [('comparison','comparison',{'comparison_dataset':source}) for source in ['demand','profitability','delivery_final']]
 original=ai_narration.narrate;calls=[];checks=[]
 def monitored(payload):
  assert len(calls)<len(panels),'Request budget exceeded'
  policy=privacy_check(payload);start=time.monotonic()
  answer=original(payload)
  calls.append(dict(policy,seconds=round(time.monotonic()-start,2)))
  return answer
 try:
  ai_narration.narrate=monitored
  for route,key,state in panels:
   a=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90)
   for k,v in dict(authenticated=True,route=route,route_initialized=True,**state).items():a.session_state[k]=v
   a.run();assert not a.exception and not a.error,'Application failed before the request'
   before=len(calls)
   button={'comparison':'comparison_generate_ai','settings':'check_live_ai'}.get(key,key+'_generate')
   assert not a.button(key=button).disabled,'AI action is disabled'
   a.button(key=button).click().run()
   if a.error:raise ai_narration.NarrationUnavailable(a.error[0].value)
   assert not a.exception and len(calls)==before+1,'Live UI request failed'
   if key=='settings':assert any('connection succeeded' in e.value for e in a.success)
   else:
    saved=a.session_state['comparison_narration' if key=='comparison' else key]
    assert saved['answer']['summary'] and saved['answer']['insights']
    a.run();assert not a.exception and len(calls)==before+1 and a.button(key=button).disabled
   checks.append({'feature':key,'dataset_state':state,'passed':True,'network':'actual Hugging Face request','request':calls[-1]})
  report={'passed':True,'checks':checks,'actual_requests':len(calls),'preflight':manifest,'checked_at':datetime.now(timezone.utc).isoformat()}
 except (ai_narration.NarrationUnavailable,AssertionError) as exc:
  report={'passed':False,'checks':checks,'actual_successful_requests':len(calls),'safe_error':str(exc),'checked_at':datetime.now(timezone.utc).isoformat()}
 finally:ai_narration.narrate=original
 (ROOT/'metadata/hf_live_dataset_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2))
 if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
