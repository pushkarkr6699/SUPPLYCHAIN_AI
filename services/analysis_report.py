"""In-memory, privacy-minimized analytical briefs for an active board."""
from io import BytesIO
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from services.privacy import minimize, safe_text
from services.visualization_config import signature
from services.visualization_service import summary, units


def create(frame,dataset,plan):
    frame=minimize(frame)
    table=minimize(summary(frame,plan['groups'],plan['metrics'],plan['operation'],plan['period'],plan['limit']))
    output=BytesIO()
    doc=SimpleDocTemplate(output,pagesize=(595,842),leftMargin=40,rightMargin=40,topMargin=42,bottomMargin=42,title='SupplyChain AI - Analysis Brief')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Meta',fontSize=8,leading=11,textColor=colors.HexColor('#52627a')))
    styles['Title'].textColor=colors.HexColor('#182b4a')
    def text(value,style='BodyText'):
        return Paragraph(escape(safe_text(value)),styles[style])
    source=signature(frame,dataset)
    flow=[text('SUPPLYCHAIN AI | DECISION INTELLIGENCE','Meta'),Spacer(1,14),text('Analysis Brief','Title'),
          text('Generated UTC: '+datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'),'Meta'),
          text('Source: '+str(frame.attrs.get('data_source','Current dataset')),'Meta'),
          text('Dataset version: '+source['version'],'Meta'),
          text(f'{len(frame):,} selected records | {len(table):,} analysis groups | {plan["operation"]} | {plan["period"]} interval','Meta'),Spacer(1,14),
          text('This report uses the exact active selection supplied by the workspace. No records from a different dataset or unselected period are included. Missing measures are not imputed as zero.'),Spacer(1,12),
          text('Selected visualizations','Heading2'),text(', '.join(plan['charts'])),
          text('Measures: '+'; '.join(c+' ('+units(c,frame)+')' for c in plan['metrics'])),Spacer(1,14)]
    if 'Date' in frame:flow.append(text('Date selection: '+str(frame.Date.min())+' to '+str(frame.Date.max()),'Meta'))
    columns=[*plan['groups'],*plan['metrics'],'Records']
    rows=[[text(c,'Meta') for c in columns]]
    for _,row in table.head(40).iterrows():rows.append([text(str(row[c])[:160],'Meta') for c in columns])
    display=Table(rows,colWidths=[515/len(columns)]*len(columns),repeatRows=1,hAlign='LEFT')
    display.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6edf7')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6fa')]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    flow += [text('Computed analysis table','Heading2'),display,text(f'First {min(40,len(table)):,} of {len(table):,} groups. The analysis CSV includes all groups.','Meta'),Spacer(1,14),
             text('Interpretation and model limitations','Heading2'),
             text('Observed associations are not causal evidence. Charts may have disclosed display/sample limits; the analysis table uses all selected records. Probabilities are not monetary loss. No future forecast or model quality is inferred from a visualization.'),
             text(frame.attrs.get('evaluation_note','No model was executed to produce this board.')),
             text('Credentials and personal contact fields are excluded from this report. Session uploads are not added to the canonical project datasets.','Meta')]
    def footer(canvas,document):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#52627a'))
        canvas.drawString(40,24,'SUPPLYCHAIN AI | Analytical evidence, not decision guarantees')
        canvas.drawRightString(555,24,str(document.page))
    doc.build(flow,onFirstPage=footer,onLaterPages=footer)
    from services.audit_log import record
    record('report_generated',rows=len(frame),charts=len(plan['charts']))
    return output.getvalue()
