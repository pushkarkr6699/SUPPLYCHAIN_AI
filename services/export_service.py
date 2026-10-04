"""In-memory downloads, always labeled as synthetic demonstration output."""
from io import BytesIO
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.graphics.shapes import Drawing, Line, String, PolyLine
from services.analytics import summary, trend
from services.provider import filter_description


def safe_frame(df):
    frame = df.copy()
    for col in frame.select_dtypes(include=["object", "string"]):
        frame[col] = frame[col].map(lambda value: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value)
    frame["Source"] = "DEMO UI DATA"
    return frame


def csv_bytes(df):
    return safe_frame(df).to_csv(index=False).encode("utf-8-sig")


def excel_bytes(df):
    buffer = BytesIO()
    safe_frame(df).to_excel(buffer, index=False, sheet_name="DEMO UI DATA")
    return buffer.getvalue()


def report_pdf(df, report_name, filters, sections):
    if report_name not in {"Executive", "Delivery", "Demand"}:
        raise ValueError("Report unavailable until verified model signals are connected.")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(595, 842), rightMargin=42, leftMargin=42, topMargin=48, bottomMargin=45, title=f"DEMO UI DATA - {report_name} Report")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Meta", fontSize=8, leading=12, textColor=colors.HexColor("#68768d")))
    styles["Title"].textColor = colors.HexColor("#182b4a")
    styles["Title"].fontSize = 24
    styles["BodyText"].leading = 15
    styles["Heading2"].keepWithNext = True
    flow = [Paragraph("SUPPLYCHAIN AI", styles["Meta"]), Spacer(1, 18), Paragraph(f"{escape(report_name)} Report", styles["Title"]),
        Paragraph("DEMO UI DATA | Synthetic records | No live model inference", styles["Meta"]), Spacer(1, 18),
        Paragraph("This report demonstrates the reporting interface. It does not contain verified operational results or production model performance.", styles["BodyText"]), Spacer(1, 12),
        Paragraph("Filter context: " + escape(filter_description(filters)), styles["Meta"]), Spacer(1, 22)]
    m = summary(df)
    if report_name == "Executive":
        status_rows = [
            ["SECTION", "STATUS / SCOPE"],
            ["1. Overall Status", "Demo UI operational; no live operational services are connected."],
            ["2. Delivery Intelligence", "Synthetic delivery signals only; verified model artifacts are not connected."],
            ["3. Demand Intelligence", "Synthetic forecast fixture only; no verified demand model is connected."],
            ["4. Profitability Intelligence", "Unavailable · no verified profitability dataset or model."],
            ["5. Cross-Risk Analysis", "Unavailable · no validated joint signal or join contract."],
            ["6. Significant Changes", "Demo observations only; no causal explanation is inferred."],
            ["7. Model Health", "Production model availability and performance are unverified."],
            ["8. Data Quality", "Current checks describe synthetic UI data only."],
            ["9. Supporting Charts", "Included below." if "Charts" in sections else "Not selected."],
            ["10. Supporting Tables", "Included below." if "Records" in sections else "Not selected."],
        ]
        status_table = Table(status_rows, colWidths=[170, 340], hAlign="LEFT", repeatRows=1)
        status_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#182b4a")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f2f5fa"), colors.white]), ("FONTSIZE", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
        flow.extend([Paragraph("Executive Summary", styles["Heading2"]), status_table, Spacer(1, 18)])
    if "KPIs" in sections:
        metrics = [["MEASURE", "DEMO VALUE"], ["Orders", f'{m["orders"]:,}'], ["Mean delivery risk", f'{m["risk"]:.1%}'], ["High-risk orders", f'{m["high"]:,}'], ["Forecast demand (units)", f'{m["forecast"]:,}'], ["Forecast WAPE", f'{m["wape"]:.1%}']]
        table = Table(metrics, colWidths=[335, 175], hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#182b4a")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f2f5fa"), colors.white]), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 11), ("BOTTOMPADDING", (0, 0), (-1, -1), 11)]))
        flow.extend([Paragraph("Workspace summary", styles["Heading2"]), table, Spacer(1, 20)])
    if "Charts" in sections and len(df):
        data = trend(df)
        drawing = Drawing(510, 170)
        drawing.add(Line(40, 25, 500, 25, strokeColor=colors.HexColor("#cbd4e4")))
        upper = max(data["Actual Demand"].max(), data["Forecast Demand"].max(), 1)
        for fraction in [0, .5, 1]:
            y = 30 + fraction * 105
            drawing.add(String(0, y - 3, f"{upper * fraction:,.0f}", fontSize=7, fillColor=colors.HexColor("#68768d")))
        for column, color in [("Actual Demand", "#4169dc"), ("Forecast Demand", "#8970dc")]:
            points = [(40 + i * 455 / max(len(data) - 1, 1), 30 + float(value) / upper * 105) for i, value in enumerate(data[column])]
            if len(points) > 1:
                drawing.add(PolyLine(points, strokeColor=colors.HexColor(color), strokeWidth=1.7, strokeDashArray=[4, 3] if column == "Forecast Demand" else None))
        drawing.add(String(40, 152, "Actual (blue) / Forecast (purple) - demo demand units", fontSize=9))
        drawing.add(String(40, 8, data.Date.min().strftime("%d %b %Y"), fontSize=8))
        drawing.add(String(425, 8, data.Date.max().strftime("%d %b %Y"), fontSize=8))
        flow.append(KeepTogether([Paragraph("Demand through the selected period", styles["Heading2"]), drawing]))
    if "Insights" in sections:
        flow.extend([Paragraph("Decision context", styles["Heading2"]), Paragraph(f'{m["high"]:,} synthetic records are in the high or critical delivery bands. {m["stock"]:,} records exceed the illustrative inventory-attention rule. These observations do not establish causal effects.', styles["BodyText"])])
    if "Records" in sections:
        rows = [["ORDER", "MARKET", "RISK"]] + [[str(r.Order), str(r.Market), f'{r["Risk Probability"]:.1%}'] for _, r in df.nlargest(10, "Risk Probability").iterrows()]
        table = Table(rows, colWidths=[170, 220, 120], hAlign="LEFT", repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf1f8")), ("FONTSIZE", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        flow.append(KeepTogether([Paragraph("Critical records - up to ten", styles["Heading2"]), table]))
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#68768d"))
        canvas.drawString(42, 24, "SUPPLYCHAIN AI | DEMO UI DATA | Portfolio interface")
        canvas.drawRightString(552, 24, str(doc.page))
        canvas.restoreState()
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()

