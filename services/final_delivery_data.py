"""Independent final delivery line-item experiment, fixed registered sources."""
from functools import lru_cache
from hashlib import sha256
import json
import numpy as np
import pandas as pd
from config import ROOT
from services.verified_data import delivery_records

DIRECTORY = 'data/delivery/legacy/d3/'
MODEL = 'models/delivery/d3/Final_Late_Delivery_Model.pkl'
FILES = {'Best_Threshold.txt','Winning_Model.txt','Late_Delivery_Feature_Importance.csv',
         'Late_Delivery_Final_Summary.csv','Late_Delivery_Model_Comparison.csv',
         'Late_Delivery_Scored_Orders.csv','Late_Delivery_Threshold_Analysis.csv'}
NOTE = 'Separate historical line-item experiment at threshold 0.56. Repeated Order IDs are line observations; these scores never replace the main order-level model or join profitability automatically. Split provenance is not independently established from these eight artifacts.'


def registered(name):
    if name not in FILES and name != MODEL:
        raise ValueError('Only registered final delivery artifacts are supported.')
    relative = name if name == MODEL else DIRECTORY + name
    path = (ROOT / relative).resolve()
    entries = json.loads((ROOT/'metadata/data_registry.json').read_text(encoding='utf-8-sig'))['artifacts']
    matched = [row for row in entries if row['path'] == relative]
    if not path.is_relative_to(ROOT.resolve()) or len(matched) != 1 or not path.is_file():
        raise ValueError('Final delivery artifact is missing or unregistered.')
    digest = sha256(path.read_bytes()).hexdigest()
    if digest != matched[0]['sha256']:
        raise ValueError('Final delivery artifact changed; revalidate before use.')
    return path, digest


@lru_cache(maxsize=2)
def _records(path, digest):
    frame = delivery_records(path)
    if frame.empty or frame.Date.isna().any():
        raise ValueError('Final delivery observations require valid dates.')
    expected = np.select([frame['Risk Probability'].le(.41),frame['Risk Probability'].le(.71)],['Low','Medium'],default='High')
    if not frame.Risk.eq(expected).all():
        raise ValueError('Final delivery risk bands disagree with probabilities.')
    # Identical exported observations are retained: source has no unique line key.
    frame.insert(0,'Delivery Row',[f'D3-{i+1:07d}' for i in range(len(frame))])
    frame.attrs.update(verified_artifacts=True,dataset='delivery_final',grain='source line-item observations; Order is not unique',
        data_source='DataCo final delivery line-item scores',model_name='Final XGBoost delivery',
        source_sha256=digest,evaluation_note=NOTE)
    return frame


def records():
    if float(registered('Best_Threshold.txt')[0].read_text().strip()) != .56:
        raise ValueError('Final delivery threshold metadata mismatch.')
    path,digest = registered('Late_Delivery_Scored_Orders.csv')
    return _records(str(path),digest).copy()


def artifact(name):
    if not name.endswith('.csv'):
        raise ValueError('Choose a registered final delivery CSV.')
    path,_ = registered(name)
    return pd.read_csv(path)


def evaluation(frame, threshold=.56):
    from sklearn.metrics import accuracy_score,balanced_accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,average_precision_score,matthews_corrcoef
    if frame.empty:return {}
    actual=frame['Actual Late'];prob=frame['Risk Probability'];pred=prob.ge(threshold)
    return {'Accuracy':float(accuracy_score(actual,pred)),'Balanced accuracy':float(balanced_accuracy_score(actual,pred)),
        'Precision':float(precision_score(actual,pred,zero_division=0)),'Recall':float(recall_score(actual,pred,zero_division=0)),
        'F1':float(f1_score(actual,pred,zero_division=0)),
        'ROC-AUC':float(roc_auc_score(actual,prob)) if actual.nunique()==2 else None,
        'PR-AUC':float(average_precision_score(actual,prob)) if actual.nunique()==2 else None,
        'MCC':float(matthews_corrcoef(actual,pred))}
