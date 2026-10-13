"""Public provenance retains exact training source, without captured records."""
import json
from hashlib import sha256
import pytest
from config import ROOT

REGISTRY = json.loads((ROOT / 'metadata/data_registry.json').read_text(encoding='utf-8-sig'))
NOTEBOOKS = [row for row in REGISTRY['artifacts'] if row['path'].endswith('.ipynb')]


@pytest.mark.parametrize('artifact', NOTEBOOKS, ids=[row['id'] for row in NOTEBOOKS])
def test_private_original_and_clean_public_notebook_preserve_training_source(artifact):
    original_path = (ROOT / artifact['path']).resolve()
    assert original_path.is_relative_to(ROOT / 'backups/private_provenance')
    original_bytes = original_path.read_bytes()
    assert sha256(original_bytes).hexdigest() == artifact['sha256']
    original = json.loads(original_bytes.decode('utf-8-sig'))
    public_path = ROOT / artifact['public_provenance_path']
    published_bytes = public_path.read_bytes()
    assert sha256(published_bytes).hexdigest() == artifact['public_provenance_sha256']
    published = json.loads(published_bytes)
    def source_digest(notebook):
        source = [(cell['cell_type'], cell.get('source', [])) for cell in notebook['cells']]
        return sha256(json.dumps(source, ensure_ascii=False).encode()).hexdigest()
    assert source_digest(original) == source_digest(published)
    assert not any(cell.get('outputs') for cell in published['cells'])
    assert all(cell.get('execution_count') is None for cell in published['cells'])
    assert 'widgets' not in published.get('metadata', {})
