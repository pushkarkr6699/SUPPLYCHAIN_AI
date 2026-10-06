"""Bring Your Data: session-local exploration, fixed trained inference and consented AI."""
import json
from hashlib import sha256
from pathlib import PurePath
import pandas as pd
import streamlit as st
from services import upload_service as uploads, parameter_comparison as analysis, ai_narration
from services.export_service import csv_bytes
from views.visualizations import board


def clear():
    generation = st.session_state.get('upload_generation', 0) + 1
    for key in list(st.session_state):
        if key.startswith(('upload_', 'viz_upload_')):
            del st.session_state[key]
    st.session_state.upload_generation = generation


def _scope(scope):
    if st.session_state.get('upload_scope') != scope:
        for key in list(st.session_state):
            if key.startswith(('upload_', 'viz_upload_')) and key not in {'upload_generation'} and not key.startswith('upload_file_'):
                del st.session_state[key]
        st.session_state.upload_scope = scope


def _filter(frame):
    with st.expander('Filter uploaded records'):
        field = st.selectbox('Filter field', ['All records', *frame.columns], key='upload_filter_field')
        if field != 'All records':
            if pd.api.types.is_numeric_dtype(frame[field]):
                values = pd.to_numeric(frame[field], errors='coerce').dropna()
                if not values.empty:
                    a, b = st.columns(2)
                    low = a.number_input('Minimum value', value=float(values.min()), key='upload_min_' + field)
                    high = b.number_input('Maximum value', value=float(values.max()), key='upload_max_' + field)
                    if low > high:
                        st.warning('Minimum must be no greater than maximum.'); return frame.iloc[:0].copy()
                    frame = frame[frame[field].between(low, high)].copy()
            else:
                values = frame[field].dropna().astype(str).unique()
                selected = st.multiselect('Include values (empty means all)', sorted(values[:200]), key='upload_values_' + field)
                if len(values) > 200:
                    st.caption('First 200 distinct values are selectable; an empty selection includes every value.')
                if selected:
                    frame = frame[frame[field].astype(str).isin(selected)].copy()
    return frame


def _ai(frame, prefix):
    with st.expander('Sevika insights for this upload', expanded=True):
        fields, numeric = analysis.catalog(frame)
        if not numeric:
            st.info('Select a numeric field to compute evidence.'); return
        a, b = st.columns(2)
        groups = a.multiselect('Insight grouping fields', fields, max_selections=2, key=prefix+'_ai_groups')
        metrics = b.multiselect('Insight measures', numeric, default=numeric[:2], max_selections=4, key=prefix+'_ai_metrics')
        operations = list(analysis.OPERATIONS)
        operation = st.selectbox('Insight calculation', operations, index=operations.index('Sum') if frame.attrs.get('generated_measure') else 0, key=prefix+'_ai_operation')
        if not metrics:
            st.info('Select at least one measure.'); return
        if operation == 'Sum' and any('Probability' in c or pd.api.types.is_bool_dtype(frame[c]) for c in metrics):
            st.info('Use Mean for probabilities and Boolean proportions.'); return
        try:
            _, facts = uploads.insights(frame, groups, metrics, operation)
        except ValueError as error:
            st.info(str(error)); return
        st.markdown('**Computed evidence (local)**')
        for fact in facts:
            st.write(fact['id']+' - '+fact['text'])
        focus = st.text_area('Ask Sevika about this selection', placeholder='Which patterns should I investigate and what are the model limitations?', max_chars=1000, key=prefix+'_ai_focus')
        payload, names = uploads.ai_payload(frame, groups, metrics, operation, focus)
        st.caption('Field names and group labels are anonymized. Measure names used by the AI: '+ '; '.join(names[c]+' = '+c for c in metrics))
        with st.expander('Review the exact external AI request'):
            st.json(payload, expanded=False)
        with st.container(key='upload_consent_control'):
            consent = st.checkbox('I am authorized to send anonymized numerical summaries and my question text from this upload to Hugging Face/Groq.', key='upload_ai_consent_'+st.session_state.get('upload_scope','unscoped'))
        st.caption('No raw rows, original column names, filenames, identifiers or group names are sent. Question text is sent as written: exclude private details. Consent resets when the upload or import options change.')
        status = ai_narration.status()
        if not status['available']:
            st.info('Live AI is not configured. Local computed evidence and every chart remain available.')
        signature = analysis.signature(frame, {'groups':groups, 'metrics':metrics, 'operation':operation, 'focus':focus})
        if st.button('Generate live Sevika insights', type='primary', disabled=not consent or not status['available'], key=prefix+'_ai_run'):
            st.session_state.pop('upload_ai_result', None)
            try:
                with st.spinner('Sevika is interpreting anonymous evidence...'):
                    result = uploads.narrate(frame, groups, metrics, operation, focus, consent=consent)
                st.session_state.upload_ai_result = {'signature':signature, 'result':result}
                st.success('Live insights generated. Verify the cited calculations before acting.')
            except (ai_narration.NarrationUnavailable, ValueError):
                st.warning('The AI request did not complete. Retry the button; your local evidence remains available.')
        saved = st.session_state.get('upload_ai_result')
        if consent and saved and saved['signature'] == signature:
            st.write(saved['result']['summary'])
            lookup = {f['id']:f for f in facts}
            for item in saved['result']['insights']:
                st.markdown('**'+item['title']+'**')
                st.write(item['observation']); st.write('Next step: '+item['next_step'])
                for ref in item['evidence_ids']:
                    st.caption(ref+' - '+lookup[ref]['text'])
            st.download_button('Download Sevika insight JSON', json.dumps(saved['result'], indent=2).encode(), 'upload_insights.json', 'application/json', key=prefix+'_ai_download', on_click='ignore')


