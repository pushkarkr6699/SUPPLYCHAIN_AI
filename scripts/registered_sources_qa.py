"""Verify every registered local artifact, and safely load every registered CSV."""
import json
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.dataset_catalog import entries, load


def main():
    registry = json.loads((ROOT / "metadata/data_registry.json").read_text(encoding="utf-8-sig"))
    tables = {row["id"]: row for row in entries()}
    checks = []
    for artifact in registry["artifacts"]:
        path = (ROOT / artifact["path"]).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise AssertionError("Registered artifact unavailable: " + artifact["id"])
        content = path.read_bytes()
        assert sha256(content).hexdigest() == artifact["sha256"], artifact["id"]
        assert len(content) == artifact["bytes"], artifact["id"]
        result = {"id": artifact["id"], "role": artifact["role"], "hash_verified": True,
                  "bytes": len(content), "table_loaded": False}
        if artifact["id"] in tables:
            frame = load(artifact["id"])
            if artifact.get("rows") is not None:
                assert len(frame) == artifact["rows"], artifact["id"]
            assert "Customer Password" not in frame.columns, artifact["id"]
            assert not frame.columns.duplicated().any(), artifact["id"]
            result.update(table_loaded=True, rows=len(frame), columns=len(frame.columns),
                          date_available="Date" in frame.columns and frame.Date.notna().any())
        checks.append(result)
    report = {"passed": True, "checked_at": datetime.now(timezone.utc).isoformat(),
              "artifacts": len(checks), "csv_tables": len(tables), "checks": checks,
              "scope": "All registered artifact hashes and byte counts; safe registered CSV loads and row counts. No raw records, model deserialization or notebook execution."}
    (ROOT / "metadata/registered_sources_qa.json").write_text(json.dumps(report, indent=2, default=bool) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "checks"}, indent=2))


if __name__ == "__main__":
    main()
