"""Acceptance cases for privacy, genuine data, joins and portable workspaces."""
import io
import json
import numpy as np
import pandas as pd
import pytest
from services import upload_service as upload, privacy, relationships as rel, visualization_config as config
from services import data_profile, data_questions, decision_intelligence as decision, access_control as access
from services.export_service import csv_bytes, excel_bytes
from services.provider import VerifiedArtifactsService


def source():
    return VerifiedArtifactsService().records(dataset='delivery')


def plan():
    return {'groups':['Market'],'metrics':['Sales'],'operation':'Sum','period':'Day','limit':20,'size':'Record count',
            'charts':['Vertical bars','Histogram'],'sort_by':'Records','ascending':False}


def test_saved_settings_include_actual_filter_rules_and_selection():
    frame=VerifiedArtifactsService().records({'Market':['Europe']},dataset='delivery')
    frame.attrs['source_sha256']='original-source-version'
    exported=json.loads(config.encode(frame,'delivery',plan()))
    assert exported['source']['version']=='original-source-version'
    assert exported['selection']['records']==len(frame)
    assert exported['selection']['filters']==[{'field':'Market','values':['Europe']}]
    assert config.decode(json.dumps(exported).encode(),frame,'delivery')==plan()
    changed=VerifiedArtifactsService().records({'Market':['LATAM']},dataset='delivery')
    changed.attrs['source_sha256']='original-source-version'
    with pytest.raises(ValueError,match='different data, filters'):config.decode(json.dumps(exported).encode(),changed,'delivery')


def test_explicit_numeric_choices_respected_for_typed_imports_and_ids():
    native=pd.DataFrame({'Order Id':[101,102],'Sales':[12.0,24.0]})
    prepared=upload.prepare(native,['Sales'],explicit_types=True)
    assert pd.api.types.is_string_dtype(prepared['Order Id']) and prepared['Order Id'].tolist()==['101','102']
    assert prepared.Sales.tolist()==[12.0,24.0]
    categorical=upload.prepare(native,[],explicit_types=True)
    assert categorical.attrs['generated_measure']=='Generated record count' and categorical['Generated record count'].sum()==2
    # Prediction boards retain already validated output probabilities/types.
    assert pd.api.types.is_numeric_dtype(upload.prepare(native,[])['Sales'])


def test_password_contact_columns_and_embedded_contacts_never_export():
    frame=pd.DataFrame({'Customer Password':['do-not-display'],'Customer Email':['analyst@example.invalid'],
                        'Customer Street':['private location'],'Customer Fname':['Private'],
                        'Notes':['Contact analyst@example.invalid or 192.168.1.10'], 'Sales':[12]})
    cleaned=privacy.minimize(frame)
    assert set(cleaned)=={'Notes','Sales'}
    assert cleaned.attrs['privacy']['removed_columns']==4
    text=csv_bytes(frame).decode('utf-8-sig')
    assert all(term not in text for term in ['do-not-display','analyst@example.invalid','192.168.1.10','private location','Customer Password'])
    workbook=pd.read_excel(io.BytesIO(excel_bytes(frame)))
    assert 'Customer Password' not in workbook and '[redacted]' in workbook.Notes.iloc[0]
    assert privacy.minimize(cleaned).attrs['privacy']==cleaned.attrs['privacy']


@pytest.mark.parametrize('dtype',['object','string'])
def test_empty_text_exports_preserve_headers_without_privacy_crash(dtype):
    frame=pd.DataFrame({'Market':pd.Series([],dtype=dtype),'Sales':pd.Series([],dtype=float)})
    cleaned=privacy.minimize(frame)
    assert cleaned.empty and list(cleaned)==['Market','Sales']
    exported=pd.read_csv(io.BytesIO(csv_bytes(frame)))
    assert exported.empty and list(exported)==['Market','Sales','Source']