def _models(frame):
    with st.container(key='upload_model_choice'):
        model = st.selectbox('Registered trained model', list(uploads.MODELS), format_func=uploads.MODELS.get, key='upload_model_'+st.session_state.get('upload_scope','unscoped'))
    try:
        contract = uploads.model_contract(model)
    except (OSError, ValueError, KeyError):
        st.warning('Model validation is unavailable. Use raw exploration or check Model Health.'); return
    st.caption(contract['note'])
    if model == 'profitability':
        st.warning('The profitability model has weak historical discrimination (ROC-AUC about 0.4978). These probabilities require careful validation on your own population.')
    st.download_button('Download required-column CSV template', uploads.template(model), model+'_upload_template.csv', 'text/csv', key='upload_template_'+model, on_click='ignore')
    st.caption('Populate every required column using its training definition. Templates contain headers only; no sample predictions or fabricated values. Mapping validates schema, not accuracy on a new population.')
    if contract['threshold'] is not None:
        st.caption('Fixed production classification threshold: '+str(contract['threshold'])+'. Risk bands and the classification threshold may differ.')
    mapping = {}
    with st.expander('Map uploaded columns to model features', expanded=True):
        columns = st.columns(2)
        for i, feature in enumerate(contract['features']):
            choices = ['[Not mapped]', *frame.columns]
            default = choices.index(feature) if feature in frame else 0
            mapping[feature] = columns[i % 2].selectbox(feature, choices, index=default, key='upload_map_'+model+'_'+feature)
    missing = [f for f, source in mapping.items() if source == '[Not mapped]']
    duplicates = len(set(mapping.values())) != len(mapping)
    if missing:
        st.info('Required inputs not mapped: '+', '.join(missing))
    elif duplicates:
        st.warning('Map each feature to a different source column.')
    if len(frame) > uploads.MAX_PREDICTION_ROWS:
        st.info('Prediction limit: 5,000 selected rows. Filter the upload or import a smaller batch.')
    signature = analysis.signature(frame, {'model':model, 'mapping':mapping})
    disabled = bool(missing) or duplicates or frame.empty or len(frame)>uploads.MAX_PREDICTION_ROWS or not contract['status']['available']
    if not contract['status']['available']:
        st.warning(contract['status']['reason'])
    if st.button('Run trained predictions on upload', type='primary', disabled=disabled, key='upload_predict'):
        st.session_state.pop('upload_predictions', None)
        try:
            with st.spinner('Validating features and running the registered trained model...'):
                output = uploads.predict(frame, model, mapping)
            st.session_state.upload_predictions = {'signature':signature, 'frame':output}
            st.success(f'Completed trained inference: {len(output):,} output records.')
        except ValueError as validation:
            st.warning('Prediction validation: '+str(validation)[:700]); return
        except (TypeError, OSError, KeyError):
            st.warning('Prediction could not complete. Check the selected input values and Model Health, then retry.'); return
    saved = st.session_state.get('upload_predictions')
    if saved and saved['signature'] == signature:
        result = saved['frame']
        st.dataframe(result.head(500), hide_index=True, width='stretch')
        st.download_button('Download uploaded predictions CSV', csv_bytes(result), 'uploaded_predictions.csv', 'text/csv', key='upload_prediction_download', on_click='ignore')
        st.caption('Predictions are aligned to uploaded row order. Demand returns one next-day forecast per product. No uploaded data is joined to the built-in datasets.')
        date_field = st.selectbox('Prediction time field (optional)', ['[No time axis]', *result.columns], key='upload_prediction_date_'+model)
        date_order = st.selectbox('Prediction date format', ['ISO 8601', 'Day first', 'Month first'], key='upload_prediction_date_order_'+model)
        try:
            plotted = uploads.prepare(result, [], None if date_field=='[No time axis]' else date_field, date_order)
            plotted.attrs.update(result.attrs)
        except (ValueError, TypeError) as error:
            st.warning(str(error)); return
        board(plotted, 'upload_predictions_'+model, True, 'Prediction visualizations')
        _ai(plotted, 'upload_predictions_'+model)


