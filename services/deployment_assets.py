"""Install only exact repository-registered assets from a private deployment bundle.

This is a server deployment operation, never a user-upload/model import feature.
It does not deserialize models or execute archive contents.
"""
from hashlib import sha256
from pathlib import Path
import json
import stat
import zipfile
from config import ROOT

MAX_BYTES = 128 * 1024 * 1024


def expected_assets(root=ROOT):
    expected = {}
    manifests = [root / 'metadata/data_registry.json', *sorted((root / 'metadata').glob('portable*registry.json'))]
    for manifest in manifests:
        registry = json.loads(manifest.read_text(encoding='utf-8-sig'))
        for row in registry.get('artifacts', []):
            name = row['path']
            if not name.startswith(('data/', 'models/')):
                continue
            target = (root / name).resolve()
            if not target.is_relative_to(root.resolve()) or len(row['sha256']) != 64:
                raise ValueError('Invalid repository asset registration.')
            if name in expected and expected[name] != row['sha256']:
                raise ValueError('Conflicting repository asset hashes.')
            expected[name] = row['sha256']
    return expected


def package(destination, root=ROOT):
    destination = Path(destination).resolve()
    if not destination.is_relative_to((root / 'backups').resolve()):
        raise ValueError('Deployment bundles must stay in ignored private backups.')
    assets = expected_assets(root)
    for name, digest in assets.items():
        path = root / name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('A registered asset is missing or changed; validate before packaging.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(assets):
            archive.write(root / name, name)
    return {'assets': len(assets), 'bytes': destination.stat().st_size,
            'sha256': sha256(destination.read_bytes()).hexdigest()}


def install(bundle, bundle_sha256, root=ROOT):
    raw = Path(bundle).read_bytes()
    if len(raw) > MAX_BYTES or sha256(raw).hexdigest() != bundle_sha256:
        raise ValueError('Deployment bundle size or pinned checksum mismatch.')
    expected = expected_assets(root)
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        names = [member.filename for member in members]
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError('Bundle must contain exactly the registered deployment assets.')
        if sum(member.file_size for member in members) > MAX_BYTES:
            raise ValueError('Expanded deployment bundle exceeds the limit.')
        # Validate every member before any write, including files already installed.
        payloads = {}
        for member in members:
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode) or member.is_dir():
                raise ValueError('Links and directories are not deployment assets.')
            target = (root / member.filename).resolve()
            if not target.is_relative_to(root.resolve()):
                raise ValueError('Deployment asset escapes the project.')
            content = archive.read(member)
            if sha256(content).hexdigest() != expected[member.filename]:
                raise ValueError('Deployment member disagrees with its repository hash.')
            if target.exists() and sha256(target.read_bytes()).hexdigest() != expected[member.filename]:
                raise ValueError('Refusing to overwrite a changed existing asset.')
            payloads[target] = content
        for target, content in payloads.items():
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    return len(payloads)
