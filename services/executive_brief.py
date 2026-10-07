"""Evidence-backed management brief keeping independent source grains separate."""
from datetime import datetime,timezone
from io import BytesIO
from xml.sax.saxutils import escape
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
from services.privacy import minimize,safe_text
from services.decision_intelligence import momentum,priorities
from services.provider import filter_description

FAMILIES={'delivery':'Delivery orders','demand':'Demand product/day web visits','profitability':'Profitability line observations','delivery_final':'Final-delivery line observations'}


def build(frames,filters):
    if set(frames)-set(FAMILIES):raise ValueError('Only registered connected source families belong in this briefing.')
    sources=[]
    for family,raw in frames.items():
        frame=minimize(raw)
        if not frame.attrs.get('verified_artifacts'):raise ValueError('The connected briefing requires actual registered source data.')
        evidence=[]
        def fact(label,value,unit):
            if value is not None and np.isfinite(value):evidence.append({'id':family+'-E'+str(len(evidence)+1),'label':label,'value':float(value),'unit':unit})
        fact('Selected observations',len(frame),'records at the stated source grain')
        if 'Order' in frame:fact('Distinct orders',frame.Order.nunique(),'unique keys within this source')
        for metric in ['Sales','Profit','Forecast Demand','Actual Demand']:
            if metric in frame:
                values=pd.to_numeric(frame[metric],errors='coerce').replace([np.inf,-np.inf],np.nan)
                fact(metric+' valid observations',values.notna().sum(),'records')
                fact('Total '+metric,values.sum(min_count=1),'web visits' if 'Demand' in metric else 'source financial units')
        if 'Risk Probability' in frame:
            values=pd.to_numeric(frame['Risk Probability'],errors='coerce').replace([np.inf,-np.inf],np.nan)
            fact('Scored observations',values.count(),'records');fact('Unscored observations',len(frame)-values.count(),'records')
            fact('Mean supplied risk probability',values.mean(),'probability; scored rows only')
        if {'Actual Demand','Forecast Demand'}.issubset(frame):
            pairs=frame[['Actual Demand','Forecast Demand']].apply(pd.to_numeric,errors='coerce').replace([np.inf,-np.inf],np.nan).dropna()
            actual=pairs['Actual Demand'].sum()
            fact('Forecast WAPE',abs(pairs['Forecast Demand']-pairs['Actual Demand']).sum()/actual if actual>0 else None,'ratio; aligned finite observations')
        change=None
        signal=next((c for c in ['Risk Probability','Forecast Demand','Profit','Sales'] if c in frame),None)
        if signal:
            try:
                value=momentum(frame,signal,'Mean' if 'Probability' in signal else 'Sum','Month')
                change={k:v for k,v in value.items() if k!='series'}
            except ValueError:pass
        dimension=next((c for c in ['Market','Category','Region','Product'] if c in frame),None)
        queue=[];priority_method=None
        if dimension and 'Risk Probability' in frame:
            try:
                ranking,priority_method=priorities(frame,dimension)
                queue=ranking.head(5).to_dict('records')
            except ValueError:pass
        sources.append({'family':family,'title':FAMILIES[family],'source':frame.attrs.get('data_source','Registered artifact'),
                        'period':str(frame.Date.min())+' to '+str(frame.Date.max()) if 'Date' in frame and not frame.empty else 'No selected dated observations',
                        'filters':filter_description(filters.get(family,{}),'All source records'),
                        'evidence':evidence,'change':change,'priority_dimension':dimension,'priorities':queue,'priority_method':priority_method,
                        'model_note':frame.attrs.get('evaluation_note','Source-provided outputs; see Model Health')})
    return {'generated_utc':datetime.now(timezone.utc).isoformat(),'sources':sources,
            'cross_risk':'Source families are reported independently. No sum across order, line-observation and product/day grains or forced cross-source join is made.',
            'limitations':'Historical observations and model estimates are not causal evidence or guarantees. Probability is not monetary loss. Missing scores/inputs and unverified uncertainty remain unavailable.'}


def pdf(brief):
    from services.access_control import require
    require('export')
    output=BytesIO();styles=getSampleStyleSheet();styles['Title'].textColor=colors.HexColor('#182b4a')
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    def text(value,style='BodyText'):return Paragraph(escape(safe_text(value)),styles[style])
    flow=[text('SUPPLYCHAIN AI | Connected Executive Briefing','Title'),text('Generated UTC: '+brief['generated_utc']),text(brief['cross_risk']),Spacer(1,12)]
    for index,source in enumerate(brief['sources']):
        if index:flow.append(PageBreak())
        flow += [text(source['title'],'Heading1'),text('Source: '+source['source']),text('Period: '+source['period']),text('Filters: '+source['filters']),Spacer(1,8)]
        change=source['change']
        flow += [text('WHAT CHANGED','Heading2'),text(f"{change['measure']}: latest observed month level {change['level']:.6g}; change {change['momentum']:+.6g} {change['change_units']}; acceleration {change['acceleration']:+.6g}. Reference periods: {', '.join(change['periods'])}. {change['note']}" if change else 'Insufficient comparable monthly observations for a three-period momentum reference.')]
        flow += [text('WHY IT MATTERS','Heading2'),text('Coverage and observed amounts show the scale of this selected source. Scores describe model output on scored observations; review coverage before interpreting risk.')]
        flow += [text('WHERE','Heading2'),text('Current source and filters above. Investigation grouping: '+str(source['priority_dimension'] or 'No validated grouping available')+'.')]
        flow.append(text('HOW LARGE | KPI EVIDENCE','Heading2'))
        for fact in source['evidence']:flow.append(text(f"[{fact['id']}] {fact['label']}: {fact['value']:,.6g} ({fact['unit']})."))
        flow += [text('WHAT TO WATCH','Heading2'),text(source['model_note']),text(brief['limitations'])]
        flow.append(text('WHAT TO INVESTIGATE NEXT','Heading2'))
        if source['priorities']:
            flow.append(text(source['priority_method']['formula']))
            for row in source['priorities']:
                flow.append(text(str(row[source['priority_dimension']])+f": priority {row['Investigation priority']:.3f}; scored observations {row['Scored_records']}; mean probability {row['Severity']:.5f}."))
            flow.append(text(source['priority_method']['limitation']))
        else:flow.append(text('Review the selected observations and coverage; no calibrated risk investigation queue is available for this source.'))
        flow.append(Spacer(1,16))
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawString(40,24,'SUPPLYCHAIN AI | Separate grains, traceable evidence');canvas.drawRightString(555,24,str(doc.page))
    SimpleDocTemplate(output,pagesize=(595,842),leftMargin=40,rightMargin=40,topMargin=40,bottomMargin=40).build(flow,onFirstPage=footer,onLaterPages=footer)
    from services.audit_log import record
    record('report_generated')
    return output.getvalue()
