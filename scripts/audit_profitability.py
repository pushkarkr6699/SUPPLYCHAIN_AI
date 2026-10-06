"""Reconcile the supplied profitability package and record supported capabilities."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,zipfile
import numpy as np
import pandas as pd
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from services import profitability_data as data,profitability_inference as model
from services.provider import VerifiedArtifactsService
raw=data.artifact(data.SCORED);frame=data.records();checks=[]
for file in data.FILES:data.registered(file)
data.registered(data.MODEL);checks.append('All 15 source artifacts match their registered hashes')
for field,name in [('Market','Market'),('Category Name','Category'),('Shipping Mode','Shipping')]:
    ref=data.artifact('DataCo_'+name+'_Summary.csv').set_index(field)
    observed=raw.groupby(field).agg(Orders=('Order Id','size'),Actual_Profitability=('Actual_Profitable','mean'),Average_Profit=('Order Profit Per Order','mean'),Average_Prediction=('Profitability_Probability','mean'))
    assert set(ref.index)==set(observed.index)
    for col in ref:
        assert np.allclose(ref[col],observed.loc[ref.index,col],rtol=1e-5,atol=1e-5),(name,col)
checks.append('Market/category/shipping references reconcile to line-item rows, not unique orders')
ref=data.artifact('DataCo_Calibration_Check.csv')
binned=raw.assign(band=pd.cut(raw.Profitability_Probability,[0,.2,.4,.6,.8,1],include_lowest=True)).groupby('band',observed=False).agg(Records=('Order Id','size'),Average_Predicted_Probability=('Profitability_Probability','mean'),Actual_Profitability=('Actual_Profitable','mean'))
assert np.allclose(ref.Records,binned.Records)
for col in ['Average_Predicted_Probability','Actual_Profitability']:assert np.allclose(ref[col],binned[col],atol=1e-6,equal_nan=True)
checks.append('Calibration bands, row counts and observed rates reconcile')
short=data.artifact('DataCo_High_Loss_Risk_Orders.csv')
expected=raw[raw.Profitability_Risk.eq('High Loss Risk')]
assert len(short)==len(expected)==5
assert set(pd.util.hash_pandas_object(short,index=False))==set(pd.util.hash_pandas_object(expected,index=False))
checks.append('Five-row high-loss shortlist matches supplied probability bands')
drift=data.artifact('DataCo_Train_Test_Drift.csv')
calculated=(drift.Test_Mean-drift.Train_Mean).abs()/drift.Train_Mean.abs().replace(0,np.nan)
assert np.allclose(calculated,drift.Relative_Change,equal_nan=True,atol=1e-7)
checks.append('Historical drift relative changes reconcile; zero baseline remains undefined')
manifest=model.validated();pre,clf=model._load(json.dumps(manifest['artifacts'],sort_keys=True))
importance=data.artifact('DataCo_Feature_Importance.csv').set_index('Feature')
actual=pd.Series(clf.feature_importances_,index=pre.get_feature_names_out())
assert set(importance.index)==set(actual.index)
assert np.allclose(importance.Importance,actual.loc[importance.index],atol=1e-7)
checks.append('All 238 feature names and importances match the converted trained model')
scores=data.evaluation(frame);summary=data.artifact('DataCo_Final_Project_Summary.csv').set_index('Property').Value
for name,column in [('Accuracy','Accuracy'),('Precision','Precision'),('Recall','Recall'),('F1','F1'),('ROC-AUC','ROC-AUC'),('PR-AUC','PR-AUC')]:assert abs(scores[name]-float(summary[column]))<=.000051,(name,scores[name],summary[column])
checks.append('Final test metrics reconcile; all-profitable classification and weak AUC are disclosed')
joined=data.cross_risk(VerifiedArtifactsService().records(dataset='delivery'))
assert joined.Order.is_unique and len(joined)==65752
assert joined['Profitability rows'].notna().sum()==14593
checks.append('14,593 profitability order IDs join one-to-one after line aggregation and identity checks; unmatched orders remain unscored')
report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':True,'checks':checks,'line_items':len(frame),'unique_orders':frame.Order.nunique(),'metrics':scores,'high_loss_rows':5,'features':len(manifest['features']),'conversion_probe_rows':32,'supplied_score_parity':False,'live_ai_requires_key':True,'limitations':['Scored CSV omits complete training inputs; existing rows use supplied probabilities.','Saved threshold predicts all rows profitable; test AUC is approximately 0.4978.','No training notebook supplied; evaluation split procedure not independently verified.','Profitability line aggregates are not order-level probabilities or complete-order profit totals.']}
(ROOT/'metadata/profitability_data_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
registry_path=ROOT/'metadata/model_registry.json';registry=json.loads(registry_path.read_text(encoding='utf-8-sig'))
entry={'id':'profitability_tuned_xgboost','display_name':'Tuned XGBoost profitability','artifact_path':data.MODEL,'status':'conversion_fidelity_validated','inference_enabled':True,'decision_threshold':.2,'features':manifest['features'],'grain':'source line-item','supplied_score_parity':False,'validation_report':'metadata/profitability_inference_validation.json','quality_note':data.NOTE}
registry['models']=[e for e in registry['models'] if e['id']!=entry['id']]+[entry];registry_path.write_text(json.dumps(registry,indent=2)+'\n',encoding='utf-8')
cap_path=ROOT/'metadata/capability_matrix.json';caps=json.loads(cap_path.read_text(encoding='utf-8-sig'));c=caps['capabilities']
c.update(profitability={'status':'connected','rows':len(frame),'grain':'line-item','threshold':.2,'evaluation_note':data.NOTE},profitability_inference={'status':'available_with_complete_inputs','source_score_parity':False,'conversion_probe_parity':True,'required_features':manifest['features']},cross_risk_join={'status':'connected','method':'order identity validated; line items aggregated to unique orders','matched_orders':14593,'combined_model':False},drift={'status':'historical_reference_connected','source':'DataCo_Train_Test_Drift.csv','live_monitoring':False},copilot={'status':'available','implementation':'local calculations plus explicit optional Hugging Face narrative'},live_ai={'status':'implemented_requires_local_key','scope':'dashboards, profitability, comparison, Insight Center and Copilot','evidence':'aggregate-only with anonymous segment labels'})
cap_path.write_text(json.dumps(caps,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
