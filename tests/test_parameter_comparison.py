import json
from urllib.error import HTTPError
import numpy as np
import pandas as pd
import pytest
from services import parameter_comparison as service
from services import ai_narration as ai

@pytest.fixture
def frame():
    return pd.DataFrame({'Group':['private-A','private-A','private-B','private-B'], 'Date':pd.to_datetime(['2026-10-05','2026-10-06','2026-10-07','2026-10-08']), 'Sales':[10.,20.,30.,40.], 'Risk':[np.nan,np.nan,.2,.8], 'Late':[True,False,True,True]})

def test_aggregation_missing_coverage_and_no_mutation(frame):
    original=frame.copy(deep=True)
    result=service.comparison(frame,['Group'],['Sales','Risk','Late'],'Sum')
    assert result.Sales.tolist()==[30.,70.]
    assert np.isnan(result.Risk.iloc[0])
    assert result['Valid · Risk'].tolist()==[0,2]
    assert result.Records.tolist()==[2,2]
    assert result.Late.tolist()==[1,2]
    pd.testing.assert_frame_equal(frame,original)

@pytest.mark.parametrize('operation,expected',[('Mean',25),('Median',25),('Minimum',10),('Maximum',40),('Sum',100)])
def test_complete_aggregation(frame,operation,expected):
    result=service.comparison(frame,[],['Sales'],operation)
    assert result.Sales.iloc[0]==expected
    assert result.Records.iloc[0]==4

def test_week_groups_start_monday(frame):
    result=service.comparison(frame,['Date'],['Sales'],'Sum','Week')
    assert result.Date.tolist()==[pd.Timestamp('2026-10-05')]
    assert result.Sales.iloc[0]==100

def test_validation_and_nonfinite(frame):
    with pytest.raises(ValueError,match='each field once'): service.comparison(frame,['Sales'],['Sales'])
    with pytest.raises(ValueError,match='numeric'): service.comparison(frame,[],['Group'])
    with pytest.raises(ValueError,match='unavailable'): service.comparison(frame,[],['Unknown'])
    frame.loc[0,'Sales']=np.inf
    assert service.comparison(frame,[],['Sales']).Sales.iloc[0]==30

def test_arbitrary_numeric_groups_and_filters(frame):
    assert 'Sales' in service.catalog(frame)[0]
    assert len(service.filter_field(frame,'Sales',bounds=(20,30)))==2
    assert len(service.filter_field(frame,'Group',selection=['private-A']))==2
    assert service.comparison(frame,['Sales'],['Late']).Records.sum()==4

def test_cohorts_disjoint_and_empty_recovery(frame):
    with pytest.raises(ValueError,match='non-overlapping'): service.cohorts(frame,'Group',['private-A'],['private-A'])
    with pytest.raises(ValueError,match='both cohorts'): service.cohorts(frame,'Group',[],['private-A'])
    result=service.cohorts(frame,'Group',['private-A'],['private-B'])
    assert result.groupby('Cohort').size().tolist()==[2,2]
    assert 'Cohort' not in frame

def test_evidence_and_external_payload_privacy(frame):
    params={'dimensions':['Group'],'metrics':['Sales','Risk'],'operation':'Mean','cohorts':{'A':['private-A'],'B':['private-B']}}
    table=service.comparison(frame,params['dimensions'],params['metrics'])
    facts=service.evidence(frame,table,params['dimensions'],params['metrics'],'Mean')
    payload=service.narration_payload(facts,params,'Historical data')
    encoded=json.dumps(payload,allow_nan=False)
    assert 'private-A' not in encoded and 'private-B' not in encoded
    assert 'Segment 1' in encoded
    assert any('2 missing' in f['text'] for f in facts)
    assert {f['id'] for f in facts}=={f['id'] for f in payload['evidence']}

def test_signature_invalidates_rows_params_and_provenance(frame):
    baseline=service.signature(frame,{'metrics':['Sales']})
    assert baseline!=service.signature(frame.iloc[:2],{'metrics':['Sales']})
    assert baseline!=service.signature(frame,{'metrics':['Risk']})
    frame.attrs['data_source']='different'
    assert baseline!=service.signature(frame,{'metrics':['Sales']})

def test_predictions_refuse_demo(frame):
    with pytest.raises(ValueError,match='verified'): service.trained_predictions(frame,'delivery')

def answer():
    return {'summary':'Measured summary','insights':[{'title':'Coverage','observation':'Four records','next_step':'Review coverage','evidence_ids':['E1']}]}

def test_ai_schema_request_and_verified_refs(monkeypatch):
    monkeypatch.setattr(ai,'credentials',lambda:('test-key','gpt-4o-mini'))
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,size):
            return json.dumps({'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(answer())}]}]}).encode()
    def send(req,timeout):
        body=json.loads(req.data)
        assert req.full_url=='https://api.openai.com/v1/responses'
        assert timeout==25 and body['store'] is False
        assert body['text']['format']['strict'] is True
        return Response()
    monkeypatch.setattr(ai.request,'urlopen',send)
    assert ai.narrate({'evidence':[{'id':'E1','value':4}]})==answer()
    invalid=answer();invalid['insights'][0]['evidence_ids']=['E999']
    with pytest.raises(ai.NarrationUnavailable,match='unavailable evidence'):ai.validate_narration(invalid,{'E1'})

@pytest.mark.parametrize('code',[401,403,429,500])
def test_ai_http_errors_do_not_leak_credentials(monkeypatch,code):
    monkeypatch.setattr(ai,'credentials',lambda:('secret-test-value','model'))
    def send(*args,**kwargs): raise HTTPError('https://api.openai.com',code,'secret-test-value',{},None)
    monkeypatch.setattr(ai.request,'urlopen',send)
    with pytest.raises(ai.NarrationUnavailable) as caught: ai.narrate({'evidence':[{'id':'E1'}]})
    assert 'secret-test-value' not in str(caught.value)

def test_ai_missing_key_never_calls_network(monkeypatch):
    monkeypatch.setattr(ai,'credentials',lambda:('','model'))
    monkeypatch.setattr(ai.request,'urlopen',lambda *a,**k:pytest.fail('No key must not send data'))
    with pytest.raises(ai.NarrationUnavailable,match='OPENAI_API_KEY'):ai.narrate({'evidence':[{'id':'E1'}]})

@pytest.mark.parametrize('response',[[],{'status':'incomplete'},{'status':'completed','output':[]}])
def test_ai_incomplete_or_malformed_response_recovery(monkeypatch,response):
    monkeypatch.setattr(ai,'credentials',lambda:('test-key','model'))
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,size):return json.dumps(response).encode()
    monkeypatch.setattr(ai.request,'urlopen',lambda *a,**k:Response())
    with pytest.raises(ai.NarrationUnavailable):ai.narrate({'evidence':[{'id':'E1'}]})

def test_ai_timeout_recovery(monkeypatch):
    monkeypatch.setattr(ai,'credentials',lambda:('test-key','model'))
    def send(*args,**kwargs):raise TimeoutError('secret internal network detail')
    monkeypatch.setattr(ai.request,'urlopen',send)
    with pytest.raises(ai.NarrationUnavailable,match='connectivity'):ai.narrate({'evidence':[{'id':'E1'}]})
