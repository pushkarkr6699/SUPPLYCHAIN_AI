"""Reconcile supplied final delivery references without replacing main scores."""
import sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from services import final_delivery_data as data,final_delivery_inference as inference
frame=data.records();scores=data.evaluation(frame)
source=Path(r'D:\IBM Prac\DATACO FINAL')
matches=[]
for name in sorted(data.FILES|{'Final_Late_Delivery_Model.pkl'}):
    path,digest=data.registered(data.MODEL if name.endswith('.pkl') else name)
    assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest
    matches.append({'name':name,'registered_path':path.relative_to(ROOT).as_posix(),'sha256':digest})
summary=data.artifact('Late_Delivery_Final_Summary.csv')
pre,model=inference._load(json.dumps(inference.validated()['artifacts'],sort_keys=True))
features=data.artifact('Late_Delivery_Feature_Importance.csv')
names=list(pre.get_feature_names_out())
assert features.Feature.is_unique and set(features.Feature)==set(names)
assert np.allclose(features.set_index('Feature').loc[names].Importance,model.feature_importances_,atol=1e-7)
assert frame['Correct Prediction'].mean()==scores['Accuracy']
raw=pd.read_csv(data.registered('Late_Delivery_Scored_Orders.csv')[0])
report={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'files':matches,
    'source_rows':len(frame),'unique_orders':int(frame.Order.nunique()),'exact_exported_duplicates':int(raw.duplicated().sum()),
    'threshold':.56,'source_score_metrics':scores,'importance_features':len(names),'importance_matches_model':True,
    'source_score_parity':False,'main_delivery_unchanged':True,
    'limitation':data.NOTE+' Exact repeated exported observations are retained because no unique source line identifier was supplied.'}
(ROOT/'metadata/final_delivery_data_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
registry_path=ROOT/'metadata/data_registry.json';registry=json.loads(registry_path.read_text(encoding='utf-8-sig'))
for row in registry['artifacts']:
    for match in matches:
        if row['path']==match['registered_path']:
            aliases=set(row.get('source_aliases',[]));aliases.add(str(source/match['name']));row['source_aliases']=sorted(aliases)
registry_path.write_text(json.dumps(registry,indent=2)+'\n',encoding='utf-8')
model_path=ROOT/'metadata/model_registry.json';models=json.loads(model_path.read_text(encoding='utf-8-sig'))
for row in models['models']:
    if row['id']=='delivery_d3_line_item_xgboost':
        row.update(status='conversion_fidelity_validated',inference_enabled=True,features=inference.status()['features'],
            validation_report='metadata/final_delivery_inference_validation.json',portable_registry='metadata/portable_final_delivery_registry.json',
            source_score_parity=False,feature_importance='4349 transformed features match this model',
            limitation='31 complete inputs required; supplied scores omit inputs. Independent line-item grain retained.')
model_path.write_text(json.dumps(models,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
