import json
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from config import ROOT
from services import visualization_service as viz


def frame(rows=24):
    data=pd.DataFrame({'Date':pd.date_range('2018-01-01',periods=rows),'Market':['A','B']*(rows//2),'Category':['X','Y','Z']*(rows//3),'Sales':np.arange(1,rows+1,dtype=float),'Profit':np.arange(rows,dtype=float)-10,'Risk Probability':np.linspace(.1,.9,rows)})
    data.attrs.update(dataset='delivery',verified_artifacts=True,data_source='Test source')
    return data


@pytest.mark.parametrize('kind',viz.CHART_TYPES)
def test_chart_types_build_serializable_figures_without_mutating_sources(kind):
    data=frame();before=data.copy(deep=True)
    if kind in {'Coordinate map','Ordered funnel'}:
        with pytest.raises(ValueError):viz.build(data,kind,['Market','Category'],['Sales'])
        pd.testing.assert_frame_equal(data,before)
        return
    result=viz.build(data,kind,['Market','Category'],['Sales','Profit'] if kind=='Stacked bars' else ['Sales','Profit','Risk Probability'],'Sum' if kind=='Stacked bars' else 'Mean')
    assert result['figure'].data and json.loads(result['figure'].to_json())['data']
    assert result['table'].Records.sum()==len(data) and result['note']
    pd.testing.assert_frame_equal(data,before)
    assert data.attrs==before.attrs


def test_missing_values_stay_missing_and_infinite_values_are_excluded():
    data=frame();data.loc[data.Market.eq('A'),'Risk Probability']=np.nan;data.loc[0,'Sales']=np.inf
    result=viz.summary(data,['Market'],['Sales','Risk Probability'])
    a=result[result.Market.eq('A')].iloc[0]
    assert np.isnan(a['Risk Probability']) and a['Valid \u00b7 Risk Probability']==0
    assert a['Valid \u00b7 Sales']==11
    assert a.Sales==data.loc[data.Market.eq('A') & data.Sales.ne(np.inf),'Sales'].mean()


def test_composition_other_preserves_complete_record_total():
    data=frame();data['Group']=[str(i) for i in range(len(data))]
    result=viz.build(data,'Donut',['Group'],['Sales'],limit=5)
    assert len(result['shown'])==5 and result['shown'].Records.sum()==24
    assert '[Other groups]' in result['shown'].Group.values


def test_negative_composition_and_sum_probabilities_are_rejected():
    data=frame();data['Profit']=-1.
    with pytest.raises(ValueError,match='nonnegative'):viz.build(data,'Pie',['Market'],['Profit'],'Sum',size='First measure (sum)')
    with pytest.raises(ValueError,match='not additive'):viz.build(frame(),'Vertical bars',['Market'],['Risk Probability'],'Sum')


@pytest.mark.parametrize('kind,metrics,groups', [('Bubble',['Sales','Profit'],['Market']),('Scatter',['Sales'],['Market']),('Grouped heatmap',['Sales'],['Market']),('Pie',['Sales'],[])])
def test_incompatible_field_choices_have_clear_recovery(kind,metrics,groups):
    with pytest.raises(ValueError):viz.build(frame(),kind,groups,metrics)


def test_empty_selection_constant_correlations_and_nonfinite_data():
    with pytest.raises(ValueError,match='No records'):viz.build(frame().iloc[:0],'Line',[],['Sales'])
    data=frame();data['Sales']=1.;data['Profit']=2.
    with pytest.raises(ValueError,match='non-constant'):viz.build(data,'Correlation heatmap',[],['Sales','Profit'])
    data['Sales']=np.nan
    with pytest.raises(ValueError,match='no finite'):viz.build(data,'Histogram',[],['Sales'])


def test_sampling_is_deterministic_bounded_and_disclosed():
    data=frame(6000)
    first=viz.build(data,'Scatter',[],['Sales','Profit'])
    second=viz.build(data,'Scatter',[],['Sales','Profit'])
    pd.testing.assert_frame_equal(first['shown'],second['shown'])
    assert len(first['shown'])==viz.SAMPLE_LIMIT and '3,000 / 6,000' in first['note']


def test_area_does_not_stack_probabilities_and_chronology_is_sorted():
    result=viz.build(frame().iloc[::-1],'Area',['Market'],['Risk Probability'])
    assert all(not trace.stackgroup and trace.fill=='tozeroy' for trace in result['figure'].data)
    assert result['shown'].Date.is_monotonic_increasing


@pytest.mark.parametrize("mode",["demo","verified"])
def test_visualization_ui_applies_chart_choices_and_additional_datasets(monkeypatch,mode):
    import services.provider as provider
    monkeypatch.setattr(provider,"SUPPLYCHAIN_PROVIDER",mode)
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45)
    app.session_state['route']='visualizations'
    app.session_state['authenticated']=True
    app.run();assert not app.exception
    assert len(app.get('plotly_chart'))==3
    app.multiselect(key='viz_'+('demo' if mode=='demo' else 'delivery')+'_charts').set_value(['Donut','Scatter'])
    next(b for b in app.button if b.label=='Build visualizations').click().run()
    assert not app.exception and len(app.get('plotly_chart'))==2
    if mode=='demo':
        assert app.multiselect(key='visualization_extra_sources').options==[]
        return
    app.multiselect(key='visualization_extra_sources').set_value(['demand']).run()
    assert not app.exception and app.date_input(key='viz_demand_period')
    assert len(app.get('plotly_chart'))==5
    app.selectbox(key='visualizations_dataset').select('profitability').run()
    assert not app.exception and app.multiselect(key='viz_profitability_metrics')


def test_analysis_pdf_survives_rerender_and_hides_when_choices_change(monkeypatch):
    import services.provider as provider
    monkeypatch.setattr(provider,'SUPPLYCHAIN_PROVIDER','verified')
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45)
    app.session_state['route']='visualizations';app.session_state['authenticated']=True
    app.run();assert not app.exception
    app.button(key='viz_delivery_pdf_create').click().run()
    assert not app.exception and app.session_state['viz_delivery_pdf']['content'].startswith(b'%PDF')
    app.run()
    labels=[entry.proto.label for entry in app.get('download_button')]
    assert 'Download analysis PDF' in labels and app.button(key='viz_delivery_pdf_create').disabled
    app.multiselect(key='viz_delivery_charts').set_value(['Donut'])
    next(b for b in app.button if b.label=='Build visualizations').click().run()
    assert not app.exception and not app.button(key='viz_delivery_pdf_create').disabled
    assert 'Download analysis PDF' not in [entry.proto.label for entry in app.get('download_button')]


def test_demand_units_use_registered_artifact_and_bounds():
    data=pd.DataFrame({'Actual Demand':[1.],'Lower':[.2],'Upper':[2.]})
    data.attrs.update(verified_artifacts=True,artifact='AccessLogs_Final_Advanced_Forecast.csv')
    assert all(viz.units(c,data)=='web visits' for c in data)


def test_studio_axes_and_bounded_legend_leave_source_note_its_own_space(monkeypatch):
    from components import charts
    import plotly.express as px
    monkeypatch.setattr(charts.st,'session_state',{'theme':'Dark','verified_context':True})
    ordinary=charts.style(px.scatter(frame(),x='Sales',y='Profit'))
    assert ordinary.layout.xaxis.title.text is None
    studio=charts.style(px.scatter(frame(),x='Sales',y='Profit'),preserve_axis_titles=True)
    assert studio.layout.xaxis.title.text=='Sales'
    assert studio.layout.margin.b==110 and not any(a.text=='Supplied data' for a in studio.layout.annotations)
    pie=charts.style(px.pie(frame(),names='Market',values='Sales'),preserve_axis_titles=True)
    assert pie.layout.margin.b==240 and pie.layout.legend.maxheight==85
    assert pie.layout.legend.yref=='container' and not any(a.text=='Supplied data' for a in pie.layout.annotations)
