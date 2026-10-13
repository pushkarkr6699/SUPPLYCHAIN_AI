"""Keep original registered notebooks private; publish source without outputs.

The original bytes and SHA-256 remain registered in ignored backups/. No cells
are executed and no source, dataset or trained model is replaced.
"""
import json
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    registry_path = ROOT / "metadata/data_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    checks = []
    for artifact in registry["artifacts"]:
        if not artifact["path"].endswith(".ipynb"):
            continue
        public_relative = artifact.get("public_provenance_path", artifact["path"])
        public = (ROOT / public_relative).resolve()
        original = (ROOT / artifact["path"]).resolve()
        archive = (ROOT / "backups/private_provenance" / public_relative).resolve()
        assert public.is_relative_to(ROOT / "notebooks")
        assert archive.is_relative_to(ROOT / "backups/private_provenance")
        payload = original.read_bytes()
        assert sha256(payload).hexdigest() == artifact["sha256"], artifact["id"]
        archive.parent.mkdir(parents=True, exist_ok=True)
        if archive.exists():
            assert archive.read_bytes() == payload, "Private backup mismatch: " + artifact["id"]
        else:
            archive.write_bytes(payload)
        notebook = json.loads(payload.decode("utf-8-sig"))
        removed = 0
        for cell in notebook.get("cells", []):
            removed += len(cell.get("outputs", []))
            if cell.get("cell_type") == "code":
                cell["outputs"] = []
                cell["execution_count"] = None
            cell.pop("attachments", None)
            cell.get("metadata", {}).pop("execution", None)
        notebook.get("metadata", {}).pop("widgets", None)
        clean = (json.dumps(notebook, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
        public.write_bytes(clean)
        artifact.update(path=archive.relative_to(ROOT).as_posix(),
                        public_provenance_path=public_relative,
                        public_provenance_sha256=sha256(clean).hexdigest(),
                        public_provenance_sanitized=True,
                        publication_note="Original registered bytes retained privately; published notebook contains source cells without captured outputs.")
        checks.append({"id": artifact["id"], "original_hash_preserved": True,
                       "published_outputs": 0, "original_outputs_archived": removed})
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    report = {"passed": True, "checked_at": datetime.now(timezone.utc).isoformat(),
              "checks": checks, "originals_preserved_privately": True,
              "scope": "Current published notebook files only; prior Git history is unchanged."}
    (ROOT / "metadata/notebook_publication_qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
