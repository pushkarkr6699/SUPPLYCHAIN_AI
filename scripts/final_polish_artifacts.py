"""Measure the filter optimization and render a representative report for QA."""
import sys, json, statistics
from pathlib import Path
from time import perf_counter
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import pymupdf as fitz
from services.provider import get_service
from services.export_service import report_pdf
from config import ROOT

service = get_service()
frame = service.records(dataset="delivery")
start, end = frame.Date.max().date() - pd.Timedelta(days=27), frame.Date.max().date()
legacy, vectorized = [], []
for _ in range(7):
    began = perf_counter()
    old = frame[frame.Date.dt.date.between(start, end)]
    legacy.append((perf_counter() - began) * 1000)
    began = perf_counter()
    new = frame[frame.Date.ge(pd.Timestamp(start)) & frame.Date.lt(pd.Timestamp(end) + pd.Timedelta(days=1))]
    vectorized.append((perf_counter() - began) * 1000)
pd.testing.assert_frame_equal(old, new)
filters = {"Date": (start, end)}
selected = service.records(filters, dataset="delivery")
target = ROOT / "output/pdf"
target.mkdir(parents=True, exist_ok=True)
path = target / "supplychain-delivery-polished-preview.pdf"
path.write_bytes(report_pdf(selected, "Delivery", filters, ["KPIs", "Charts", "Insights", "Records"]))
render_dir = ROOT / "tmp/pdfs"
render_dir.mkdir(parents=True, exist_ok=True)
with fitz.open(path) as document:
    for i, page in enumerate(document):
        page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(str(render_dir / f"polish-report-{i + 1}.png"))
    pages = len(document)
report = {"checked_at": datetime.now(timezone.utc).isoformat(), "rows": len(frame),
          "date_filter_equal": True, "legacy_filter_median_ms": round(statistics.median(legacy), 2),
          "vectorized_filter_median_ms": round(statistics.median(vectorized), 2), "pdf_pages": pages,
          "scope": "Seven in-process runs on the local source frame; timings are observations, not performance guarantees."}
(ROOT / "metadata/final_polish_performance.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report), flush=True)
