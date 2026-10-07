"""Explicit joins with null, cardinality and metric duplication safeguards."""
import numpy as np
import pandas as pd
from services.privacy import minimize

MAX_JOIN_ROWS = 200000


def inspect(left, right, left_key, right_key):
    if left_key not in left or right_key not in right:raise ValueError('Select an existing key on each side.')
    a,b=left[left_key],right[right_key]
    if pd.api.types.is_numeric_dtype(a) != pd.api.types.is_numeric_dtype(b):raise ValueError('Key types differ. Choose keys with the same definition and compatible types.')
    a_count,b_count=a.dropna().value_counts(),b.dropna().value_counts()
    shared=a_count.index.intersection(b_count.index)
    expected=sum(int(a_count[k])*int(b_count[k]) for k in shared)
    left_unique=bool(a_count.le(1).all());right_unique=bool(b_count.le(1).all())
    cardinality='one-to-one' if left_unique and right_unique else 'one-to-many' if left_unique else 'many-to-one' if right_unique else 'many-to-many'
    return {'left_rows':len(left),'right_rows':len(right),'left_null_keys':int(a.isna().sum()),'right_null_keys':int(b.isna().sum()),
            'left_unique_keys':len(a_count),'right_unique_keys':len(b_count),'left_duplicate_key_rows':int(a.dropna().duplicated().sum()),
            'right_duplicate_key_rows':int(b.dropna().duplicated().sum()),'shared_keys':len(shared),'left_matched_records':int(a_count.reindex(shared).sum()),
            'right_matched_records':int(b_count.reindex(shared).sum()),'left_unmatched_records':int(len(left)-a_count.reindex(shared).sum()),
            'right_unmatched_records':int(len(right)-b_count.reindex(shared).sum()),'expected_inner_rows':expected,'cardinality':cardinality,
            'safe_direct_join':cardinality=='one-to-one' and 0<expected<=MAX_JOIN_ROWS,
            'policy':'Null keys never match. Direct materialization requires one-to-one; aggregate child observations explicitly first to avoid duplicated parent measures.'}


def aggregate_child(right,key,metrics,operation):
    if key not in right or not metrics or len(metrics)>4 or key in metrics or any(c not in right or not pd.api.types.is_numeric_dtype(right[c]) for c in metrics):raise ValueError('Choose a key and 1-4 numeric child measures.')
    if operation not in {'Mean','Sum'}:raise ValueError('Choose Mean or Sum for child aggregation.')
    if operation=='Sum' and any('probability' in c.lower() or pd.api.types.is_bool_dtype(right[c]) for c in metrics):raise ValueError('Probabilities and Boolean proportions cannot be summed.')
    grouped=right[right[key].notna()].groupby(key,dropna=True,observed=True)
    values=grouped[metrics].sum(min_count=1) if operation=='Sum' else grouped[metrics].mean()
    result=values.rename(columns=lambda c:operation+' child '+c).join(grouped.size().rename('Child records')).reset_index()
    result.attrs.update(right.attrs,join_aggregation={'key':key,'metrics':metrics,'operation':operation})
    return result


def join(left,right,left_key,right_key):
    left,right=minimize(left),minimize(right)
    evidence=inspect(left,right,left_key,right_key)
    if not evidence['safe_direct_join']:raise ValueError('Join blocked: require overlapping one-to-one keys within 200,000 rows. Aggregate repeated child records explicitly before joining.')
    result=left[left[left_key].notna()].merge(right[right[right_key].notna()],left_on=left_key,right_on=right_key,
                                             how='inner',validate='one_to_one',suffixes=('',' [right]'))
    if len(result)!=evidence['expected_inner_rows']:raise ValueError('Join count reconciliation failed.')
    if result.memory_usage(deep=True).sum()>80*1024*1024:raise ValueError('Joined table exceeds the 80 MB analysis limit. Select smaller sources.')
    result.attrs.update(left.attrs,data_source='Explicit validated join: '+str(left.attrs.get('data_source','Left source'))+' + '+str(right.attrs.get('data_source','Right source')),
                        grain='Matched unique keys',join_evidence=evidence)
    return result
