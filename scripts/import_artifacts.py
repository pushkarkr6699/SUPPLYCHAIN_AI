"""Import the explicitly supplied training artifacts without losing prior versions."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def import_files(source_root, root=ROOT):
    root, source_root = Path(root).resolve(), Path(source_root).resolve()
    entries = []
    delivery = {
        "DataCo_Final_Order_Level_Dataset.csv": "primary order-level analytical dataset",
        "DataCo_Final_Scored_Orders.csv": "Tuned XGBoost scored test orders",
        "DataCo_Late_Delivery_Predictions.csv": "earlier Random Forest prediction reference",
        "DataCo_Risk_Level_Summary.csv": "scored risk aggregation reference",
    }
    evaluation = ["DataCo_Feature_Importance.csv", "DataCo_Final_Model_Comparison.csv", "DataCo_Model_Comparison.csv", "DataCo_Model_Comparison (1).csv"]
    for name, role in delivery.items():
        entries.append(("d1", name, f"data/delivery/final/{name}", role, "delivery_d1"))
    for name in evaluation:
        entries.append(("d1", name, f"data/delivery/final/evaluation/{name}", "Random Forest importance" if "Importance" in name else "model evaluation reference", "delivery_d1"))
    for name in ["DataCo_Late_Delivery_Model.pkl", "DataCo_Tuned_XGBoost.pkl"]:
        entries.append(("d1", name, f"models/delivery/{name}", "serialized model; not executed by importer", "delivery_d1"))
    entries.append(("d1", "Welcome_To_Colab (2).ipynb", "notebooks/delivery/Welcome_To_Colab (2).ipynb", "training provenance", "delivery_d1"))
    for name in ["AccessLogs_Final_Advanced_Forecast.csv", "AccessLogs_Final_Model_Comparison.csv"]:
        entries.append(("d2", name, f"data/demand/final/{name}", "forecast output" if "Forecast" in name else "mixed comparison reference", "demand_d2"))
    entries.extend([
        ("d2", "AccessLogs_Final_XGBoost_Demand_Model.pkl", "models/demand/AccessLogs_Final_XGBoost_Demand_Model.pkl", "serialized demand model", "demand_d2"),
        ("d2", "Welcome_To_Colab (1).ipynb", "notebooks/demand/Welcome_To_Colab (1).ipynb", "training provenance", "demand_d2"),
    ])
    for name in ["Best_Threshold.txt", "Winning_Model.txt", "Late_Delivery_Feature_Importance.csv", "Late_Delivery_Final_Summary.csv", "Late_Delivery_Model_Comparison.csv", "Late_Delivery_Scored_Orders.csv", "Late_Delivery_Threshold_Analysis.csv", "Late-Delviery-final"]:
        entries.append(("d3", name, f"data/delivery/legacy/d3/{name}", "separate line-item model reference", "delivery_d3"))
    entries.extend([
        ("d3", "Final_Late_Delivery_Model.pkl", "models/delivery/d3/Final_Late_Delivery_Model.pkl", "separate line-item model", "delivery_d3"),
        ("d3", "Welcome_To_Colab.ipynb", "notebooks/delivery/d3/Welcome_To_Colab.ipynb", "training provenance", "delivery_d3"),
        ("d3", "AccessLogs_Final_Advanced_Forecast.csv", "data/demand/legacy/d3/AccessLogs_Final_Advanced_Forecast.csv", "duplicate forecast reference", "demand_d3"),
    ])
    manifest, hashes = [], {}
    for folder, name, relative, role, family in entries:
        source = source_root / folder / name
        if not source.is_file():
            raise FileNotFoundError(f"Supplied artifact is missing: {source}")
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or source.suffix.lower() == ".crdownload":
            raise ValueError("Artifact destination is outside the workspace or incomplete.")
        sha = digest(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and digest(target) != sha:
            old_sha = digest(target)
            archive = root / "data/delivery/legacy/previous_integration" / f"{target.stem}_{old_sha[:12]}{target.suffix}"
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                shutil.copy2(target, archive)
        if not target.exists() or digest(target) != sha:
            shutil.copy2(source, target)
        if digest(target) != sha:
            raise ValueError(f"Copy verification failed: {relative}")
        item = {"id": f"{family}/{name}", "path": relative, "source_path": str(source), "sha256": sha,
                "bytes": target.stat().st_size, "family": family, "role": role, "status": "copied_and_hash_verified"}
        if sha in hashes:
            item["identical_to"] = hashes[sha]
        else:
            hashes[sha] = relative
        if target.suffix.lower() == ".csv":
            df = pd.read_csv(target)
            item.update(rows=len(df), columns=list(df.columns), missing_cells=int(df.isna().sum().sum()), exact_duplicates=int(df.duplicated().sum()))
        manifest.append(item)
    registry = {"registry_version": 2, "active_delivery_family": "delivery_d1", "active_demand_family": "demand_d2",
                "primary_delivery_path": "data/delivery/final/DataCo_Final_Order_Level_Dataset.csv", "artifacts": manifest,
                "excluded": ["Unconfirmed 506925.crdownload"],
                "policy": "Original sources are unchanged; prior destination conflicts are archived; model and notebook files are copied without execution."}
    destination = root / "metadata/data_registry.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    print(f"Imported and hash-verified {len(manifest)} artifacts. Registry: {destination}")
    return registry


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True)
    args = parser.parse_args()
    import_files(args.source_root)
