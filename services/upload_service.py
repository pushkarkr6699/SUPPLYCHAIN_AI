"""Bounded, session-only data imports and fixed registered model adapters.

No paths, executable artifacts, or caller-selected models are loaded here.
Column names, row values and filenames are excluded from external AI payloads.
"""
import csv
import io
import json
import zipfile
import re
from hashlib import sha256
from pathlib import PurePath

import numpy as np
import pandas as pd
from config import ROOT
from services import parameter_comparison as analysis

MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 50000
MAX_COLUMNS = 100
MAX_CELL = 4096
MAX_PREDICTION_ROWS = 5000
MODELS = {'delivery': 'Delivery order risk', 'demand': 'Next-day web visits',
          'profitability': 'Profitability line items', 'delivery_final': 'Final delivery line items'}
FORMATS = ['csv', 'tsv', 'xlsx', 'json']


def _headers(names):
    if not names or len(names) > MAX_COLUMNS:
        raise ValueError('Provide 1-100 columns.')
    if any(not isinstance(n, str) or not n.strip() or len(n) > 128 for n in names):
        raise ValueError('Column names must be nonempty text of at most 128 characters.')
    clean = [n.strip() for n in names]
    if len(set(clean)) != len(clean):
        raise ValueError('Duplicate column names are not supported, including names differing only by surrounding spaces.')
    return clean


def _xlsx(data):
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        entries = archive.infolist()
        if len(entries) > 2048 or sum(e.file_size for e in entries) > 40 * 1024 * 1024:
            raise ValueError('This workbook expands beyond the 40 MB import limit. Export a smaller sheet as CSV.')
        if any(e.flag_bits & 1 or 'vbaproject' in e.filename.lower() or 'externallinks/' in e.filename.lower() for e in entries):
            raise ValueError('Encrypted workbooks, macros and external workbook links are not supported.')
        if any(e.file_size > max(1, e.compress_size) * 1000 for e in entries):
            raise ValueError('This workbook has excessive compressed expansion. Export its values as CSV.')
        for entry in entries:
            if entry.filename.lower().endswith('.xml'):
                xml = archive.read(entry)
                if b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():
                    raise ValueError('Workbook XML entity declarations are not supported.')
                if entry.filename.startswith('xl/worksheets/'):
                    # Bound sparse cell coordinates before the reader allocates or pads rows.
                    for letters, row in re.findall(rb'\br\s*=\s*[\"\x27]([A-Za-z]+)([0-9]+)[\"\x27]', xml):
                        column = 0
                        for char in letters.upper():
                            column = column * 26 + char - 64
                        if column > MAX_COLUMNS or int(row) > MAX_ROWS + 1:
                            raise ValueError('Workbook cell coordinates exceed 100 columns or 50,000 data rows. Export a smaller sheet.')
        from openpyxl import load_workbook
        return load_workbook(io.BytesIO(data), read_only=True, data_only=False, keep_links=False)
    except ValueError:
        raise
    except Exception:
        raise ValueError('The XLSX workbook could not be read. Export the sheet as CSV.') from None


def sheets(data):
    if not data or len(data) > MAX_BYTES:
        raise ValueError('Choose a nonempty file no larger than 20 MB.')
    book = _xlsx(data)
    try:
        return book.sheetnames
    finally:
        book.close()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON keys are not supported.')
        result[key] = value
    return result