def test_formula_headers_and_cells_are_escaped_in_csv_and_excel():
    frame=pd.DataFrame({'=1+1':['=1+1'], 'Plain':[' @SUM(A1:A2)']})
    text=csv_bytes(frame).decode('utf-8-sig')
    assert "'=1+1" in text and "' @SUM" in text
    from openpyxl import load_workbook
    sheet=load_workbook(io.BytesIO(excel_bytes(frame)),data_only=False).active
    assert sheet['A1'].data_type!='f' and sheet['A2'].data_type!='f'


def test_sensitive_only_upload_rejected_and_ids_preserved():
    with pytest.raises(ValueError,match='No analytical columns'):upload.parse(b'Customer Password\nprivate\n','p.csv')
    frame=upload.parse(b'Customer ID,Sales,Customer Password\n001,12,private\n','p.csv')
    assert frame['Customer ID'].iloc[0]=='001' and 'Customer Password' not in frame


def test_parquet_import_keeps_actual_values_and_rejects_nested_or_corrupt():
    actual=source()[['Order','Market','Sales']].head(12)
    buffer=io.BytesIO();actual.to_parquet(buffer,index=False)
    loaded=upload.parse(buffer.getvalue(),'rows.parquet')
    pd.testing.assert_frame_equal(loaded,actual,check_dtype=False)
    nested=pd.DataFrame({'Nested':[[1,2]]});bad=io.BytesIO();nested.to_parquet(bad,index=False)
    with pytest.raises(ValueError,match='flat scalar'):upload.parse(bad.getvalue(),'rows.parquet')
    with pytest.raises(ValueError,match='Parquet'):upload.parse(b'not parquet','rows.parquet')


def test_latin1_read_and_profile_counts_are_independent():
    actual=source().head(18)[['Market','Sales']]
    loaded=upload.parse(actual.to_csv(index=False).encode('latin1'),'rows.csv',encoding='latin1')
    assert loaded.attrs['import_encoding']=='latin1'
    details=data_profile.profile(actual)
    assert details['rows']==18 and details['missing_cells']==int(actual.isna().sum().sum())
    sales=details['fields'].set_index('Field').loc['Sales']
    assert sales['Mean']==pytest.approx(sum(actual.Sales)/len(actual))


def test_registered_source_catalog_validates_every_csv_and_rejects_path():
    from services.dataset_catalog import catalog, load
    entries=catalog()
    assert len(entries)>20 and all(e['Status'] in {'READY','WARNING'} for e in entries)
    primary=next(e for e in entries if e['Name'].endswith('/ DataCo_Final_Order_Level_Dataset.csv'))
    assert primary['Rows']==65752
    with pytest.raises(ValueError):load('../../.env')


def test_real_delivery_contract_compatibility_without_scoring():
    from services.inference_service import input_rows
    data=input_rows().head(20)
    assert upload.compatibility(data,'delivery')['Compatibility']=='COMPATIBLE'
    assert upload.compatibility(data.drop(columns=['Sales']),'delivery')['Compatibility']=='PARTIAL'
    data.loc[data.index[0],'Sales']=np.nan
    assert upload.compatibility(data,'delivery')['Compatibility']=='INCOMPATIBLE'
    assert upload.compatibility(pd.DataFrame({'Unrelated':[1]}),'delivery')['Compatibility']=='UNKNOWN'


def test_current_scores_cannot_fake_complete_profitability_features():
    from services.dataset_catalog import entries,load
    key=next(a['id'] for a in entries() if 'profitability' in a['path'] and a['path'].endswith('DataCo_Final_Scored_Orders.csv'))
    check=upload.compatibility(load(key).head(15),'profitability')
    assert check['Compatibility']=='PARTIAL' and 'Department Id' in check['Missing features']


def test_unique_real_order_join_reconciles_counts_and_sales():
    left=source().head(80)[['Order','Sales']]
    right=source().iloc[30:100][['Order','Market']]
    evidence=rel.inspect(left,right,'Order','Order')
    assert evidence['shared_keys']==50 and evidence['expected_inner_rows']==50
    joined=rel.join(left,right,'Order','Order')
    assert len(joined)==50 and joined.Sales.sum()==pytest.approx(left.Sales.iloc[30:].sum())


