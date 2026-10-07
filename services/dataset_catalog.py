"""Read-only, hash-validated access to registered project tables."""
import json
from hashlib import sha256
import pandas as pd
import streamlit as st
from config import ROOT
from services.privacy import minimize


def entries():
    data=json.loads((ROOT/'metadata/data_registry.json').read_text(encoding='utf-8-sig'))
    return [a for a in data['artifacts'] if a['path'].endswith('.csv') and a['path'].startswith('data/') and '/cache/' not in a['path']]


@st.cache_data(show_spinner=False,max_entries=48)
def _read(relative,digest,mtime,size):
    path=(ROOT/relative).resolve()
    if not path.is_relative_to((ROOT/'data').resolve()) or not path.is_file():raise ValueError('Invalid registered data path.')
    content=path.read_bytes()
    if sha256(content).hexdigest()!=digest:raise ValueError('Registered data integrity mismatch.')
    import io
    for encoding in ('utf-8-sig','utf-8','latin1'):
        try:frame=pd.read_csv(io.BytesIO(content),encoding=encoding);break
        except UnicodeError:continue
    frame=minimize(frame)
    for column in ('Order_Date','Date','DateOnly','order date (DateOrders)'):
        if column in frame:
            dates=pd.to_datetime(frame[column],errors='coerce',format='mixed')
            if dates.notna().any():frame['Date']=dates;break
    frame.attrs.update(verified_artifacts=True,data_source='Registered source: '+path.name,artifact=path.name,artifact_hash=digest)
    return frame


def load(identifier):
    from services.access_control import require
    require('project_data')
    row=next((a for a in entries() if a['id']==identifier),None)
    if row is None:raise ValueError('Choose an available registered dataset.')
    path=(ROOT/row['path']).resolve()
    if not path.is_relative_to((ROOT/'data').resolve()) or not path.is_file():raise ValueError('Registered file unavailable.')
    stat=path.stat()
    frame=_read(row['path'],row['sha256'],stat.st_mtime_ns,stat.st_size)
    frame.attrs.update(dataset=identifier,grain=row.get('role','Registered observations'))
    return frame


def catalog():
    result=[]
    for row in entries():
        status='WARNING' if '/legacy/' in row['path'] else 'READY'
        period='No valid date field'
        try:
            frame=load(row['id'])
            if 'Date' in frame:period=f'{frame.Date.min():%Y-%m-%d} to {frame.Date.max():%Y-%m-%d}'
            rows,columns=len(frame),len(frame.columns)
        except (OSError,ValueError,pd.errors.ParserError):status,rows,columns='UNAVAILABLE',row.get('rows'),len(row.get('columns',[]))
        result.append({'id':row['id'],'Name':row['family']+' / '+row['path'].split('/')[-1], 'Role':row['role'],
                       'Rows':rows,'Columns':columns,'Period':period,'Status':status})
    return result
