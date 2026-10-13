"""Private bundles accept only fixed repository hashes; never executable uploads."""
import json
import zipfile
from hashlib import sha256
from pathlib import Path
import pytest
from services.deployment_assets import install, package


@pytest.fixture
def repository(tmp_path):
    root=tmp_path/'project';(root/'metadata').mkdir(parents=True)
    payload=b'field\n1\n'
    registry={'artifacts':[{'path':'data/test/source.csv','sha256':sha256(payload).hexdigest()}]}
    (root/'metadata/data_registry.json').write_text(json.dumps(registry))
    return root,payload


def archive(path,entries):
    with zipfile.ZipFile(path,'w') as bundle:
        for name,payload in entries:bundle.writestr(name,payload)
    return sha256(path.read_bytes()).hexdigest()


def test_exact_bundle_installs_and_preserves_existing_assets(repository,tmp_path):
    root,payload=repository;bundle=tmp_path/'bundle.zip'
    digest=archive(bundle,[('data/test/source.csv',payload)])
    assert install(bundle,digest,root)==1
    assert (root/'data/test/source.csv').read_bytes()==payload
    assert install(bundle,digest,root)==1
    result=package(root/'backups/private.zip',root)
    assert result['assets']==1 and len(result['sha256'])==64
    with pytest.raises(ValueError,match='private backups'):package(tmp_path/'public.zip',root)


@pytest.mark.parametrize('entries',[
    [('data/test/source.csv',b'changed')],
    [('../outside.csv',b'bad')],
    [('data/test/source.csv',b'field\n1\n'),('malicious.py',b'print(1)')],
    [],
])
def test_invalid_bundle_is_rejected_before_any_write(repository,tmp_path,entries):
    root,_=repository;bundle=tmp_path/'bundle.zip';digest=archive(bundle,entries)
    with pytest.raises(ValueError):install(bundle,digest,root)
    assert not (root/'data').exists()


def test_bundle_checksum_and_existing_changed_file_fail_closed(repository,tmp_path):
    root,payload=repository;bundle=tmp_path/'bundle.zip'
    digest=archive(bundle,[('data/test/source.csv',payload)])
    with pytest.raises(ValueError,match='checksum'):install(bundle,'0'*64,root)
    (root/'data/test').mkdir(parents=True);(root/'data/test/source.csv').write_bytes(b'private changed data')
    with pytest.raises(ValueError,match='overwrite'):install(bundle,digest,root)
    assert (root/'data/test/source.csv').read_bytes()==b'private changed data'