def parse(data, filename, delimiter='Auto', encoding='utf-8-sig', sheet=None):
    if not isinstance(data, bytes) or not data or len(data) > MAX_BYTES:
        raise ValueError('Choose a nonempty file no larger than 20 MB.')
    extension = PurePath(filename).suffix.lower().lstrip('.')
    if extension not in FORMATS:
        raise ValueError('Use CSV, TSV, XLSX or a JSON array of flat records. Model and executable uploads are not accepted.')
    if encoding not in {'utf-8-sig', 'cp1252'} or delimiter not in {'Auto', ',', ';', '\t', '|'}:
        raise ValueError('Choose a supported encoding and delimiter.')
    try:
        if extension in {'csv', 'tsv'}:
            text = data.decode(encoding)
            if '\x00' in text:
                raise ValueError('Binary or UTF-16 files are not supported. Save as UTF-8 CSV.')
            if delimiter == 'Auto':
                try:
                    delimiter = '\t' if extension == 'tsv' else csv.Sniffer().sniff(text[:8192], delimiters=',;\t|').delimiter
                except csv.Error:
                    delimiter = ','
            reader = csv.reader(io.StringIO(text), delimiter=delimiter, strict=True)
            headers = _headers(next(reader, []))
            rows = []
            for row in reader:
                if not row or not any(row):
                    continue
                if len(rows) >= MAX_ROWS:
                    raise ValueError('Import at most 50,000 rows; split larger files.')
                if len(row) != len(headers):
                    raise ValueError('A CSV row has a different field count from the header. Check the delimiter and quoting.')
                if any(len(v) > MAX_CELL for v in row):
                    raise ValueError('Cells must contain at most 4,096 characters.')
                rows.append([v if v != '' else None for v in row])
            frame = pd.DataFrame(rows, columns=headers)
        elif extension == 'json':
            def bad_constant(_):
                raise ValueError('JSON numeric values must be finite.')
            records = json.loads(data.decode('utf-8-sig'), object_pairs_hook=_object, parse_constant=bad_constant)
            if not isinstance(records, list) or not records or len(records) > MAX_ROWS:
                raise ValueError('JSON must be a nonempty array with at most 50,000 flat record objects.')
            if any(not isinstance(r, dict) or any(isinstance(v, (list, dict)) for v in r.values()) for r in records):
                raise ValueError('JSON rows must be flat record objects; nested values are not supported.')
            names = list(dict.fromkeys(k for r in records for k in r))
            headers = _headers(names)
            frame = pd.DataFrame(records).rename(columns=dict(zip(names, headers)))
        else:
            book = _xlsx(data)
            try:
                if sheet is not None and sheet not in book.sheetnames:
                    raise ValueError('Choose an available worksheet.')
                worksheet = book[sheet or book.sheetnames[0]]
                # Reset potentially forged dimensions; bound iteration ourselves.
                worksheet.reset_dimensions()
                iterator = worksheet.iter_rows(max_col=MAX_COLUMNS + 1)
                first = next(iterator, ())
                if any(c.data_type == 'f' for c in first):
                    raise ValueError('Formula cells are not imported. Export calculated values as CSV.')
                values = [c.value for c in first]
                while values and values[-1] is None:
                    values.pop()
                headers = _headers(values)
                rows = []
                for row_number, cells in enumerate(iterator, start=2):
                    if row_number > MAX_ROWS + 1:
                        raise ValueError('Workbook row coordinates exceed the 50,000-row limit.')
                    if any(c.data_type == 'f' for c in cells):
                        raise ValueError('Formula cells are not imported. Export calculated values as CSV or a values-only workbook.')
                    values = [c.value for c in cells]
                    if not any(v is not None for v in values):
                        continue
                    if len(rows) >= MAX_ROWS or any(v is not None for v in values[len(headers):]):
                        raise ValueError('Workbook rows exceed the row limit or header column count.')
                    rows.append(values[:len(headers)])
                frame = pd.DataFrame(rows, columns=headers)
            finally:
                book.close()
    except (UnicodeError, csv.Error, json.JSONDecodeError, RecursionError, OverflowError) as exc:
        raise ValueError('This file could not be parsed. Check its format, encoding and delimiter; JSON must contain flat records.') from exc
    if frame.empty:
        raise ValueError('The file has headers but no data records.')
    for column in frame:
        if frame[column].map(lambda v: isinstance(v, str) and len(v) > MAX_CELL).any():
            raise ValueError('Cells must contain at most 4,096 characters.')
        if pd.api.types.is_numeric_dtype(frame[column]) and np.isinf(pd.to_numeric(frame[column])).any():
            raise ValueError('Numeric values must be finite; use empty cells for missing values.')
        if frame[column].map(lambda v: isinstance(v, float) and not np.isfinite(v) and not pd.isna(v)).any():
            raise ValueError('Numeric values must be finite; use empty cells for missing values.')
    if frame.memory_usage(deep=True).sum() > 80 * 1024 * 1024:
        raise ValueError('The parsed data exceeds the 80 MB session limit. Import fewer rows or columns.')
    frame.attrs.update(upload_digest=sha256(data).hexdigest(), data_source='Session upload', dataset='uploaded', uploaded=True)
    return frame


