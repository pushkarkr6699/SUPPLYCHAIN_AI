"""Convert the trusted profitability pipeline without fitting; compare on deterministic probes."""
from pathlib import Path
from hashlib import sha256
import sys,json
import joblib,numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from services.profitability_data import registered,MODEL
path,model_hash=registered(MODEL)
model=joblib.load(path)
pre=model.named_steps['preprocessor'];classifier=model.steps[-1][1]
features=list(model.feature_names_in_)
numeric=list(pre.transformers_[0][2]);categorical=list(pre.transformers_[1][2])
num_pipeline=pre.transformers_[0][1];cat_pipeline=pre.transformers_[1][1]
values=dict(zip(numeric,num_pipeline.named_steps['imputer'].statistics_))
values.update(dict(zip(categorical,cat_pipeline.named_steps['imputer'].statistics_)))
probe=pd.DataFrame([values.copy() for _ in range(32)])
for j,name in enumerate(numeric):probe[name]=probe[name]*(1+np.linspace(-.15,.15,32))
encoder=cat_pipeline.named_steps['onehot']
for name,categories in zip(categorical,encoder.categories_):probe[name]=[str(categories[i%len(categories)]) for i in range(32)]
prob=model.predict_proba(probe[features])[:,1]
folder=ROOT/'models/profitability'
classifier.save_model(folder/'DataCo_Profitability.json')
joblib.dump(pre,folder/'DataCo_Profitability_Preprocessor.joblib')
probe['Expected Probability']=prob
probe_path=ROOT/'data/cache/profitability_conversion_probe.csv';probe_path.parent.mkdir(parents=True,exist_ok=True);probe.to_csv(probe_path,index=False)
manifest={'source_model_path':MODEL,'source_model_sha256':model_hash,'conversion':'Native XGBoost JSON and original fitted preprocessing; no retraining','features':features,'numeric_features':numeric,'categorical_features':categorical,'probe_rows':len(probe),'source_score_parity':'Unavailable: supplied scored CSV omits required training inputs','artifacts':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha256(p.read_bytes()).hexdigest()} for p in [folder/'DataCo_Profitability.json',folder/'DataCo_Profitability_Preprocessor.joblib',probe_path]]}
(ROOT/'metadata/portable_profitability_registry.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'features':features,'probe_rows':len(probe),'status':'converted'},indent=2))
