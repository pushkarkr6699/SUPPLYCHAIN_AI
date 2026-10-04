"""Generate and render representative demo reports for layout inspection."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pymupdf as fitz
from services.provider import get_service
from services.export_service import report_pdf

folder = Path("tmp/pdfs")
folder.mkdir(parents=True, exist_ok=True)
df = get_service().records({"Market": ["Europe", "LATAM"]})
for report in ["Executive", "Delivery", "Demand"]:
    content = report_pdf(df, report, {"Market": ["Europe", "LATAM"]}, ["KPIs", "Charts", "Insights", "Records"])
    path = folder / f"demo-{report.lower()}.pdf"
    path.write_bytes(content)
    doc = fitz.open(stream=content, filetype="pdf")
    for index, page in enumerate(doc):
        assert "DEMO UI DATA" in page.get_text()
        page.get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).save(str(folder / f"{report.lower()}-{index+1}.png"))
    print(f"{report}: {len(doc)} pages, provenance verified, rendered to PNG")

