"""Read-only asset discovery; never deserialize models or read private settings."""
import json
from hashlib import sha256
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git', '.venv', 'tmp', 'backups', '__pycache__', '.pytest_cache', 'node_modules'}
SUFFIXES = {'.csv', '.tsv', '.xlsx', '.parquet', '.json', '.pkl', '.joblib', '.ipynb', '.py', '.css', '.toml'}


def inventory():
    registry = json.loads((ROOT / 'metadata/data_registry.json').read_text(encoding='utf-8-sig'))
    registered = {a['path']: a for a in registry['artifacts']}
    assets = []
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED for part in relative.parts) or not path.is_file() or path.suffix.lower() not in SUFFIXES:
            continue
        if path.name in {'master_inventory.json'}:
            continue
        name = relative.as_posix()
        item = {'path': name, 'bytes': path.stat().st_size, 'kind': path.suffix[1:]}
        if relative.parts[0] in {'data', 'models', 'notebooks'}:
            item['sha256'] = sha256(path.read_bytes()).hexdigest()
        if name in registered:
            item.update(family=registered[name]['family'], role=registered[name]['role'],
                        registered_hash_matches=item['sha256'] == registered[name]['sha256'])
        if path.suffix.lower() in {'.csv', '.tsv'}:
            for encoding in ('utf-8-sig', 'utf-8', 'latin1'):
                try:
                    frame = pd.read_csv(path, encoding=encoding, sep='\t' if path.suffix == '.tsv' else ',')
                    item.update(rows=len(frame), columns=list(frame.columns), dtypes={c: str(frame[c].dtype) for c in frame},
                                missing_cells=int(frame.isna().sum().sum()), duplicate_rows=int(frame.duplicated().sum()), encoding=encoding)
                    break
                except UnicodeError:
                    continue
                except (ValueError, pd.errors.ParserError):
                    item['read_status'] = 'Invalid tabular file'; break
        if path.suffix.lower() == '.ipynb':
            notebook = json.loads(path.read_text(encoding='utf-8-sig'))
            item.update(cells=len(notebook.get('cells', [])), code_cells=sum(c.get('cell_type') == 'code' for c in notebook.get('cells', [])))
        assets.append(item)
    missing = [n for n in ('DataCoSupplyChainDataset.csv', 'DescriptionDataCoSupplyChain.csv', 'tokenized_access_logs.csv')
               if not any(Path(a['path']).name == n for a in assets)]
    result = {'generated_utc': datetime.now(timezone.utc).isoformat(), 'assets': assets, 'missing_requested_sources': missing,
              'private_settings': 'Existence/configuration only; contents excluded. No models deserialized by this inventory.'}
    (ROOT / 'metadata/master_inventory.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# Project inventory', '', 'This inventory was captured before the master-prompt implementation. Existing UI and labelled demo mode are preserved.', '',
             '## Actual data and model assets', '', '| Path | Bytes | Rows | Role / format | Integrity |', '|---|---:|---:|---|---|']
    for a in assets:
        if a['path'].split('/')[0] in {'data', 'models', 'notebooks'}:
            lines.append(f"| `{a['path']}` | {a['bytes']:,} | {a.get('rows', '-')} | {a.get('role', a['kind'])} | {'Verified registry hash' if a.get('registered_hash_matches') else 'Discovered; see JSON'} |")
    lines += ['', '## Schema and provenance', '', 'Exact columns, types, row counts, missing cells, duplicates and hashes are in `metadata/master_inventory.json`.',
              'Delivery: order-grain primary records and a scored test subset. Demand: product/day web visits, not purchased units. Profitability and final delivery: supplied line observations, not interchangeable with delivery orders.',
              'Portable model registries define input order, preprocessors, artifact hashes and decision thresholds. No uploaded serialized model may execute.', '',
              '## Missing assets and limitations', '', *['- Missing: `' + n + '`.' for n in missing],
              '- Profitability/final-delivery scored files omit required training inputs; real-row source-score parity is unavailable. Existing conversion probes are test evidence, never business data.',
              '- Original raw access logs, description dictionary, calibrated future intervals, route endpoints and per-record SHAP evidence are not supplied.', '',
              '## Implementation gaps identified before edits', '',
              '- Remove credentials and unnecessary personal information before upload previews, charts, exports and AI context.',
              '- Add Parquet, richer profiling and automatic compatibility checks for all four existing model contracts.',
              '- Extend chart boards to ten slots, portable configuration restoration and per-card controls.',
              '- Expose registered analytical sources and validate any requested cross-source joins.',
              '- Add deterministic uploaded-data questions, momentum/acceleration and investigation evidence.',
              '- Reconcile real data, run regression/browser/security/performance checks and issue an evidence-backed audit.', '',
              '## Security boundary', '', 'Private .env values are excluded. Dataset passwords are never authentication credentials. Session-only demo access is not production authentication. External AI receives only consented anonymous numerical summaries.']
    (ROOT / 'PROJECT_INVENTORY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'assets': len(assets), 'registered': len(registered), 'missing_sources': missing}))


if __name__ == '__main__':
    inventory()