def numeric_candidates(frame):
    result = []
    for column in frame:
        if any(token in column.lower() for token in [' id', '_id', 'identifier', 'postal', 'zip', 'phone', 'code']):
            continue
        values = frame[column].dropna()
        if values.empty or pd.api.types.is_datetime64_any_dtype(values):
            continue
        numbers = pd.to_numeric(values, errors='coerce')
        # Numeric-looking identifiers with leading zeros stay text by default.
        leading_zero = values.astype(str).str.match(r'^[+-]?0\d+$').any()
        if numbers.notna().all() and np.isfinite(numbers.astype(float)).all() and not leading_zero:
            result.append(column)
    return result


def prepare(frame, numeric, date_field=None, date_order='ISO 8601'):
    result = frame.copy()
    if len(set(numeric)) != len(numeric) or any(c not in frame for c in numeric) or date_field in numeric:
        raise ValueError('Choose distinct existing numeric fields, separate from the date field.')
    for column in numeric:
        values = pd.to_numeric(result[column], errors='coerce')
        present = result[column].notna() & result[column].astype(str).str.strip().ne('')
        if (present & values.isna()).any() or np.isinf(values.astype(float)).any():
            raise ValueError('A selected numeric field has invalid or infinite values. Keep it as text or correct the source: ' + column)
        result[column] = values.astype(float)
    if date_field:
        if date_field not in result:
            raise ValueError('Choose an available date field.')
        kwargs = {'format': 'ISO8601'} if date_order == 'ISO 8601' else {'format': 'mixed', 'dayfirst': date_order == 'Day first'}
        dates = pd.to_datetime(result[date_field], errors='coerce', utc=True, **kwargs).dt.tz_convert(None)
        if dates.isna().any():
            raise ValueError('Every selected date value must be valid. Choose the matching date format or no time axis.')
        result[date_field] = dates
        if date_field != 'Date' and 'Date' in result:
            raise ValueError('Rename the existing Date column before selecting a different time field.')
        result['Date'] = dates
    if not any(pd.api.types.is_numeric_dtype(result[c]) for c in result):
        name = 'Generated record count'
        while name in result:
            name += '_'
        result[name] = 1.0
        result.attrs['generated_measure'] = name
    result.attrs.update(data_source='User-uploaded data (session only)', dataset='uploaded', grain='Uploaded records')
    return result


def model_contract(model):
    if model not in MODELS:
        raise ValueError('Choose a registered model.')
    if model == 'delivery':
        from services import inference_service as service
        return {'features': service.FEATURES, 'numeric': service.NUMERIC_FEATURES, 'threshold': service.THRESHOLD,
                'model': MODELS[model], 'status': service.status(), 'note': 'One row per order; engineered features must use the original training definitions.'}
    if model == 'demand':
        from services import demand_inference as service
        return {'features': ['DateOnly', 'Product', 'Category', 'Department', 'Visits'], 'numeric': ['Visits'],
                'threshold': None, 'model': MODELS[model], 'status': service.status(),
                'note': 'At least 15 consecutive daily rows per product, including zero-visit days; stable category/department. Predicts web visits, not purchases.'}
    from services import profitability_inference, final_delivery_inference
    service = profitability_inference if model == 'profitability' else final_delivery_inference
    data = service.contract()
    return {'features': data['features'], 'numeric': data['numeric_features'], 'threshold': service.THRESHOLD,
            'model': MODELS[model], 'status': service.status(), 'note': service.status()['reason']}


def template(model):
    contract = model_contract(model)
    return pd.DataFrame(columns=contract['features']).to_csv(index=False).encode('utf-8-sig')


def map_features(frame, model, mapping):
    contract = model_contract(model)
    if set(mapping) != set(contract['features']) or any(c not in frame for c in mapping.values()):
        raise ValueError('Map every required model feature to an uploaded column. Missing features are never fabricated.')
    if len(set(mapping.values())) != len(mapping):
        raise ValueError('Each model feature requires a distinct source column.')
    return pd.DataFrame({feature: frame[source] for feature, source in mapping.items()}, index=frame.index)


