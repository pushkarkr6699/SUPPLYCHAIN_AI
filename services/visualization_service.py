"""Bounded, read-only chart construction for connected dataset fields."""
import numpy as np
import pandas as pd
import plotly.express as px
from services import parameter_comparison as analysis

CHART_TYPES = ['Vertical bars','Horizontal bars','Line','Area','Scatter','Bubble','Histogram','Box plot','Violin plot','ECDF','Correlation heatmap','Density heatmap','Grouped heatmap','Treemap','Sunburst','Pie','Donut','Scatter matrix']
SAMPLE_LIMIT = 3000
COMPOSITION = {'Treemap','Sunburst','Pie','Donut'}


def units(field, frame):
    if 'Probability' in field or pd.api.types.is_bool_dtype(frame[field]):return 'fraction (0-1)'
    if field in {'Forecast Demand','Actual Demand','Forecast Error','Absolute Error','Lower','Upper','Lower Bound','Upper Bound'}:
        return 'web visits' if frame.attrs.get('verified_artifacts') and (frame.attrs.get('dataset')=='demand' or frame.attrs.get('artifact')=='AccessLogs_Final_Advanced_Forecast.csv') else 'source demand units'
    if field in {'Sales','Profit','Discount Value'}:return 'source monetary units'
    return 'source units'


def validate(frame, groups, metrics, operation, limit):
    if frame.empty:raise ValueError('No records match this selection. Broaden the date range or reset filters.')
    if not metrics or len(metrics)>4 or len(groups)>2:raise ValueError('Choose 1-4 numeric measures and up to two grouping fields.')
    if len(set(groups+metrics))!=len(groups+metrics):raise ValueError('Use each field once: grouping fields cannot also be measures.')
    if any(c not in frame for c in groups+metrics):raise ValueError('A chosen field is unavailable in this dataset.')
    if any(not pd.api.types.is_numeric_dtype(frame[c]) for c in metrics):raise ValueError('Choose numeric dataset measures.')
    if operation not in analysis.OPERATIONS or not 5<=limit<=50:raise ValueError('Choose a supported calculation and 5-50 visible groups.')
    if operation=='Sum' and any('Probability' in c or pd.api.types.is_bool_dtype(frame[c]) for c in metrics):
        raise ValueError('Probabilities and Boolean flags are not additive. Choose Mean for proportions or select additive measures for Sum.')


def summary(frame, groups, metrics, operation='Mean', period='Day', limit=20):
    validate(frame,groups,metrics,operation,limit)
    return analysis.comparison(frame,groups,metrics,operation,period)


def composition_table(table, groups, metrics, operation, size, limit):
    if not groups:raise ValueError('Choose a grouping field for a composition chart.')
    if size=='Record count':column='Records';note='Slice/area size is record count, not an average probability.'
    elif size=='First measure (sum)':
        if operation!='Sum':raise ValueError('First-measure composition requires Sum; choose Record count for other calculations.')
        column=metrics[0];note='Slice/area size is the sum of '+column+'.'
    else:raise ValueError('Choose a supported composition size.')
    data=table.copy();values=pd.to_numeric(data[column],errors='coerce')
    if values.lt(0).any():raise ValueError('Composition requires nonnegative amounts. Use bars or a distribution for negative values.')
    data=data.loc[values.notna() & values.gt(0)].copy()
    if data.empty:raise ValueError('No positive composition values are available; missing values are not zeros.')
    for group in groups:data[group]=data[group].astype('string').fillna('(Missing)').astype(str)
    data=data.sort_values(column,ascending=False,kind='stable')
    if len(data)>limit:
        keep=data.head(limit-1).copy();tail=data.iloc[limit-1:]
        other={c:'[Other groups]' for c in groups};other[column]=tail[column].sum();other['Records']=tail.Records.sum()
        data=pd.concat([keep,pd.DataFrame([other])],ignore_index=True)
        note+=' Remaining groups are combined as [Other groups], preserving the total.'
    data['Segment']=analysis.segment_labels(data,groups)
    return data,column,note


