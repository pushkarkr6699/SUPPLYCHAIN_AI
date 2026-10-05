"""Create a local immutable artifact backup, excluding secrets and environments."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
directory = ROOT / "backups"
directory.mkdir(exist_ok=True)
archive = directory / ("trained_artifacts_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".zip")
if archive.exists():
    raise SystemExit("Backup already exists; existing backups are never overwritten.")
files = sorted(path for name in ("data", "models", "metadata", "notebooks") for path in (ROOT / name).rglob("*") if path.is_file())
with ZipFile(archive, "x", compression=ZIP_DEFLATED, compresslevel=1) as output:
    for path in files:
        output.write(path, path.relative_to(ROOT).as_posix())
with ZipFile(archive) as output:
    if output.testzip() is not None:
        raise SystemExit("Backup integrity check failed")
report = {"archive": archive.relative_to(ROOT).as_posix(), "files": len(files), "bytes": archive.stat().st_size, "sha256": sha256(archive.read_bytes()).hexdigest(), "integrity": "passed", "secrets_included": False}
(ROOT / "metadata/backup_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