def predict(frame, model, mapping):
    if frame.empty or len(frame) > MAX_PREDICTION_ROWS:
        raise ValueError('Run predictions on 1-5,000 rows. Split larger uploads or filter the selected data.')
    inputs = map_features(frame, model, mapping)
    contract = model_contract(model)
    for column in contract['numeric']:
        values = pd.to_numeric(inputs[column], errors='coerce')
        if values.isna().any() or not np.isfinite(values.astype(float)).all():
            raise ValueError('Model inputs require complete finite numbers: ' + column)
        inputs[column] = values.astype(float)
    for column, low, high in [('Order Item Discount Rate',0,1),('Order_Month',1,12),('Order_DayOfWeek',0,6),('Order_Hour',0,23),('Weekend',0,1),('Order_Weekend',0,1),('Order_Quarter',1,4)]:
        if column in inputs and not inputs[column].between(low,high).all():
            raise ValueError(column + ' must be between ' + str(low) + ' and ' + str(high) + '.')
    for column in ['Order Item Quantity','Order Item Product Price','Product Price','Days for shipment (scheduled)','Number_of_Items','Number_of_Products','Number_of_Categories']:
        if column in inputs and not inputs[column].ge(0).all():
            raise ValueError(column + ' cannot be negative.')
    if model == 'delivery':
        from services.inference_service import predict_delivery
        output = predict_delivery(inputs)
    elif model == 'demand':
        from services.demand_inference import predict_next_day
        for column in ['Product', 'Category', 'Department']:
            if inputs[column].isna().any() or not inputs[column].map(lambda v: isinstance(v, str) and bool(v.strip())).all():
                raise ValueError('Demand product, category and department must contain nonempty text.')
        output = predict_next_day(inputs)
        output['Date'] = output['Forecast Date']
    else:
        from services import profitability_inference, final_delivery_inference
        service = profitability_inference if model == 'profitability' else final_delivery_inference
        scored = service.predict(inputs)
        fields = ['Profitability Probability', 'Loss Probability', 'Predicted Profitable', 'Profitability Risk'] if model == 'profitability' else ['Risk Probability', 'Predicted Late', 'Risk']
        output = scored[fields].copy()
        output.attrs.update(scored.attrs)
    if model != 'demand':
        if any(c in frame for c in output.columns):
            raise ValueError('Remove or rename existing prediction columns before scoring to avoid confusing old and new scores.')
        context = frame.copy()
        # Expose the same validated numbers used by inference to charts, even when
        # the CSV parser deliberately kept the original upload as text.
        for feature in contract['numeric']:
            context[mapping[feature]] = inputs[feature].astype(float)
        result = pd.concat([context.reset_index(drop=True), output.reset_index(drop=True)], axis=1)
    else:
        result = output.copy()
    result.attrs.update(output.attrs, uploaded=True, dataset='uploaded', model_key=model,
                        data_source='Registered ' + MODELS[model] + ' predictions on user-uploaded data',
                        production_threshold=contract['threshold'], grain='Next-day per product' if model == 'demand' else 'Uploaded feature rows',
                        evaluation_note=contract['note'])
    return result


def insights(frame, groups, metrics, operation='Mean'):
    table = analysis.comparison(frame, groups, metrics, operation)
    return table, analysis.evidence(frame, table, groups, metrics, operation)


def ai_payload(frame, groups, metrics, operation, focus=''):
    # Anonymize field names too: an arbitrary uploaded header may itself be private.
    names = {c: 'Dimension ' + str(i + 1) for i, c in enumerate(groups)}
    names.update({c: 'Measure ' + str(i + 1) for i, c in enumerate(metrics)})
    anonymous = frame[groups + metrics].rename(columns=names)
    dims, measures = [names[c] for c in groups], [names[c] for c in metrics]
    _, facts = insights(anonymous, dims, measures, operation)
    payload = analysis.narration_payload(facts, {'dimensions': dims, 'metrics': measures, 'operation': operation}, 'User-uploaded session data')
    payload['focus'] = focus[:1000]
    model = frame.attrs.get('model_key')
    payload['model'] = MODELS.get(model, 'No trained inference in this view')
    payload['threshold'] = frame.attrs.get('production_threshold') if model else None
    payload['limitations'] = 'Historical summaries, not causal evidence. Uploaded data compatibility does not establish model accuracy on a new population.'
    if model == 'profitability':
        payload['limitations'] += ' Profitability historical ROC-AUC is approximately 0.4978; do not treat these scores as reliable decision guarantees.'
    return payload, names


def narrate(frame, groups, metrics, operation, focus, *, consent=False):
    if not consent:
        raise ValueError('Approve anonymized summaries and the question text before requesting external AI.')
    from services.ai_narration import narrate as generate
    return generate(ai_payload(frame, groups, metrics, operation, focus)[0])


def excel_download(frame):
    """Create an upload export without using the shared built-in export cache."""
    from services.export_service import safe_frame
    buffer = io.BytesIO()
    safe_frame(frame).to_excel(buffer, index=False, sheet_name='Uploaded analysis')
    return buffer.getvalue()
