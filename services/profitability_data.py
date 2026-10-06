"""Registered profitability scores at source-row grain; never order-level duplicates."""
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import json
import numpy as np
import pandas as pd
from config import ROOT

DIRECTORY='data/profitability/final/'
MODEL='models/profitability/DataCo_Final_Trained_Model.pkl'
SCORED='DataCo_Final_Scored_Orders.csv'
FILES={SCORED,'Best_Threshold.txt','Winning_Model.txt','DataCo_Calibration_Check.csv','DataCo_CatBoost_Tuning.csv','DataCo_Category_Summary.csv','DataCo_Feature_Importance.csv','DataCo_Final_Project_Summary.csv','DataCo_High_Loss_Risk_Orders.csv','DataCo_Market_Summary.csv','DataCo_Model_Comparison.csv','DataCo_Shipping_Summary.csv','DataCo_Threshold_Analysis.csv','DataCo_Train_Test_Drift.csv'}
THRESHOLD=.20
NOTE='Historical line-item test scores. At threshold 0.20 all supplied rows predict profitable; test ROC-AUC is approximately 0.4978. Risk bands are separate descriptive probability bands.'
RENAME={'Order Id':'Order','Order Region':'Region','Order Country':'Country','Category Name':'Category','Department Name':'Department','Order_Date':'Date','Order Profit Per Order':'Profit','Actual_Profitable':'Actual Profitable','Profitability_Probability':'Profitability Probability','Predicted_Profitable':'Predicted Profitable','Correct_Prediction':'Correct Profitability Prediction','Profitability_Risk':'Profitability Risk'}


def registered(name):
    if name not in FILES and name!=MODEL:raise ValueError('Only registered profitability artifacts are supported.')
    relative=name if name==MODEL else DIRECTORY+name
    path=(ROOT/relative).resolve()
    if not path.is_relative_to(ROOT.resolve()):raise ValueError('Artifact resolves outside the project.')
    registry=json.loads((ROOT/'metadata/data_registry.json').read_text(encoding='utf-8-sig'))
    matches=[e for e in registry['artifacts'] if e['path']==relative]
    if len(matches)!=1 or not path.is_file():raise ValueError('Profitability artifact is missing or not registered: '+name)
    digest=sha256(path.read_bytes()).hexdigest()
    if digest!=matches[0]['sha256']:raise ValueError('Profitability artifact changed; revalidate before use: '+name)
    return path,digest


def risk_bands(probabilities):
    return pd.Series(np.select([probabilities.lt(.4),probabilities.lt(.7)],['High Loss Risk','Moderate Profitability'],default='High Profit Probability'),index=probabilities.index)


def validate_raw(raw):
    required=set(RENAME)|{'Market','Customer Segment','Shipping Mode','Order Item Quantity','Order Item Discount Rate','Order Item Product Price'}
    if not required.issubset(raw):raise ValueError('Profitability scored CSV is missing required columns.')
    data=raw.copy()
    if data.empty or data.columns.duplicated().any() or data.duplicated().any():raise ValueError('Profitability rows must be nonempty with no exact duplicates.')
    for col in ['Order Id','Order Profit Per Order','Profitability_Probability','Order Item Quantity','Order Item Discount Rate','Order Item Product Price','Actual_Profitable','Predicted_Profitable','Correct_Prediction']:
        data[col]=pd.to_numeric(data[col],errors='raise')
        if not np.isfinite(data[col]).all():raise ValueError('Profitability numeric values must be finite: '+col)
    if not data['Order Id'].ge(0).all() or not data['Order Id'].eq(data['Order Id'].round()).all():raise ValueError('Order IDs must be nonnegative integers.')
    p=data.Profitability_Probability
    if not p.between(0,1).all():raise ValueError('Profitability probabilities must lie in [0, 1].')
    for col in ['Actual_Profitable','Predicted_Profitable','Correct_Prediction']:
        if not data[col].isin([0,1]).all():raise ValueError('Profitability labels must be binary.')
    if not data.Actual_Profitable.eq(data['Order Profit Per Order'].gt(0).astype(int)).all():raise ValueError('Profitability target disagrees with recorded profit.')
    if not data.Predicted_Profitable.eq(p.ge(THRESHOLD).astype(int)).all():raise ValueError('Profitability prediction threshold mismatch.')
    if not data.Correct_Prediction.eq(data.Actual_Profitable.eq(data.Predicted_Profitable).astype(int)).all():raise ValueError('Profitability correctness flag mismatch.')
    if not data.Profitability_Risk.eq(risk_bands(p)).all():raise ValueError('Profitability risk band mismatch.')
    data['Order_Date']=pd.to_datetime(data.Order_Date,errors='raise')
    if data.Order_Date.isna().any():raise ValueError('Profitability dates cannot be missing.')
    if not data['Order Item Quantity'].ge(0).all() or not data['Order Item Product Price'].ge(0).all() or not data['Order Item Discount Rate'].between(0,1).all():raise ValueError('Invalid item quantity, price or discount rate.')
    return data


