"""Connected sources must replace demo content and expose profitability evidence."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
from streamlit.testing.v1 import AppTest
from config import ROOT
from services.provider import VerifiedArtifactsService
from services.workspace_status import connected_sources
from services.profitability_data import selection_summary
from services.analytics import alerts


def test_profitability_order_amounts_are_not_summed_across_lines():
    from services.parameter_comparison import comparison
    from services.decision_intelligence import momentum
    from services.executive_brief import build
    frame=VerifiedArtifactsService().records(dataset='profitability')
    with pytest.raises(ValueError,match='additive grain'):
        comparison(frame,[],['Profit'],'Sum')
    with pytest.raises(ValueError,match='not validated as additive'):
        momentum(frame,'Profit','Sum','Month')
    source=build({'profitability':frame},{})['sources'][0]
    facts={item['label']:item['value'] for item in source['evidence']}
    assert 'Total Profit' not in facts
    assert facts['Mean recorded Profit']==pytest.approx(frame.Profit.mean())
    assert source['change']['operation']=='Mean'


def test_real_profitability_summary_and_alert_counts_reconcile():
    frame=VerifiedArtifactsService().records(dataset='profitability')
    summary=selection_summary(frame)
    assert summary['lines']==27078
    assert summary['orders']==frame.Order.nunique()
    assert summary['losing_lines']==int(frame.Profit.le(0).sum())
    assert summary['profit_probability']==pytest.approx(frame['Profitability Probability'].mean())
    findings={item['Title']:item for item in alerts(frame)}
    assert findings['Observed losing line items']['Records']==summary['losing_lines']
    assert findings['High loss probability band']['Records']==summary['high_loss_lines']
    assert all('demo' not in item['Description'].lower() for item in findings.values())


def test_order_profitability_evidence_checks_identity_before_linking():
    from services.profitability_data import records,order_lines
    row=records().iloc[0]
    assert len(order_lines(row))>0
    invalid=row.copy();invalid['Country']='TEST mismatched identity'
    with pytest.raises(ValueError,match='identity'):order_lines(invalid)


def test_independent_filters_and_missing_source_do_not_fall_back_to_demo():
    service=VerifiedArtifactsService()
    source=service.records(dataset='profitability')
    market=source.Market.iloc[0]
    contexts={'profitability':{'Market':[market]}}
    states=connected_sources(service,contexts)
    assert states['profitability']['rows']==int(source.Market.eq(market).sum())
    assert states['delivery']['rows']==65752
    class Missing:
        def records(self,*args,**kwargs): raise FileNotFoundError('missing private source')
    unavailable=connected_sources(Missing())
    assert all(not item['available'] and item['frame'] is None and item['rows'] is None for item in unavailable.values())


@pytest.mark.parametrize('route',['landing','login','overview','alerts','insights'])
def test_connected_pages_use_real_data_and_profitability(monkeypatch,route):
    import services.provider as provider
    monkeypatch.setattr(provider,'SUPPLYCHAIN_PROVIDER','verified')
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60)
    for key,value in {'route':route,'route_initialized':True,'authenticated':route not in {'landing','login'}}.items():
        app.session_state[key]=value
    if route in {'alerts','insights'}:app.session_state[route+'_dataset']='profitability'
    app.run()
    assert not app.exception
    assert not any('could not be rendered' in error.value for error in app.error)
    html=' '.join(element.proto.body for element in app.get('html'))
    assert 'DEMO UI' not in html and 'Demo state' not in html and 'Demo response' not in html
    if route=='overview':
        assert any(metric.label=='Profitability line items' for metric in app.metric) or 'Profitability line items' in html
        assert 'Profitability scored outputs' in html
    if route in {'alerts','insights'}:
        assert 'Observed losing line items' in html and 'High loss probability band' in html
        assert app.session_state.active_filter_dataset=='profitability'
    if route=='login': assert app.button(key='login_demo').label=='Continue to workspace'
    if route=='insights':
        app.button(key='insight_copilot_feed_0_Profitability').click().run()
        assert not app.exception and app.session_state.copilot_dataset=='profitability'


def test_default_provider_is_connected_without_private_environment():
    # Execute config alone from a temporary working directory without reading .env.
    import os
    env={k:v for k,v in os.environ.items() if k!='SUPPLYCHAIN_PROVIDER'}
    code="from pathlib import Path; import types; source=Path('config.py').read_text(); source=source.replace('_ENV_FILE = ROOT / \".env\"','_ENV_FILE = ROOT / \"tmp/nonexistent-config-test.env\"'); module=types.ModuleType('cfg'); module.__file__=str(Path('config.py').resolve()); exec(compile(source,'config.py','exec'),module.__dict__); assert module.SUPPLYCHAIN_PROVIDER=='verified'; assert module.DELIVERY_PRIMARY_URI.endswith('DataCo_Final_Order_Level_Dataset.csv')"
    result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
