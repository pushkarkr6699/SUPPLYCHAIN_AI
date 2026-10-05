"""Remeasure registered files and source consistency without altering outputs."""
from pathlib import Path
from hashlib import sha256
import json
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
registry=json.loads((ROOT/"metadata/data_registry.json").read_text(encoding="utf-8"))
profiles=[]
for item in registry["artifacts"]:
    path=ROOT/item["path"]
    assert path.is_file() and sha256(path.read_bytes()).hexdigest()==item["sha256"],item["path"]
    profile={"path":item["path"],"role":item["role"],"status":"present/readable/hash matches"}
    if path.suffix.lower()==".csv":
        frame=pd.read_csv(path)
        profile.update(rows=len(frame),columns=len(frame.columns),schema={column:str(dtype) for column,dtype in frame.dtypes.items()},
                       null_cells=int(frame.isna().sum().sum()),duplicate_rows=int(frame.duplicated().sum()),
                       nonfinite_numeric_cells=int(np.isinf(frame.select_dtypes(include="number")).sum().sum()))
        for column in ("Order_Date","DateOnly"):
            if column in frame:
                dates=pd.to_datetime(frame[column],errors="raise")
                profile["date_range"]={"column":column,"start":str(dates.min()),"end":str(dates.max()),"missing":int(dates.isna().sum())}
        if "Order Id" in frame:
            profile["identifier_integrity"]={"unique_orders":int(frame["Order Id"].nunique()),"missing_ids":int(frame["Order Id"].isna().sum()),"duplicate_ids":int(frame["Order Id"].duplicated().sum())}
        if {"Product","DateOnly"}.issubset(frame):
            profile["product_day_integrity"]={"products":int(frame.Product.nunique()),"duplicate_keys":int(frame.duplicated(["Product","DateOnly"]).sum())}
        if "Risk_Level" in frame: profile["risk_counts"]=frame.Risk_Level.value_counts().to_dict()
        if "Prediction_Model" in frame: profile["model_identifiers"]=frame.Prediction_Model.unique().tolist()
        if "Decision_Threshold" in frame: profile["decision_thresholds"]=frame.Decision_Threshold.unique().tolist()
    profiles.append(profile)
primary=pd.read_csv(ROOT/"data/delivery/final/DataCo_Final_Order_Level_Dataset.csv")
scored=pd.read_csv(ROOT/"data/delivery/final/DataCo_Final_Scored_Orders.csv")
earlier=pd.read_csv(ROOT/"data/delivery/final/DataCo_Late_Delivery_Predictions.csv")
assert len(primary)==65752 and len(scored)==2123 and primary["Order Id"].is_unique and scored["Order Id"].is_unique
assert scored["Order Id"].isin(primary["Order Id"]).all()
assert np.array_equal(scored.Predicted_Late_Delivery,scored.Late_Delivery_Probability.ge(.35).astype(int))
assert scored.Risk_Level.eq(np.select([scored.Late_Delivery_Probability<.4,scored.Late_Delivery_Probability<.7],["Low Risk","Medium Risk"],default="High Risk")).all()
aligned=scored.merge(earlier,on="Order Id",suffixes=("_final","_earlier"),validate="one_to_one")
comparison={"aligned_order_ids":len(aligned),"earlier_rows":len(earlier),"earlier_reference_is_active":False}
comparison["different_probabilities"]=int(np.count_nonzero(~np.isclose(aligned.Late_Delivery_Probability,aligned.Late_Risk_Probability,rtol=1e-7,atol=1e-7)))
comparison["different_predicted_labels"]=int(aligned.Predicted_Late_Delivery.ne(aligned.Predicted_Late_Risk).sum())
report={"artifacts_verified":len(profiles),"profiles":profiles,"active_delivery":{"rows":len(primary),"scored_rows":len(scored),"matching_unique_scored_orders":len(scored),"unscored_orders":len(primary)-len(scored),"threshold":.35,"model":"Tuned XGBoost"},"earlier_prediction_reference":comparison,"notes":["Earlier Random Forest predictions are a distinct reference, not final tuned scores","Demand units are web visits; DateOnly is base date and target is following day","d3 line-item delivery is preserved separately; not a one-to-one source","Demand comparison XGBoost classification row is an export defect, excluded from regression comparison"]}
(ROOT/"metadata/dataset_audit.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps({key:value for key,value in report.items() if key!="profiles"},indent=2))