def test_child_aggregation_prevents_parent_sales_duplication_and_null_matches():
    left=source().head(4)[['Order','Sales']]
    children=pd.concat([left[['Order']].assign(Quantity=1),left[['Order']].assign(Quantity=2)],ignore_index=True)
    assert rel.inspect(left,children,'Order','Order')['cardinality']=='one-to-many'
    with pytest.raises(ValueError,match='Join blocked'):rel.join(left,children,'Order','Order')
    aggregated=rel.aggregate_child(children,'Order',['Quantity'],'Sum')
    joined=rel.join(left,aggregated,'Order','Order')
    assert joined.Sales.sum()==pytest.approx(left.Sales.sum()) and joined['Sum child Quantity'].tolist()==[3]*4
    a=pd.DataFrame({'Key':['a',None],'Sales':[1,2]});b=pd.DataFrame({'Key':['a',None],'Count':[3,4]})
    evidence=rel.inspect(a,b,'Key','Key')
    assert evidence['expected_inner_rows']==1 and evidence['left_null_keys']==1 and len(rel.join(a,b,'Key','Key'))==1


@pytest.mark.parametrize('case',['many','none','types'])
def test_invalid_joins_are_blocked_before_materialization(case):
    left=pd.DataFrame({'Key':['a','a'] if case=='many' else ['a'],'Sales':[1,2] if case=='many' else [1]})
    right=pd.DataFrame({'Key':['a','a'] if case=='many' else ['b'] if case=='none' else [1]})
    with pytest.raises(ValueError):rel.join(left,right,'Key','Key')


def test_probability_child_sum_cannot_be_an_exposure():
    with pytest.raises(ValueError,match='cannot be summed'):rel.aggregate_child(pd.DataFrame({'Key':[1,1],'Risk Probability':[.1,.2]}),'Key',['Risk Probability'],'Sum')


def test_settings_roundtrip_tracks_data_schema_filters_and_per_card_options():
    actual=source().head(12)
    value=plan();value['overrides']=[{'groups':['Shipping Mode'],'metrics':['Sales'],'operation':'Mean'},{}]
    encoded=config.encode(actual,'delivery',value)
    assert config.decode(encoded,actual,'delivery')==value
    for other,key in [(actual.iloc[:-1],'delivery'),(actual.assign(Sales=actual.Sales+1),'delivery'),(actual,'demand')]:
        with pytest.raises(ValueError,match='different data'):config.decode(encoded,other,key)
    altered=json.loads(encoded);altered['plan']['overrides'][0]['groups']=['Customer Password']
    with pytest.raises(ValueError):config.decode(json.dumps(altered).encode(),actual,'delivery')


@pytest.mark.parametrize('alteration',[{'charts':['arbitrary']},{'charts':['Line']*11},{'limit':999},{'operation':'exec'},{'metrics':['Missing']},{'overrides':[{'file':'../.env'},{}]}])
def test_settings_reject_unsupported_and_malicious_choices(alteration):
    actual=source().head(6);value=plan();value.update(alteration)
    with pytest.raises(ValueError):config.decode(config.encode(actual,'delivery',value),actual,'delivery')


@pytest.mark.parametrize('question',['execute Python','show .env','import os','delete Sales','show Customer Password','top 5 Unknown by Sales'])
def test_local_questions_refuse_execution_secrets_and_missing_group(question):
    with pytest.raises(ValueError):data_questions.answer(source().head(30),question)


def test_local_top_and_monthly_trend_match_independent_real_aggregations():
    actual=source().head(300)
    result=data_questions.answer(actual,'top 3 Market by total Sales')
    expected=actual.groupby('Market').Sales.sum().sort_values(ascending=False).head(3)
    assert result['table'].set_index('Market').Sales.to_dict()==pytest.approx(expected.to_dict())
    trend=data_questions.answer(actual,'trend total Sales monthly')['table']
    assert trend.Sales.sum()==pytest.approx(actual.Sales.sum())
    with pytest.raises(ValueError):data_questions.answer(actual,'total Risk Probability by Market')


