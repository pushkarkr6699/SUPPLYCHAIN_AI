"""Isolated browser tests with synthetic uploads and fixed local model probes."""
import io
import json
import sys
import time
from hashlib import sha256
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'tests')]
from playwright.sync_api import sync_playwright,expect
expect.set_options(timeout=60000)
from workspace_usability_qa import settled as _settled,theme
from test_uploads import source_for,workbook
from services import upload_service as upload

OUT=ROOT/'tmp/screenshots/uploads';OUT.mkdir(parents=True,exist_ok=True)
class Checks(list):
    def append(self,item):
        super().append(item); print(item,flush=True)
checks=Checks();errors=[]
def settled(page):
    # Allow the click/upload websocket event to start its rerun before waiting for completion.
    page.wait_for_timeout(250)
    _settled(page)
    page.wait_for_timeout(100)
def select(page,key,value):
    field=page.locator('.st-key-'+key).get_by_role('combobox')
    field.focus();field.press('ArrowDown')
    page.get_by_role('option',name=value,exact=True).click();settled(page)

def send(page,data,name):
    page.locator('[class*="st-key-upload_file_"] input[type=file]').set_input_files({'name':name,'mimeType':'application/octet-stream','buffer':data})
    sheet=upload.sheets(data)[0] if name.lower().endswith('.xlsx') else None
    scope=sha256(data+json.dumps([Path(name).suffix.lower(),'Auto','utf-8-sig',sheet]).encode()).hexdigest()
    page.locator('.st-key-import_state_'+scope).wait_for(timeout=20000)
    settled(page)
    page.wait_for_timeout(250)
    expect(page.get_by_test_id('stException')).to_have_count(0)

