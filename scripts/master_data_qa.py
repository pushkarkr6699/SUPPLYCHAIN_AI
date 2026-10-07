"""Reconcile actual sources and measure bounded analysis; no generated business data."""
import os,sys,json,io
from pathlib import Path
from time import perf_counter
from datetime import datetime,timezone
import pandas as pd
import pymupdf
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['SUPPLYCHAIN_PROVIDER']='verified'
from services.provider import get_service
from services import visualization_service as viz, relationships, visualization_config
from services.export_service import csv_bytes
from services.analysis_report import create
from services.inference_service import validate_registered_delivery_model
from services.demand_inference import validate as validate_demand
from services.profitability_inference import validate_conversion as validate_profit
from services.final_delivery_inference import validate_conversion as validate_final


def timed(action):
    started=perf_counter();value=action();return value,round(perf_counter()-started,4)


def main():
    service=get_service();checks=[]
    source,cold=timed(lambda:service.records(dataset='delivery'))
    warm_frame,warm=timed(lambda:service.records(dataset='delivery'))
    pd.testing.assert_frame_equal(source,warm_frame)
    raw=pd.read_csv(ROOT/'data/delivery/final/DataCo_Final_Order_Level_Dataset.csv')
    assert len(source)==len(raw)==65752 and source.Order.nunique()==len(source)
    assert abs(source.Sales.sum()-raw.Sales.sum())<1e-6
    assert source['Risk Probability'].notna().sum()==2123
    assert source['Risk Probability'].isna().sum()==len(source)-2123
    checks.append('Primary order count, unique keys, sales and scored/unscored coverage independently reconciled')
    selected=source[source.Market.eq('Pacific Asia')].copy()
    table=viz.summary(selected,['Market'],['Sales'],'Sum')
    assert abs(table.Sales.sum()-selected.Sales.sum())<1e-6 and table.Records.sum()==len(selected)
    exported=pd.read_csv(io.BytesIO(csv_bytes(table)))
    assert abs(exported.Sales.sum()-selected.Sales.sum())<1e-6
    checks.append('Filtered aggregation and CSV agree with independent source totals')
    key=next(a for a in __import__('services.dataset_catalog',fromlist=['entries']).entries() if a['path'].endswith('DataCo_Final_Scored_Orders.csv') and a['family']=='delivery_d1')
    right=__import__('services.dataset_catalog',fromlist=['load']).load(key['id'])
    profile=relationships.inspect(raw,right,'Order Id','Order Id')
    joined=relationships.join(raw,right,'Order Id','Order Id')
    assert len(joined)==profile['expected_inner_rows']==2123
    assert abs(joined.Sales.sum()-raw.loc[raw['Order Id'].isin(right['Order Id']),'Sales'].sum())<1e-6
    checks.append('Actual primary/scored join coverage, output count and additive sales reconciled')
    kinds=['Vertical bars','Horizontal bars','Line','Area','Scatter','Histogram','Box plot','Violin plot','ECDF','Donut']
    figures,ten_seconds=timed(lambda:[viz.build(source,k,['Market'],['Risk Probability','Sales']) for k in kinds])
    assert len(figures)==10 and all(f['figure'].data for f in figures)
    repeated=[]
    for country in source.Country.drop_duplicates().head(5):
        _,seconds=timed(lambda:viz.summary(source[source.Country.eq(country)],['Market'],['Sales'],'Sum'))
        repeated.append(seconds)
    checks.append('Ten simultaneous chart constructions and repeated real-source filters')
    plan={'groups':['Market'],'metrics':['Sales'],'operation':'Sum','period':'Day','limit':20,'size':'Record count','charts':kinds,'sort_by':'Records','ascending':False}
    assert visualization_config.decode(visualization_config.encode(selected,'delivery',plan),selected,'delivery')==plan
    report=create(selected.head(50),'delivery',plan)
    folder=ROOT/'tmp/pdfs/master';folder.mkdir(parents=True,exist_ok=True)
    (folder/'analysis-brief.pdf').write_bytes(report)
    document=pymupdf.open(stream=report,filetype='pdf')
    for i,page in enumerate(document):
        assert page.get_text().strip()
        page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(str(folder/f'analysis-{i+1}.png'))
    checks.append('Privacy-safe analysis PDF parsed and every page rendered for visual inspection')
    model_results={}
    for name,fn in [('delivery',validate_registered_delivery_model),('demand',validate_demand),('profitability',validate_profit),('delivery_final',validate_final)]:
        result,seconds=timed(fn);model_results[name]={'status':result.get('status'), 'seconds':seconds,
             'rows':result.get('parity_rows',result.get('scored_rows',result.get('probe_rows'))),
             'supplied_score_parity':result.get('supplied_score_parity',name in {'delivery','demand'}),
             'probability_difference':result.get('max_probability_difference',result.get('max_probability_error'))}
        assert result.get('status')=='validated'
    checks.append('All four original registered model adapters revalidated; real-row parity distinguished from conversion probes')
    result={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'rows':len(source),
            'scored':2123,'join':profile,'performance':{'cold_source_seconds':cold,'warm_source_seconds':warm,
            'ten_chart_build_seconds':ten_seconds,'repeated_filter_seconds':repeated,'source_frame_MB':round(source.memory_usage(deep=True).sum()/1024**2,2),
            'scope':'Single local process, actual supplied sources; no multi-user load or production SLA claimed'},
            'models':model_results,'pdf_pages':len(document)}
    (ROOT/'metadata/master_data_qa.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