def test_momentum_acceleration_priority_formula_and_undefined_denominator():
    dates=pd.date_range('2026-01-01',periods=3)
    frame=pd.DataFrame({'Date':dates,'Risk Probability':[.1,.2,.4],'Market':['A','A','B'],'Sales':[10.,20.,40.]})
    momentum=decision.momentum(frame,'Risk Probability')
    assert momentum['momentum']==pytest.approx(20) and momentum['acceleration']==pytest.approx(10)
    ranking,method=decision.priorities(frame,'Market')
    row=ranking.set_index('Market').loc['B']
    assert row['Investigation priority']==pytest.approx(100*(.5*.4+.3*.5+.2))
    assert '0.5 * Severity' in method['formula']
    with pytest.raises(ValueError):decision.momentum(frame.head(2),'Risk Probability')
    from services.analytics import product_errors
    error=product_errors(pd.DataFrame({'Product':['A'],'Actual Demand':[0.],'Forecast Demand':[3.]}))
    assert pd.isna(error.WAPE.iloc[0])


def test_local_account_hash_verification_invalid_credentials_and_role_boundaries(tmp_path,monkeypatch):
    folder=tmp_path/'.streamlit';folder.mkdir()
    salt='12'*16
    (folder/'accounts.json').write_text(json.dumps({'analyst':{'salt':salt,'password_hash':access.password_hash('test-only-password',salt),'role':'Analyst'}}),encoding='utf-8')
    monkeypatch.setattr(access,'ROOT',tmp_path)
    assert access.authenticate('ANALYST','test-only-password')['user_role']=='Analyst'
    assert access.authenticate('analyst','wrong') is None and access.authenticate('unknown','wrong') is None
    assert not access.allowed('export','Viewer') and not access.allowed('predict','Executive')
    assert access.allowed('export','Analyst') and not access.allowed('project_data','Analyst','demo')


def test_analysis_report_readable_and_contains_actual_totals_not_passwords():
    from services.analysis_report import create
    import pymupdf
    actual=source().head(6);actual['Customer Password']='do-not-display'
    content=create(actual,'delivery',plan())
    text=''.join(p.get_text() for p in pymupdf.open(stream=content,filetype='pdf'))
    assert 'Analysis Brief' in text and '6 selected records' in text and 'do-not-display' not in text


def test_server_roles_suppress_download_urls_and_model_execution(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from config import ROOT
    import services.provider as provider
    monkeypatch.setenv('SUPPLYCHAIN_AUTH_MODE','accounts')
    monkeypatch.setattr(provider,'SUPPLYCHAIN_PROVIDER','verified')
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=50)
    for key,value in {'authenticated':True,'auth_kind':'account','user_role':'Viewer','route':'visualizations','route_initialized':True}.items():app.session_state[key]=value
    app.run()
    assert not app.exception and not app.error and len(app.get('plotly_chart'))==3
    assert len(app.get('download_button'))==0
    assert app.button(key='viz_delivery_pdf_create').disabled
    app.session_state['route']='downloads';app.run()
    assert not app.exception and any('role does not allow' in x.value for x in app.warning)
    app.session_state['route']='scenarios';app.run()
    assert not app.exception and any('requires an Analyst' in x.value for x in app.info)


def test_account_mode_demo_cannot_read_project_sources(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from config import ROOT
    import services.provider as provider
    monkeypatch.setenv('SUPPLYCHAIN_AUTH_MODE','accounts')
    monkeypatch.setattr(provider,'SUPPLYCHAIN_PROVIDER','verified')
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=50)
    for key,value in {'authenticated':True,'auth_kind':'demo','user_role':'Analyst','route':'overview','route_initialized':True}.items():app.session_state[key]=value
    app.run()
    assert not app.exception and not app.error
    assert any('DEMO' in str(x.value).upper() for x in app.markdown)