def build(frame, kind, groups, metrics, operation='Mean', period='Day', limit=20, size='Record count'):
    if kind not in CHART_TYPES:raise ValueError('Choose an available chart type.')
    table=summary(frame,groups,metrics,operation,period,limit)
    sampled=frame.sample(min(SAMPLE_LIMIT,len(frame)),random_state=42)
    clean=analysis.clean_numeric(sampled,metrics)
    axes={c:c+' ('+units(c,frame)+')' for c in metrics}
    note=''
    if kind in COMPOSITION:
        data,column,note=composition_table(table,groups,metrics,operation,size,limit)
        if kind in {'Pie','Donut'}:
            fig=px.pie(data,names='Segment',values=column,hole=.55 if kind=='Donut' else 0)
            fig.update_traces(textinfo='percent',hovertemplate='%{label}<br>%{value:,.6g}<br>%{percent}<extra></extra>')
        else:
            fig=(px.treemap if kind=='Treemap' else px.sunburst)(data,path=groups,values=column)
        shown=data
    elif kind in {'Vertical bars','Horizontal bars'}:
        data=table.sort_values('Records',ascending=False,kind='stable').head(limit).copy()
        data['Segment']=analysis.segment_labels(data,groups)
        long=data.melt(id_vars=['Segment','Records'],value_vars=metrics,var_name='Measure',value_name='Value').dropna(subset=['Value'])
        if long.empty:raise ValueError('No finite values for these measures. Missing scores are not plotted as zeros.')
        horizontal=kind=='Horizontal bars'
        fig=px.bar(long,x='Value' if horizontal else 'Segment',y='Segment' if horizontal else 'Value',orientation='h' if horizontal else 'v',facet_col='Measure',facet_col_wrap=1,hover_data=['Records'])
        fig.update_xaxes(matches=None);fig.update_yaxes(matches=None)
        note=f'{operation} in original field units, in separate measure panels. Largest {len(data):,} of {len(table):,} groups by record count.'
        shown=data
    elif kind in {'Line','Area'}:
        if 'Date' not in frame:raise ValueError('Time charts require a Date field in the connected dataset.')
        dims=[c for c in groups if c!='Date']
        data=analysis.comparison(frame,['Date',*dims],metrics,operation,period)
        data['Series']=analysis.segment_labels(data,dims)
        series=data.groupby('Series',sort=False).Records.sum().nlargest(min(limit,12)).index
        dates=sorted(data.Date.dropna().unique())[-180:]
        data=data[data.Series.isin(series) & data.Date.isin(dates)].sort_values('Date',kind='stable')
        long=data.melt(id_vars=['Date','Series','Records'],value_vars=metrics,var_name='Measure',value_name='Value').dropna(subset=['Value'])
        if long.empty:raise ValueError('No measured time-series values in this period.')
        fig=px.line(long,x='Date',y='Value',color='Series',facet_col='Measure',facet_col_wrap=1,markers=True,hover_data=['Records'])
        if kind=='Area':fig.update_traces(fill='tozeroy',opacity=.45)
        fig.update_yaxes(matches=None)
        note=f'{operation} per {period.lower()}, separate measure panels; at most 12 series and the latest 180 time bins. Areas overlap without stacking means.'
        shown=data
    elif kind in {'Histogram','Box plot','Violin plot','ECDF'}:
        long=clean.melt(var_name='Measure',value_name='Value').dropna()
        if long.empty:raise ValueError('These measures contain no finite values in the selected records.')
        kwargs={'data_frame':long,'facet_col':'Measure','facet_col_wrap':1}
        if kind=='Histogram':fig=px.histogram(**kwargs,x='Value',nbins=30,labels={'Value':'Value (original field units)'})
        elif kind=='ECDF':fig=px.ecdf(**kwargs,x='Value',labels={'Value':'Value (original field units)'})
        elif kind=='Box plot':fig=px.box(**kwargs,y='Value',points=False)
        else:fig=px.violin(**kwargs,y='Value',box=True,points=False)
        fig.update_xaxes(matches=None);fig.update_yaxes(matches=None)
        note=f'Distribution of a deterministic sample of {len(sampled):,} / {len(frame):,} records. Each panel retains its own field units; missing/non-finite values are excluded.'
        shown=clean
    elif kind=='Correlation heatmap':
        if len(metrics)<2:raise ValueError('Select at least two measures for correlation.')
        matrix=analysis.clean_numeric(frame,metrics).corr(min_periods=3)
        if matrix.notna().sum().sum()<=len(metrics):raise ValueError('Correlation requires non-constant fields and at least three paired finite values.')
        fig=px.imshow(matrix,text_auto='.2f',zmin=-1,zmax=1,color_continuous_scale='RdBu_r',aspect='auto')
        note='Pearson correlation uses all matching records and at least three paired finite values. Association is not causation; missing correlations remain gaps.'
        shown=matrix
    elif kind=='Grouped heatmap':
        if len(groups)!=2:raise ValueError('Choose exactly two grouping fields for a grouped heatmap.')
        data=table.sort_values('Records',ascending=False,kind='stable').head(limit).copy()
        for c in groups:data[c]=data[c].astype('string').fillna('(Missing)')
        matrix=data.pivot(index=groups[0],columns=groups[1],values=metrics[0])
        if not matrix.notna().any().any():raise ValueError('No finite values for the first measure in these groups.')
        fig=px.imshow(matrix,text_auto='.3g',aspect='auto',color_continuous_scale='Blues',labels={'color':operation+' '+metrics[0]})
        note=f'{operation} of {metrics[0]} ({units(metrics[0],frame)}), largest {len(data)} grouped cells by record count. Missing cells are gaps.'
        shown=matrix
    else:
        if len(metrics)<2:raise ValueError('Select at least two numeric measures for this chart.')
        if kind=='Scatter matrix':
            data=clean.dropna()
            if data.empty:raise ValueError('No rows have finite values for every selected measure.')
            fig=px.scatter_matrix(data,dimensions=metrics,labels=axes,opacity=.35)
            fig.update_traces(diagonal_visible=False)
        else:
            selected=metrics[:3] if kind=='Bubble' else metrics[:2]
            if kind=='Bubble' and len(selected)<3:raise ValueError('Select three measures: X, Y and bubble size.')
            data=clean[selected].dropna();x,y=selected[:2]
            if data.empty:raise ValueError('No paired finite values are available for these measures.')
            if kind=='Density heatmap':fig=px.density_heatmap(data,x=x,y=y,nbinsx=25,nbinsy=25,labels=axes)
            elif kind=='Bubble':
                data=data.copy();data['__size']=data[selected[2]].abs()
                if not data.__size.gt(0).any():raise ValueError('Bubble size needs at least one nonzero measured value.')
                fig=px.scatter(data,x=x,y=y,size='__size',size_max=35,opacity=.5,labels={**axes,'__size':'Absolute '+selected[2]},hover_data=[selected[2]])
            else:fig=px.scatter(data,x=x,y=y,opacity=.5,labels=axes)
        note=f'Deterministic sample of {len(sampled):,} / {len(frame):,} records; missing/non-finite values are excluded. Axes retain field units.'
        if kind=='Bubble':note+=' Bubble area uses the absolute third measure, including negative amounts; it does not indicate confidence.'
        if kind=='Density heatmap':note+=' Color shows sampled record count, not summed value.'
        shown=data
    for annotation in fig.layout.annotations:
        if '=' in annotation.text:annotation.text=annotation.text.split('=',1)[1]
    fig.update_layout(showlegend=(kind in {'Line','Area'} and shown.Series.nunique()>1) or kind in {'Pie','Donut'})
    return {'figure':fig,'note':note,'table':table,'shown':shown}
