"""Aggregate-only evidence for optional live AI across connected datasets."""
from services import parameter_comparison as analysis
from services import ai_narration


def context(frame,question='Explain the most important findings and limitations.'):
    if frame.empty:raise ValueError('No matching data is available for insights.')
    if 'Profitability Probability' in frame:
        metrics=['Profitability Probability','Loss Probability','Profit','Actual Profitable']
    elif frame.attrs.get('dataset') == 'delivery_final':
        metrics=['Risk Probability','Actual Late','Predicted Late','Correct Prediction']
    elif 'Risk Probability' in frame:
        metrics=['Risk Probability','Sales','Profit']
    else:metrics=['Forecast Demand','Actual Demand','Absolute Error']
    metrics=[c for c in metrics if c in frame]
    dimension=next((c for c in ['Market','Category','Shipping Mode'] if c in frame and frame[c].nunique()>1),None)
    params={'dimensions':[dimension] if dimension else [],'metrics':metrics,'operation':'Mean','question':question}
    table=analysis.comparison(frame,params['dimensions'],metrics)
    facts=analysis.evidence(frame,table,params['dimensions'],metrics,'Mean')
    if 'Profitability Probability' in frame:
        from services.profitability_data import evaluation,NOTE
        for name,value in evaluation(frame).items():
            if value is not None:facts.append({'id':f'E{len(facts)+1}','title':name,'text':f'{name}: {value:.6g} on the selected line-item rows.','metric':name,'value':float(value),'segment':None})
        limitation=NOTE
    else:limitation=frame.attrs.get('evaluation_note','Historical observations; no causal or future guarantees.')
    payload=analysis.narration_payload(facts,params,'Verified historical '+frame.attrs.get('dataset','data') if frame.attrs.get('verified_artifacts') else 'Synthetic demonstration data')
    payload.update(focus=question,limitations=limitation,grain=frame.attrs.get('grain','Dataset observations'))
    token=analysis.signature(frame,dict(params,model=ai_narration.status()['model']))
    return facts,payload,token
