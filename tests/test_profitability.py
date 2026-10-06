import json
import numpy as np
import pandas as pd
import pytest
from services import profitability_data as data,profitability_inference as model,live_insights
from services.export_service import report_pdf

@pytest.fixture
def raw():
    return pd.DataFrame({'Order Id':[1,1,2],'Market':['A']*3,'Order Region':['Region']*3,'Order Country':['Country']*3,'Category Name':['A','B','C'],'Department Name':['Dept']*3,'Customer Segment':['Consumer']*3,'Shipping Mode':['Standard Class']*3,'Order Item Quantity':[1,2,1],'Order Item Discount Rate':[.1]*3,'Order Item Product Price':[10.]*3,'Order_Date':['2018-01-01']*3,'Order Profit Per Order':[-2.,4.,3.],'Actual_Profitable':[0,1,1],'Profitability_Probability':[.3,.8,.6],'Predicted_Profitable':[1,1,1],'Correct_Prediction':[0,1,1],'Profitability_Risk':['High Loss Risk','High Profit Probability','Moderate Profitability']})

def canonical(raw):
    frame=data.validate_raw(raw).rename(columns=data.RENAME)
    frame['Order']=frame.Order.astype(str);frame['Profitability Row']=['P1','P2','P3'];frame['Loss Probability']=1-frame['Profitability Probability'];frame['Actual Profitable']=frame['Actual Profitable'].astype(bool)
    frame.attrs.update(dataset='profitability',verified_artifacts=True)
    return frame

@pytest.mark.parametrize('column,value',[('Profitability_Probability',np.nan),('Profitability_Probability',1.2),('Predicted_Profitable',0),('Actual_Profitable',1),('Correct_Prediction',1),('Profitability_Risk','Low'),('Order Item Discount Rate',1.1),('Order_Date','bad-date')])
def test_invalid_profitability_rows_are_rejected(raw,column,value):
    raw.loc[0,column]=value
    with pytest.raises((ValueError,TypeError)):data.validate_raw(raw)

def test_line_grain_and_missing_join_coverage(raw):
    frame=canonical(raw)
    assert frame.Order.nunique()==2 and len(frame)==3
    delivery=pd.DataFrame({'Order':['1','2','3'],'Date':pd.to_datetime(['2018-01-01']*3),'Market':['A']*3,'Country':['Country']*3,'Risk Probability':[.8,np.nan,.2]})
    joined=data.cross_risk(delivery,frame)
    assert len(joined)==3 and joined.Order.is_unique
    assert joined.loc[0,'Profitability rows']==2
    assert joined.loc[0,'Mean line profitability']==pytest.approx(.55)
    assert joined.loc[0,'Maximum line loss probability']==pytest.approx(.7)
    assert joined.loc[0,'Observed losing lines']==1
    assert pd.isna(joined.loc[2,'Profitability rows']) and pd.isna(joined.loc[1,'Risk Probability'])
    delivery.loc[0,'Country']='wrong'
    with pytest.raises(ValueError,match='identity'):data.cross_risk(delivery,frame)

def test_profitability_evaluation_matches_baseline(raw):
    scores=data.evaluation(canonical(raw))
    assert scores['Accuracy']==pytest.approx(2/3)
    assert scores['Predicted profitable rate']==1
    assert scores['Balanced accuracy']==.5

def test_profitability_ai_context_does_not_send_source_labels(raw):
    frame=canonical(raw);frame['Market']=['PrivateAlpha','PrivateAlpha','PrivateBeta']
    facts,payload,token=live_insights.context(frame)
    encoded=json.dumps(payload,allow_nan=False)
    assert 'PrivateAlpha' not in encoded and 'PrivateBeta' not in encoded
    assert '0.4978' in payload['limitations']
    assert any(f['title']=='Balanced accuracy' for f in facts)
    assert token!=live_insights.context(frame,'Explain losses')[2]

def test_fixed_profitability_paths_reject_traversal():
    with pytest.raises(ValueError,match='registered'):data.registered('../../.env')

def test_feature_contract_rejects_incomplete_scores_and_nonfinite():
    contract=model.contract()
    raw=data.artifact(data.SCORED)
    with pytest.raises(ValueError,match='Missing trained'):model.validate_features(raw,contract)
    probe=pd.read_csv(model.ROOT/'data/cache/profitability_conversion_probe.csv')
    probe.loc[0,contract['numeric_features'][0]]=np.inf
    with pytest.raises(ValueError,match='finite'):model.validate_features(probe,contract)

def test_original_model_conversion_fidelity_and_prediction_contract():
    probe=pd.read_csv(model.ROOT/'data/cache/profitability_conversion_probe.csv')
    result=model.predict(probe)
    assert np.allclose(result['Profitability Probability'],probe['Expected Probability'],atol=1e-6)
    assert result['Predicted Profitable'].eq(result['Profitability Probability'].ge(.2)).all()
    assert result.attrs['live_inference'] is True
    assert json.loads(model.VALIDATION.read_text())['supplied_score_parity'] is False

def test_current_runtime_needs_matching_validation(tmp_path,monkeypatch):
    report=tmp_path/'validation.json';report.write_text(json.dumps({'status':'failed'}))
    monkeypatch.setattr(model,'VALIDATION',report)
    assert model.status()['available'] is False

def test_profitability_pdf_contains_scope_and_limits():
    import pymupdf
    frame=data.records().head(30)
    output=report_pdf(frame,'Profitability',{},['KPIs','Charts','Insights','Records'])
    doc=pymupdf.open(stream=output,filetype='pdf');text=' '.join(p.get_text() for p in doc)
    assert 'Profitability Report' in text and '0.20' in text and '0.4978' in text
    assert 'Unique order IDs' in text and 'Line-item source' in text
def test_profitability_pdf_contains_no_footer_only_page():
    import pymupdf
    from services.profitability_data import records
    from services.export_service import report_pdf
    document=pymupdf.open(stream=report_pdf(records(),'Profitability',{},['KPIs','Charts','Insights','Records']),filetype='pdf')
    assert all(len(page.get_text().split())>20 for page in document)
