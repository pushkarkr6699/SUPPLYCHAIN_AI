import numpy as np
import pandas as pd
import pytest
from services import final_delivery_data as data,final_delivery_inference as inference


def test_final_delivery_retains_line_grain_and_separate_threshold():
    frame=data.records()
    assert len(frame)==24369 and frame.Order.nunique()<len(frame)
    assert frame['Delivery Row'].is_unique
    assert frame.attrs['dataset']=='delivery_final' and frame.attrs['production_threshold']==.56
    assert frame['Predicted Late'].eq(frame['Risk Probability'].ge(.56)).all()
    assert frame['Correct Prediction'].eq(frame['Actual Late'].eq(frame['Predicted Late'])).all()
    from services.provider import VerifiedArtifactsService
    assert VerifiedArtifactsService().records(dataset='delivery').Order.is_unique


def test_final_delivery_paths_are_fixed():
    for name in ['../../.env','models/delivery/DataCo_Tuned_XGBoost.pkl']:
        with pytest.raises(ValueError):data.registered(name)


def test_final_delivery_missing_features_are_refused():
    with pytest.raises(ValueError,match='Missing trained'):
        inference.predict(data.records().head(2))


def test_final_delivery_original_conversion_fidelity():
    from config import ROOT
    probe=pd.read_csv(ROOT/'data/cache/final_delivery_conversion_probe.csv')
    result=inference.predict(probe)
    assert len(result)==32
    assert np.max(np.abs(result['Risk Probability']-probe['Expected Probability']))<1e-6
    assert result['Predicted Late'].eq(result['Risk Probability'].ge(.56)).all()
    assert inference.status()['available']


def test_final_delivery_threshold_analysis_does_not_mutate_scores():
    frame=data.records().head(500)
    saved=frame['Predicted Late'].copy()
    low,high=data.evaluation(frame,0),data.evaluation(frame,1)
    assert low['Recall']==1 and high['Recall']==0
    pd.testing.assert_series_equal(saved,frame['Predicted Late'])
