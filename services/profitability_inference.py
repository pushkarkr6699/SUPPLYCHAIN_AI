"""Fixed registered profitability model; portable fidelity checked independently of score accuracy."""
from pathlib import Path
from functools import lru_cache
from hashlib import sha256
from datetime import datetime,timezone
import json
import numpy as np
import pandas as pd
from config import ROOT
from services.profitability_data import registered,MODEL,THRESHOLD,risk_bands
from services.inference_service import _versions

MANIFEST=ROOT/'metadata/portable_profitability_registry.json'
VALIDATION=ROOT/'metadata/profitability_inference_validation.json'
PATHS={'models/profitability/DataCo_Profitability.json','models/profitability/DataCo_Profitability_Preprocessor.joblib','data/cache/profitability_conversion_probe.csv'}


def contract():
    _,source=registered(MODEL)
    data=json.loads(MANIFEST.read_text(encoding='utf-8-sig'))
    if data['source_model_sha256']!=source or data['source_model_path']!=MODEL:raise ValueError('Profitability model provenance mismatch.')
    if {a['path'] for a in data['artifacts']}!=PATHS or len(data['artifacts'])!=len(PATHS):raise ValueError('Unexpected profitability portable artifacts.')
    for row in data['artifacts']:
        path=(ROOT/row['path']).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file() or sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Profitability portable artifact changed. Revalidate before inference.')
    return data


def validated():
    data=contract();versions=_versions();report=json.loads(VALIDATION.read_text(encoding='utf-8-sig'))
    if report.get('status')!='validated' or report.get('source_model_sha256')!=data['source_model_sha256'] or report.get('artifacts')!=data['artifacts'] or report.get('packages')!=versions or report.get('features')!=data['features'] or report.get('threshold')!=THRESHOLD:raise ValueError('Profitability inference requires successful validation for the current model and runtime.')
    return data


def status():
    try:
        data=validated()
        return {'available':True,'model':'Tuned XGBoost profitability','threshold':THRESHOLD,'features':data['features'],'reason':'Original-to-portable prediction fidelity validated on 32 synthetic probes. Complete training features are required; supplied-score parity is unavailable.'}
    except (OSError,ValueError,KeyError) as exc:return {'available':False,'model':'Tuned XGBoost profitability','reason':'Profitability trained inference is unavailable: '+str(exc)}


def validate_features(frame,data):
    if frame.empty or frame.columns.duplicated().any():raise ValueError('Provide nonempty rows with unique feature column names.')
    missing=[c for c in data['features'] if c not in frame]
    if missing:raise ValueError('Missing trained profitability inputs: '+', '.join(missing))
    result=frame[data['features']].copy()
    for c in data['numeric_features']:
        result[c]=pd.to_numeric(result[c],errors='raise').astype(float)
        if not np.isfinite(result[c]).all():raise ValueError('Profitability inputs require finite numeric values: '+c)
    for c in data['categorical_features']:
        if result[c].isna().any() or not result[c].map(lambda x:isinstance(x,str) and bool(x.strip())).all():raise ValueError('Profitability inputs require nonempty text: '+c)
        result[c]=result[c].astype(object)
    if not result['Order Item Discount Rate'].between(0,1).all():raise ValueError('Discount rate must be between zero and one.')
    if not result['Order Item Quantity'].ge(0).all() or not result['Order Item Product Price'].ge(0).all():raise ValueError('Quantity and price cannot be negative.')
    return result


@lru_cache(maxsize=2)
def _load(manifest_signature):
    import joblib
    from xgboost import XGBClassifier
    pre=joblib.load(ROOT/'models/profitability/DataCo_Profitability_Preprocessor.joblib')
    classifier=XGBClassifier();classifier.load_model(ROOT/'models/profitability/DataCo_Profitability.json')
    return pre,classifier


def _probabilities(frame,data):
    pre,model=_load(json.dumps(data['artifacts'],sort_keys=True))
    if list(pre.feature_names_in_)!=data['features']:raise ValueError('Profitability preprocessing feature contract mismatch.')
    return model.predict_proba(pre.transform(frame[data['features']]))[:,1]


def predict(frame):
    from services.access_control import require
    from services.privacy import minimize
    require('predict');frame=minimize(frame)
    data=validated();features=validate_features(frame,data);prob=_probabilities(features,data)
    if not np.isfinite(prob).all() or not ((prob>=0)&(prob<=1)).all():raise ValueError('Profitability model returned invalid probabilities.')
    result=frame.copy();result['Profitability Probability']=prob;result['Loss Probability']=1-prob;result['Predicted Profitable']=prob>=THRESHOLD
    result['Profitability Risk']=risk_bands(result['Profitability Probability'])
    from services.audit_log import record
    record('model_predicted',model='profitability',rows=len(result))
    result.attrs.update(verified_artifacts=True,live_inference=True,dataset='profitability',data_source='Registered trained profitability inference on supplied complete feature rows',production_threshold=THRESHOLD,model_name='Tuned XGBoost profitability',evaluation_note='Portable conversion fidelity validated. Supplied-score parity not available; historical test ROC-AUC approximately 0.4978.')
    return result


def validate_conversion():
    data=contract();probe=pd.read_csv(ROOT/'data/cache/profitability_conversion_probe.csv')
    features=validate_features(probe,data);prob=_probabilities(features,data)
    error=float(np.abs(prob-probe['Expected Probability']).max())
    if len(probe)!=32 or error>1e-6:raise ValueError('Profitability portability fidelity failed.')
    report={'status':'validated','checked_at':datetime.now(timezone.utc).isoformat(),'source_model_sha256':data['source_model_sha256'],'artifacts':data['artifacts'],'packages':_versions(),'features':data['features'],'threshold':THRESHOLD,'probe_rows':len(probe),'max_probability_difference':error,'supplied_score_parity':False,'limitation':'The scored CSV lacks full training features. This validates conversion fidelity on synthetic probes, not source-score parity or real-world predictive quality.'}
    VALIDATION.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report

if __name__=='__main__':print(json.dumps(validate_conversion(),indent=2))