def test_chart_edit_duplicate_reorder_remove_reset_and_ten_slots(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from config import ROOT
    import services.provider as provider
    monkeypatch.setattr(provider,'SUPPLYCHAIN_PROVIDER','verified')
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=50)
    for key,value in {'authenticated':True,'route':'visualizations','route_initialized':True}.items():app.session_state[key]=value
    app.run()
    app.button(key='viz_delivery_duplicate_0').click().run()
    assert not app.error and len(app.get('plotly_chart'))==4
    app.multiselect(key='viz_delivery_edit_groups_1').set_value(['Shipping Mode'])
    app.selectbox(key='viz_delivery_edit_1').set_value('Horizontal bars')
    app.button(key='viz_delivery_edit_apply_1').click().run()
    assert not app.error and app.session_state['viz_delivery_plan']['overrides'][1]['groups']==['Shipping Mode']
    app.button(key='viz_delivery_move_1').click().run()
    assert app.session_state['viz_delivery_plan']['charts'][0]=='Horizontal bars'
    app.button(key='viz_delivery_remove_0').click().run()
    assert not app.error and len(app.get('plotly_chart'))==3
    chosen=['Vertical bars','Horizontal bars','Line','Area','Scatter','Histogram','Box plot','Violin plot','ECDF','Donut']
    app.multiselect(key='viz_delivery_charts').set_value(chosen)
    next(b for b in app.button if b.label=='Build visualizations').click().run()
    assert not app.exception and not app.error and len(app.get('plotly_chart'))==10
    app.button(key='viz_delivery_reset').click().run()
    assert not app.error and len(app.get('plotly_chart'))==3


def test_waterfall_additive_contributions_reconcile_with_independent_totals():
    from services.comparison_service import additive_contributions
    actual=source().head(100)
    a,b=actual.iloc[50:],actual.iloc[:50]
    contributions=additive_contributions(a,b,'Market','Sales')
    assert contributions.Contribution.sum()==pytest.approx(a.Sales.sum()-b.Sales.sum())
    with pytest.raises(ValueError):additive_contributions(a,b,'Market','Risk Probability')


def test_uploaded_floating_sevika_uses_local_context_and_requires_external_consent(monkeypatch):
    from services import sevika,ai_provider
    actual=source().head(40)[['Market','Sales']].copy()
    actual.columns=['Private Group Name','Private Amount']
    actual.attrs.update(uploaded=True,dataset='uploaded',data_source='Session upload')
    context=sevika.build_context(actual,'uploads','uploaded')
    answer,facts=sevika.answer('top 3 Private Group Name by total Private Amount',context)
    assert 'top-N' in answer['answer'] and facts
    with pytest.raises(ValueError,match='file-specific'):sevika.answer('Summarize this selection.',context,'Live AI')
    context['upload_consent']=True
    def provider(messages,schema):
        payload=json.loads(messages[-1]['content'])
        assert 'Private Group Name' not in json.dumps(payload) and 'Private Amount' not in json.dumps(payload)
        return json.dumps({'answer':'Evidence reviewed.','evidence_ids':['E1'],'follow_ups':[]})
    monkeypatch.setattr(ai_provider,'generate',provider)
    answer,_=sevika.answer('Summarize this selection.',context,'Live AI')
    assert answer['answer']=='Evidence reviewed.'


def test_ordered_funnel_and_coordinate_validation_never_invent_fields():
    from services import visualization_service as viz
    stages=pd.DataFrame({'Stage':['Placed','Shipped'],'Stage Order':[1,2],'Count':[10,8]})
    result=viz.build(stages,'Ordered funnel',['Stage'],['Count'],'Sum')
    assert list(result['figure'].data[0].x)==[10,8]
    with pytest.raises(ValueError):viz.build(stages.drop(columns='Stage Order'),'Ordered funnel',['Stage'],['Count'],'Sum')
    with pytest.raises(ValueError):viz.build(stages.assign(**{'Stage Order':[1,1]}),'Ordered funnel',['Stage'],['Count'],'Sum')
    # Coordinates are validation fixtures only, never built-in business records.
    points=pd.DataFrame({'Latitude':[10.,200.],'Longitude':[20.,30.],'Count':[1.,2.]})
    result=viz.build(points,'Coordinate map',[],['Count'])
    assert len(result['shown'])==1 and result['shown'].Latitude.iloc[0]==10