def render(_df=None):
    st.info('Bring Your Data works independently of the built-in demo and connected datasets. Files stay in this browser session on the server; they are not saved as project data.')
    st.caption('CSV / TSV / XLSX / JSON flat records | 20 MB per file | 50,000 rows | 100 columns | predictions up to 5,000 rows. No uploaded models or executable files.')
    st.button('Clear uploaded data and results', on_click=clear, key='clear_uploads')
    with st.expander('Download model input templates before uploading'):
        selected_model = st.selectbox('Input template model', list(uploads.MODELS), format_func=uploads.MODELS.get, key='template_model_choice')
        try:
            st.download_button('Download empty model-input template', uploads.template(selected_model), selected_model+'_input_template.csv', 'text/csv', key='input_template_download', on_click='ignore')
        except (ValueError, OSError, KeyError):
            st.info('This model template is unavailable until its registered artifacts are validated.')
    generation = st.session_state.get('upload_generation', 0)
    file = st.file_uploader('Upload your dataset', type=uploads.FORMATS, key='upload_file_'+str(generation), max_upload_size=20)
    if file is None:
        st.caption('Choose a file, review its fields, then select Raw data exploration or Trained-model predictions. Live Sevika insights are available for either path after explicit consent.'); return
    data = file.getvalue()
    with st.expander('Import options', expanded=False):
        a, b = st.columns(2)
        delimiter = a.selectbox('CSV delimiter', ['Auto', ',', ';', '\t', '|'], key='import_upload_delimiter')
        encoding = b.selectbox('CSV encoding', ['utf-8-sig', 'cp1252'], key='import_upload_encoding')
        sheet = None
        if file.name.lower().endswith('.xlsx'):
            try:
                sheet = st.selectbox('Worksheet', uploads.sheets(data), key='import_upload_sheet')
            except (ValueError, TypeError, OSError):
                st.warning('This workbook is not a supported values-only XLSX file. Export it as CSV.'); return
    scope = sha256(data + json.dumps([PurePath(file.name).suffix.lower(), delimiter, encoding, sheet]).encode()).hexdigest()
    _scope(scope)
    with st.container(key='import_state_'+scope):
        st.caption('Import fingerprint: '+scope[:12]+' | session only')
    try:
        if 'upload_raw' not in st.session_state:
            st.session_state.upload_raw = uploads.parse(data, file.name, delimiter, encoding, sheet)
        raw = st.session_state.upload_raw
    except (ValueError, TypeError, OSError) as error:
        st.warning('Import validation: '+str(error)[:700]); return
    st.success(f'Imported {len(raw):,} rows and {len(raw.columns)} columns. Built-in datasets and models are unchanged.')
    with st.expander('Preview and data quality', expanded=True):
        st.dataframe(raw.head(100), hide_index=True, width='stretch')
        quality = pd.DataFrame({'Field':raw.columns, 'Missing':raw.isna().sum().to_numpy(), 'Distinct values':[raw[c].nunique() for c in raw], 'Type':[str(raw[c].dtype) for c in raw]})
        st.dataframe(quality, hide_index=True, width='stretch')
        st.caption(f'{int(raw.duplicated().sum()):,} duplicate rows. Empty cells remain missing; no values are imputed. CSV numeric-looking fields start as text to preserve identifiers.')
    with st.container(key='upload_workflow'):
        mode = st.radio('Choose an upload workflow', ['Raw data exploration', 'Trained-model predictions'], horizontal=True, key='upload_mode_'+scope)
    if mode == 'Trained-model predictions':
        _models(_filter(raw)); return
    with st.form('upload_prepare'):
        numeric = st.multiselect('Treat fields as numeric', list(raw.columns), default=uploads.numeric_candidates(raw), key='upload_numeric')
        a,b = st.columns(2)
        date = a.selectbox('Time field (optional)', ['[No time axis]', *raw.columns], key='upload_date')
        order = b.selectbox('Date format', ['ISO 8601', 'Day first', 'Month first'], key='upload_date_order')
        apply = st.form_submit_button('Apply field types', type='primary')
    if apply or 'upload_prepared' not in st.session_state:
        try:
            st.session_state.upload_prepared = uploads.prepare(raw, numeric, None if date=='[No time axis]' else date, order)
            # Widget choices from the previous prepared schema cannot survive type changes.
            for key in list(st.session_state):
                if key.startswith(('viz_upload_', 'upload_filter_', 'upload_values_', 'upload_min_', 'upload_max_', 'upload_raw_ai_')):
                    del st.session_state[key]
            st.session_state.pop('upload_ai_result', None)
        except (ValueError, TypeError) as error:
            st.warning(str(error)); return
    frame = _filter(st.session_state.upload_prepared)
    st.caption(f'{len(frame):,} selected of {len(raw):,} uploaded rows. Charts use the applied field types above.')
    if frame.empty:
        st.info('No rows match. Broaden the uploaded-record filter.'); return
    if frame.attrs.get('generated_measure'):
        st.caption('No numeric measures were supplied. Generated record count = 1 per row supports category counts; it is not a model input.')
    board(frame, 'upload_raw', True, 'Raw data visualizations')
    st.download_button('Download selected upload CSV', csv_bytes(frame), 'uploaded_analysis.csv', 'text/csv', key='upload_data_csv', on_click='ignore')
    if len(frame)<=5000:
        st.download_button('Download selected upload Excel', uploads.excel_download(frame), 'uploaded_analysis.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key='upload_data_excel', on_click='ignore')
    _ai(frame, 'upload_raw')
