"""Measure complete source reads and repeated exports for the local showcase."""
from pathlib import Path
from time import perf_counter
import os
import sys
import json
from io import BytesIO
import pandas as pd

os.environ["SUPPLYCHAIN_PROVIDER"] = "verified"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.provider import get_service
from services.export_service import csv_bytes, excel_bytes


def timed(action):
    started = perf_counter()
    result = action()
    return result, round(perf_counter() - started, 4)


service = get_service()
cold, cold_seconds = timed(lambda: service.records(dataset="delivery"))
warm, warm_seconds = timed(lambda: service.records(dataset="delivery"))
pd.testing.assert_frame_equal(cold, warm)
frame = cold[cold.Market.eq("Pacific Asia")]
csv_data, csv_seconds = timed(lambda: csv_bytes(frame))
first, excel_cold = timed(lambda: excel_bytes(frame))
second, excel_warm = timed(lambda: excel_bytes(frame.copy()))
assert first == second
exported = pd.read_excel(BytesIO(second), dtype={"Order": str})
assert len(exported) == len(frame) and exported.Order.tolist() == frame.Order.tolist()
assert len(pd.read_csv(BytesIO(csv_data), low_memory=False)) == len(frame)
report = {"status": "passed", "delivery_rows": len(cold), "export_rows": len(frame),
          "cold_records_seconds": cold_seconds, "warm_records_seconds": warm_seconds,
          "csv_generation_seconds": csv_seconds, "cold_excel_seconds": excel_cold,
          "warm_excel_seconds": excel_warm, "cached_export_identical": True,
          "scope": "single-process local showcase; no concurrency or production SLA"}
(ROOT / "metadata/performance_qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
