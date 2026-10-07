"""In-memory downloads carrying the source provenance of the supplied frame."""
from io import BytesIO
from collections import OrderedDict
from hashlib import sha256
from threading import Lock
from datetime import datetime, timezone
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.graphics.shapes import Drawing, Line, String, PolyLine
from services.analytics import summary, trend
from services.provider import filter_description
from services.decision_context import coverage_context, decision_summary
from services.privacy import minimize

_excel_cache = OrderedDict()
_excel_lock = Lock()
_EXCEL_CACHE_BYTES = 32 * 1024 * 1024


def safe_frame(df, source=None):
    frame = minimize(df)
    for col in frame.select_dtypes(include=["object", "string"]):
        frame[col] = frame[col].map(lambda value: "'" + value if isinstance(value, str) and value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")) else value)
    frame["Source"] = source or frame.attrs.get("data_source", "DEMO UI DATA")
    # Spreadsheet applications can execute formulas in column headers as well.
    frame.columns=["'"+str(c) if str(c).lstrip(" \t\r\n").startswith(("=","+","-","@")) else c for c in frame.columns]
    return frame


def csv_bytes(df, source=None):
    return safe_frame(df, source).to_csv(index=False).encode("utf-8-sig")


def excel_bytes(df, source=None):
    frame = safe_frame(df, source)
    if df.attrs.get('uploaded'):
        buffer = BytesIO()
        frame.to_excel(buffer, index=False, sheet_name="SupplyChain Data")
        return buffer.getvalue()
    # Hash every row, column, dtype and provenance; never sample a large frame.
    digest = sha256(pd.util.hash_pandas_object(frame, index=True, categorize=False).values.tobytes())
    digest.update(repr([(column, str(dtype)) for column, dtype in zip(frame.columns, frame.dtypes)]).encode("utf-8"))
    for column in frame.select_dtypes(include=["object", "string"]):
        types = frame[column].map(lambda value: type(value).__name__)
        digest.update(pd.util.hash_pandas_object(types, index=False, categorize=False).values.tobytes())
    key = digest.hexdigest()
    with _excel_lock:
        if key in _excel_cache:
            _excel_cache.move_to_end(key)
            return _excel_cache[key]
    buffer = BytesIO()
    frame.to_excel(buffer, index=False, sheet_name="SupplyChain Data")
    result = buffer.getvalue()
    if len(result) <= _EXCEL_CACHE_BYTES:
        with _excel_lock:
            _excel_cache[key] = result
            while len(_excel_cache) > 3 or sum(map(len, _excel_cache.values())) > _EXCEL_CACHE_BYTES:
                _excel_cache.popitem(last=False)
    return result


def report_pdf(df, report_name, filters, sections):
    """Build a report for the supplied grain without inventing unavailable signals."""
    df = minimize(df)
    if report_name not in {"Executive", "Delivery", "Demand", "Profitability", "Cross-Risk"}:
        raise ValueError("Report unavailable until verified model signals are connected.")
    profitability = "Profitability Probability" in df
    cross = "Maximum line loss probability" in df
    if report_name == "Profitability" and not profitability or report_name == "Cross-Risk" and not cross:
        raise ValueError("Report unavailable without its matching verified dataset.")
    delivery = "Risk Probability" in df
    demand = {"Actual Demand", "Forecast Demand"}.issubset(df)
    if report_name == "Delivery" and not delivery or report_name == "Demand" and not demand:
        raise ValueError(f"{report_name} report requires its matching dataset.")
    line_delivery = df.attrs.get("dataset") == "delivery_final"
    verified = bool(df.attrs.get("verified_artifacts"))
    source = df.attrs.get("data_source", "DEMO UI DATA")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(595, 842), rightMargin=42, leftMargin=42,
        topMargin=48, bottomMargin=45, title=f"{source} - {report_name} Report")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Meta", fontSize=9, leading=13, textColor=colors.HexColor("#52627a")))
    styles["Title"].textColor = colors.HexColor("#182b4a")
    styles["Title"].fontSize = 24
    styles["BodyText"].leading = 15
    styles["Heading2"].keepWithNext = True
    styles["Heading2"].textColor = colors.HexColor("#315de6")
    generated_at = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    context = coverage_context(df)
    note = ("Analysis of supplied data and precomputed outputs. Model inference is not performed by this report. "
            "Delivery and demand datasets have separate grains and are not joined." if verified else
            "This report demonstrates the reporting interface. It does not contain verified operational results or production model performance.")
    flow = [Paragraph("SUPPLYCHAIN AI", styles["Meta"]), Spacer(1, 18),
        Paragraph(f"{escape(report_name)} Report", styles["Title"]),
        Paragraph(escape(source), styles["Meta"]),
        Paragraph("Generated: " + generated_at, styles["Meta"]),
        Paragraph("Selected records: " + escape(context["period"].replace("–", "-")), styles["Meta"]),
        Paragraph("Source freshness: " + escape(context["freshness"].replace("·", "|")), styles["Meta"]), Spacer(1, 18),
        Paragraph(note, styles["BodyText"]), Spacer(1, 12),
        Paragraph("Filter context: " + escape(filter_description(filters, "All records in supplied dataset" if verified else "All demo records").replace("–", "-")), styles["Meta"]), Spacer(1, 22)]
    m = summary(df)

    def add_table(rows, widths, heading):
        wrapped = [[Paragraph(escape(str(cell)), styles["Meta"]) for cell in row] for row in rows]
        table = Table(wrapped, colWidths=widths, hAlign="LEFT", repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6edf7")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f2f5fa"), colors.white]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        flow.extend([Paragraph(heading, styles["Heading2"]), table, Spacer(1, 18)])

    if report_name == "Executive":
        add_table([["SECTION", "STATUS / SCOPE"],
            ["Overall status", "Supplied artifact analysis" if verified else "Demonstration data"],
            ["Delivery intelligence", "Included for current delivery rows" if delivery else "Outside this report's dataset scope"],
            ["Demand intelligence", "Included for current demand observations" if demand else "Outside this report's dataset scope"],
            ["Profitability / cross-risk", "Connected in dedicated reports; separate source grains and limitations"],
            ["Model inference", "Precomputed outputs only; no model executed"],
            ["Data quality", "Missing scores remain missing; results describe the selected rows"]],
            [170, 340], "Executive Summary")
    if "KPIs" in sections:
        metrics = [["MEASURE", "VALUE"], ["Rows", f"{len(df):,}"]]
        if delivery:
            scored = df["Risk Probability"].notna()
            metrics.extend([["Line observations with supplied scores" if line_delivery else "Orders with supplied scores", f"{int(scored.sum()):,}"],
                ["Score coverage", f"{scored.mean():.1%}" if len(df) else "N/A"],
                ["Mean supplied delivery risk", f"{df.loc[scored, 'Risk Probability'].mean():.1%}" if scored.any() else "N/A"],
                ["High-risk scored rows", f"{int(df['Risk'].isin(['High', 'Critical']).sum()):,}" if "Risk" in df else "N/A"]])
        if demand:
            metrics.extend([["Forecast next-day visits", f"{m['forecast']:,.2f}" if m["forecast"] is not None else "N/A"],
                ["Forecast WAPE", f"{m['wape']:.1%}" if m["wape"] is not None else "N/A"]])
        if profitability:
            metrics.extend([["Source line items",f"{len(df):,}"],["Unique order IDs",f"{df.Order.nunique():,}"],["Mean profit probability",f"{df["Profitability Probability"].mean():.1%}"],["Observed profitable rate",f"{df["Actual Profitable"].mean():.1%}"],["Recorded decision threshold","0.20"]])
        if cross:
            metrics.extend([["Orders with profitability lines",str(df["Profitability rows"].notna().sum())],["Orders with both scores",str((df["Profitability rows"].notna() & df["Risk Probability"].notna()).sum())]])
        add_table(metrics, [335, 175], "Workspace summary")
    if "Charts" in sections and len(df):
        if demand:
            data = df.groupby("Date", as_index=False)[["Actual Demand", "Forecast Demand"]].sum()
            series = [("Actual Demand", "#4169dc"), ("Forecast Demand", "#8970dc")]
            chart_title, legend = "Demand through the selected period", "Actual (blue) / Forecast (purple) - next-day visits"
        elif profitability:
            data=df.assign(Date=pd.to_datetime(df.Date).dt.normalize()).groupby("Date",as_index=False)[["Profitability Probability","Actual Profitable"]].mean()
            series=[("Profitability Probability","#4169dc"),("Actual Profitable","#8970dc")]
            chart_title,legend="Profitability in selected line items","Predicted profitability (blue) / observed profitable rate (purple)"
        elif delivery:
            data = df.dropna(subset=["Risk Probability"]).copy()
            data["Date"] = pd.to_datetime(data["Date"]).dt.normalize()
            data = data.groupby("Date", as_index=False)["Risk Probability"].mean()
            series = [("Risk Probability", "#4169dc")]
            chart_title, legend = "Delivery risk through the selected period", "Mean supplied probability per day - scored rows only"
        else:
            data = pd.DataFrame()
        if not data.empty:
            drawing = Drawing(510, 170)
            drawing.add(Line(40, 25, 500, 25, strokeColor=colors.HexColor("#cbd4e4")))
            upper = max(max(float(data[column].max()) for column, _ in series), .01)
            for fraction in [0, .5, 1]:
                label = f"{upper * fraction:.0%}" if (delivery or profitability) and not demand else f"{upper * fraction:,.0f}"
                drawing.add(String(0, 27 + fraction * 105, label, fontSize=9, fillColor=colors.HexColor("#52627a")))
            for column, color in series:
                points = [(40 + i * 455 / max(len(data) - 1, 1), 30 + float(value) / upper * 105) for i, value in enumerate(data[column])]
                if len(points) > 1:
                    drawing.add(PolyLine(points, strokeColor=colors.HexColor(color), strokeWidth=1.7))
            drawing.add(String(40, 152, legend, fontSize=8))
            drawing.add(String(40, 8, data.Date.min().strftime("%d %b %Y"), fontSize=8))
            drawing.add(String(425, 8, data.Date.max().strftime("%d %b %Y"), fontSize=8))
            flow.append(KeepTogether([Paragraph(chart_title, styles["Heading2"]), drawing]))
    if "Insights" in sections:
        observations = [decision_summary(df, "demand" if report_name == "Demand" else None).replace("→", "to")]
        if delivery:
            observations.append(f"{df['Risk Probability'].notna().sum():,} of {len(df):,} rows contain supplied probabilities. Unscored rows are excluded from probability averages.")
        if demand:
            observations.append("Forecast errors compare supplied next-day actual visits with supplied predictions.")
            if {"Lower", "Upper"}.issubset(df) and len(df):
                coverage = df["Actual Demand"].between(df["Lower"], df["Upper"]).mean()
                observations.append(f"Observed coverage of supplied interval bounds is {coverage:.1%}; nominal labels do not establish calibration.")
        if profitability:
            observations.append(df.attrs.get("evaluation_note","Historical profitability line-item observations."))
        if cross:
            observations.append("Profitability is aggregated to unique order IDs before joining. Mean/max line probabilities are descriptive statistics, not a combined model or an order-level profitability probability.")
        observations.append("These observations do not establish causal effects.")
        flow.extend([Paragraph("Decision context", styles["Heading2"]), Paragraph(escape(" ".join(observations)), styles["BodyText"]), Spacer(1, 12)])
    if "Records" in sections:
        if profitability:
            columns=["Profitability Row","Order","Profit","Profitability Probability"]
            records=df.head(10)
        elif report_name == "Demand" or not delivery:
            columns = [column for column in ["Date", "Product", "Actual Demand", "Forecast Demand"] if column in df]
            records = df.head(10)
        else:
            columns = [column for column in ["Order", "Market", "Risk Probability", "Risk"] if column in df]
            if line_delivery: columns.insert(0,"Delivery Row")
            records = df.sort_values("Risk Probability", ascending=False, na_position="last").head(10)
        if columns:
            rows = [columns] + [["N/A" if pd.isna(row[column]) else f"{row[column]:.1%}" if column in {"Risk Probability","Profitability Probability"} else f"{row[column]:,.2f}" if column == "Profit" else str(row[column]) for column in columns] for _, row in records.iterrows()]
            add_table(rows, [510 / len(columns)] * len(columns), "Supporting records - up to ten")
    provenance = [["SOURCE / LIMITATION", "DETAIL"],
        ["Primary artifact", df.attrs.get("artifact", "Synthetic demo fixture")],
        ["Score artifact", df.attrs.get("score_artifact", "Not separately supplied")],
        ["Refresh", "Historical snapshot; no operational refresh feed" if verified else "Fixed synthetic demo snapshot"]]
    if delivery:
        provenance.extend([["Delivery model", df.attrs.get("model_name", "Demo fixture")],
            ["Decision threshold", str(df.attrs.get("production_threshold", "Demo configuration"))],
            ["Evaluation", df.attrs.get("evaluation_note", "Illustrative demo outputs")],
            ["Explanation", "No individual SHAP artifact or causal explanation supplied"]])
    if profitability or cross:
        provenance.append(["Profitability scope", "Line-item source observations; no complete-order profit totals or calibrated order-profitability score are asserted."])
        provenance.append(["Profitability reliability", "All saved predictions are profitable at threshold 0.20; test ROC-AUC approximately 0.4978. No source-score parity without complete features."])
    if demand:
        provenance.append(["Demand scope", "Next-day web visits; inventory and fulfilled units are not supplied"])
    add_table(provenance, [150, 360], "Sources and interpretation limits")
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#68768d"))
        canvas.setStrokeColor(colors.HexColor("#cbd4e4"))
        canvas.line(42, 38, 552, 38)
        canvas.drawString(42, 24, "SUPPLYCHAIN AI | " + ("Supplied artifact analysis" if verified else "DEMO UI DATA"))
        canvas.drawRightString(552, 24, str(doc.page))
        canvas.restoreState()
    while flow and isinstance(flow[-1], Spacer):
        flow.pop()
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    from services.audit_log import record
    record('report_generated',rows=len(df))
    return buffer.getvalue()
