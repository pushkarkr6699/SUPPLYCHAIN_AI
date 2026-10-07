"""Independent checks for observed anomalies and separate-grain brief evidence."""
from io import BytesIO
import pandas as pd
import pytest
import pymupdf
from services.decision_intelligence import anomalies
from services.executive_brief import build,pdf
from services.provider import VerifiedArtifactsService


def test_anomaly_classes_and_reference_are_observed_not_forecast():
    frame=pd.DataFrame({'Date':pd.date_range('2018-01-01',periods=10),'Sales':[0,1,2,3,4,5,6,7,20,50]})
    table,method=anomalies(frame,'Sales')
    assert method['q1']==2.25 and method['q3']==6.75
    assert table.Status.tolist()==['NORMAL']*8+['UNUSUAL','HIGHLY UNUSUAL']
    assert table['Reference median'].eq(4.5).all()
    assert table.iloc[-1]['Deviation from median']==45.5
    assert 'not an independently fitted detector' in method['limitation']


def test_anomaly_no_zero_imputation_and_insufficient_reference():
    dates=pd.date_range('2018-01-01',periods=10)
    frame=pd.DataFrame({'Date':dates,'Actual Demand':[1]*10,'Forecast Demand':[1,2,3,4,5,6,7,8,None,None]})
    table,_=anomalies(frame,'Forecast error')
    assert len(table)==8 and table['Valid observations'].eq(1).all()
    assert table['Observed value'].tolist()==list(range(8))
    with pytest.raises(ValueError,match='eight observed'):anomalies(frame.head(3),'Forecast error')
    with pytest.raises(ValueError,match='range is zero'):anomalies(pd.DataFrame({'Date':dates,'Sales':[1]*10}),'Sales')


def test_connected_brief_totals_match_independent_sources_and_pdf():
    service=VerifiedArtifactsService()
    frames={key:service.records(dataset=key) for key in ['delivery','demand','profitability','delivery_final']}
    brief=build(frames,{})
    assert len(brief['sources'])==4
    for source in brief['sources']:
        facts={f['label']:f['value'] for f in source['evidence']}
        actual=frames[source['family']]
        assert facts['Selected observations']==len(actual)
        if 'Sales' in actual:assert facts['Total Sales']==pytest.approx(sum(actual.Sales))
        if 'Risk Probability' in actual:assert facts['Scored observations']==actual['Risk Probability'].count()
    result=pdf(brief)
    document=pymupdf.open(stream=result,filetype='pdf');text=' '.join(page.get_text() for page in document)
    assert all(title in text for title in ['Delivery orders','Demand product/day web visits','Profitability line observations','Final-delivery line observations'])
    assert all(title in text for title in ['WHAT CHANGED','WHY IT MATTERS','WHERE','HOW LARGE','WHAT TO WATCH','WHAT TO INVESTIGATE NEXT'])
    assert 'No sum across order' in text and 'delivery-E1' in text


def test_brief_rejects_demo_or_unregistered_source():
    with pytest.raises(ValueError,match='registered source'):build({'delivery':pd.DataFrame({'Sales':[1]})},{})
    with pytest.raises(ValueError,match='registered connected'):build({'arbitrary':pd.DataFrame()},{})