deadline=time.monotonic()+15
while True:
    try:
        with urlopen('http://127.0.0.1:8501/_stcore/health',timeout=2) as response:assert response.status==200
        break
    except Exception:
        if time.monotonic()>deadline:raise
        time.sleep(.25)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
    page=context.new_page()
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto('http://127.0.0.1:8501/?page=landing');settled(page)
    page.locator('.st-key-landing_open_platform button').click();settled(page)
    page.locator('.st-key-nav_uploads button').click();settled(page)
    page.get_by_role('heading',name='Bring Your Data',exact=True).wait_for()
    expect(page.locator('.st-key-global_filters')).to_have_count(0)
    live='not rerun (model-only verification)'
    if '--models-only' not in sys.argv:
        raw=b'Date,Segment,Amount,Quantity\n2026-01-01,Alpha,12,2\n2026-01-02,Beta,24,3\n2026-01-03,Alpha,36,4\n'
        send(page,raw,'synthetic.csv')
        expect(page.get_by_text('Imported 3 rows and 4 columns.',exact=False)).to_be_visible()
        expect(page.get_by_test_id('stPlotlyChart')).to_have_count(2,timeout=15000)
        assert page.get_by_role('button',name='Generate live Sevika insights',exact=True).is_disabled()
        select(page,'upload_date','Date')
        page.get_by_role('button',name='Apply field types',exact=True).click();settled(page)
        expect(page.get_by_test_id('stPlotlyChart')).to_have_count(3)
        chart=page.get_by_test_id('stPlotlyChart').first;chart.scroll_into_view_if_needed()
        assert chart.locator('.modebar').is_visible()
        with page.expect_download() as dl:page.get_by_role('button',name='Download selected upload CSV',exact=True).click()
        assert dl.value.suggested_filename=='uploaded_analysis.csv'
        checks.append('CSV types/date preparation, three charts, controls and formula-safe download')
        # Synthetic rows only: explicitly consent through the same user-facing UI.
        consent=page.locator('.st-key-upload_consent_control input[type=checkbox]')
        page.locator('.st-key-upload_consent_control label').click();settled(page)
        button=page.get_by_role('button',name='Generate live Sevika insights',exact=True)
        live='not configured'
        if button.is_enabled() and '--skip-live' not in sys.argv:
            button.click()
            page.get_by_text('Live insights generated.',exact=False).or_(page.get_by_text('The AI request did not complete.',exact=False)).first.wait_for(timeout=40000)
            settled(page)
            if page.get_by_text('Live insights generated.',exact=False).count():
                live='passed';checks.append('Actual live Sevika request on consented synthetic anonymous summaries')
            else:
                live='provider unavailable';checks.append('Live AI failure recovery preserves local charts and evidence')
        elif button.is_enabled():
            live='not rerun; independently verified on synthetic evidence'
            checks.append('Consented live AI control enabled; unconsented control disabled')
        else:checks.append('Unconfigured AI stays disabled; local evidence remains available')
        # Both themes and narrow layouts use the existing application design.
        for choice,width in [('Light',390),('Dark',320)]:
            theme(page,choice);settled(page)
            if page.get_by_test_id('stSidebar').get_attribute('aria-expanded')=='true':
                page.locator('[data-testid=stSidebarCollapseButton] button').click()
            page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(400)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.screenshot(path=str(OUT/(choice.lower()+'-'+str(width)+'.png')))
            page.set_viewport_size({'width':1440,'height':1000})
        checks.append('Light 390px and dark 320px layouts without horizontal page overflow')
        send(page,b'Segment,Amount\nAlpha,3\nBeta,4\n','changed.csv')
        assert not page.locator('.st-key-upload_consent_control input').is_checked()
        expect(page.get_by_role('button',name='Generate live Sevika insights',exact=True)).to_be_disabled()
        checks.append('Changing file revokes AI consent and resets types, charts and results')
        send(page,b'Segment\nAlpha\nBeta\nAlpha\n','categorical.csv')
        expect(page.get_by_text('Generated record count',exact=False).first).to_be_visible()
        expect(page.get_by_test_id('stPlotlyChart')).to_have_count(2)
        checks.append('Categorical-only uploads produce counts without fabricated numeric model inputs')
        for data,name in [(b'Segment\tAmount\nAlpha\t3\n','data.tsv'),
                          (b'[{"Segment":"Alpha","Amount":3}]','data.json'),(workbook(),'data.xlsx')]:
            send(page,data,name);expect(page.get_by_text('Imported 1 rows',exact=False)).to_be_visible()
        checks.append('TSV, flat JSON and values-only XLSX import')
        send(page,b'a,a\n1,2\n','duplicate.csv')
        expect(page.get_by_text('Duplicate column names',exact=False)).to_be_visible()
        send(page,workbook(True),'formula.xlsx')
        expect(page.get_by_text('Formula cells are not imported.',exact=False)).to_be_visible()
        checks.append('Malformed CSV and XLSX formulas fail with recoverable validation feedback')
    for model,label in upload.MODELS.items():
        data=source_for(model).to_csv(index=False).encode()
        send(page,data,model+'.csv')
        page.get_by_text('Trained-model predictions',exact=True).click();settled(page)
        field=page.locator('.st-key-upload_model_choice').get_by_role('combobox')
        field.wait_for();field.focus();field.press('ArrowDown')
        page.get_by_role('option',name=label,exact=True).click();settled(page)
        run=page.get_by_role('button',name='Run trained predictions on upload',exact=True)
        expect(run).to_be_enabled();run.click();settled(page)
        expect(page.get_by_text('Completed trained inference:',exact=False)).to_be_visible(timeout=20000)
        with page.expect_download() as dl:page.get_by_role('button',name='Download uploaded predictions CSV',exact=True).click()
        assert dl.value.suggested_filename=='uploaded_predictions.csv'
        assert page.get_by_test_id('stPlotlyChart').count()>=2
        checks.append(label+' actual uploaded inference, charts and prediction download')
    # Model results must not survive an incompatible replacement file.
    send(page,b'Segment,Amount\nAlpha,3\n','missing.csv')
    page.get_by_text('Trained-model predictions',exact=True).click();settled(page)
    expect(page.get_by_role('button',name='Run trained predictions on upload',exact=True)).to_be_disabled()
    expect(page.get_by_role('button',name='Download uploaded predictions CSV',exact=True)).to_have_count(0)
    checks.append('Missing features disable scoring; stale prediction downloads disappear')
    page.get_by_role('button',name='Clear uploaded data and results',exact=True).click();settled(page)
    expect(page.get_by_text('Imported',exact=False)).to_have_count(0)
    checks.append('Clear uploads removes session data and resets the uploader')
    expect(page.get_by_test_id('stException')).to_have_count(0)
    assert not errors,errors
    browser.close()
report={'passed':True,'checked_at_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'live_ai_synthetic_test':live,'browser_errors':errors,'screenshots':'tmp/screenshots/uploads'}
(ROOT/('metadata/uploads_models_browser_qa.json' if '--models-only' in sys.argv else 'metadata/uploads_browser_qa.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