@lru_cache(maxsize=4)
def _records(path,digest):
    data=validate_raw(pd.read_csv(path)).rename(columns=RENAME)
    data['Order']=data.Order.astype('int64').astype(str)
    data.insert(0,'Profitability Row',[f'P{i+1:07d}' for i in range(len(data))])
    data['Loss Probability']=1-data['Profitability Probability']
    for col in ['Actual Profitable','Predicted Profitable','Correct Profitability Prediction']:data[col]=data[col].astype(bool)
    data.attrs.update(verified_artifacts=True,dataset='profitability',grain='source line-item rows; Order is not unique',data_source='DataCo supplied profitability line-item test scores',artifact=SCORED,model_name='Tuned XGBoost profitability',production_threshold=THRESHOLD,evaluation_note=NOTE,source_sha256=digest)
    return data


def records():
    path,digest=registered(SCORED)
    if float(registered('Best_Threshold.txt')[0].read_text().strip())!=THRESHOLD:raise ValueError('Profitability threshold metadata mismatch.')
    return _records(str(path),digest).copy()


def artifact(name):
    path,digest=registered(name)
    data=pd.read_csv(path)
    data.attrs.update(data_source='Supplied profitability reference: '+name,source_sha256=digest)
    return data


def evaluation(frame,threshold=THRESHOLD):
    from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,average_precision_score,balanced_accuracy_score,brier_score_loss
    if frame.empty:return {}
    y=frame['Actual Profitable'].astype(int);p=frame['Profitability Probability'];pred=p.ge(threshold).astype(int)
    return {'Accuracy':accuracy_score(y,pred),'Balanced accuracy':balanced_accuracy_score(y,pred),'Precision':precision_score(y,pred,zero_division=0),'Recall':recall_score(y,pred,zero_division=0),'F1':f1_score(y,pred,zero_division=0),'ROC-AUC':roc_auc_score(y,p) if y.nunique()==2 else None,'PR-AUC':average_precision_score(y,p) if y.nunique()==2 else None,'Brier score':brier_score_loss(y,p),'Actual profitable rate':float(y.mean()),'Predicted profitable rate':float(pred.mean())}


def cross_risk(delivery,profitability=None):
    profit=records() if profitability is None else profitability
    if delivery.Order.duplicated().any():raise ValueError('Cross-risk requires unique delivery orders.')
    identity=profit.groupby('Order').agg(Date=('Date','first'),Market=('Market','first'),Country=('Country','first'))
    if any(profit.groupby('Order')[c].nunique().gt(1).any() for c in ['Date','Market','Country']):raise ValueError('Profitability order identity is inconsistent.')
    matched=delivery[['Order','Date','Market','Country']].merge(identity.reset_index(),on='Order',suffixes=('_delivery','_profit'),validate='one_to_one')
    for c in ['Date','Market','Country']:
        if not matched[c+'_delivery'].eq(matched[c+'_profit']).all():raise ValueError('Cross-risk order identity mismatch: '+c)
    aggregate=profit.groupby('Order').agg(**{'Profitability rows':('Profitability Row','size'),'Mean line profitability':('Profitability Probability','mean'),'Maximum line loss probability':('Loss Probability','max'),'Observed losing lines':('Actual Profitable',lambda s:int((~s).sum())),'High loss risk lines':('Profitability Risk',lambda s:int(s.eq('High Loss Risk').sum()))}).reset_index()
    result=delivery.merge(aggregate,on='Order',how='left',validate='one_to_one')
    result.attrs.update(delivery.attrs,data_source='Verified order identity join: delivery orders + aggregated profitability line items',dataset='cross_risk',evaluation_note='Mean/max line probabilities are descriptive aggregates, not an order-profitability probability. No demand join.')
    return result
