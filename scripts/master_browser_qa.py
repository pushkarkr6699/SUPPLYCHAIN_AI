"""Final isolated-browser journey through old pages and actual-data lab features."""
import io,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pandas as pd
from playwright.sync_api import sync_playwright,expect
expect.set_options(timeout=60000)
from workspace_usability_qa import settled as _settled,theme
from views.registry import PAGES

OUT=ROOT/'tmp/screenshots/master';OUT.mkdir(parents=True,exist_ok=True)
class Checks(list):
    def append(self,item):
        super().append(item);print(item,flush=True)
checks=Checks();errors=[]


def settled(page):
    page.wait_for_timeout(250);_settled(page);page.wait_for_timeout(100)
    expect(page.get_by_test_id('stException')).to_have_count(0)
    assert not page.get_by_text('This page could not be displayed',exact=False).count()


def navigate(page,route):
    button=page.locator('.st-key-nav_'+route+' button')
    if not button.is_visible():
        parent=button.locator('xpath=ancestor::details[1]')
        if parent.count() and parent.get_attribute('open') is None:parent.locator('summary').click()
    button.click();page.get_by_role('heading',name=PAGES[route][0],level=1,exact=True).wait_for(state='attached',timeout=60000);settled(page)


def upload(page,data,name):
    page.locator('[class*="st-key-upload_file_"] input[type=file]').set_input_files({'name':name,'mimeType':'application/octet-stream','buffer':data})
    page.get_by_text('Imported ',exact=False).first.wait_for(timeout=30000);settled(page)


def select(page,key,value):
    field=page.locator('.st-key-'+key).get_by_role('combobox');field.focus();field.press('ArrowDown')
    page.get_by_role('option',name=value,exact=True).click();settled(page)


def expose(locator):
    """Open native disclosure ancestors as a user would before interacting."""
    parents=locator.locator('xpath=ancestor::details')
    for index in range(parents.count()):
        parent=parents.nth(index)
        if parent.get_attribute('open') is None:parent.locator('summary').first.click()
    if locator.get_attribute('type')!='file':locator.scroll_into_view_if_needed()


def click(locator):
    expose(locator);locator.click()


def main():
    from urllib.request import urlopen
    deadline=time.monotonic()+20
    while True:
        try:
            with urlopen('http://127.0.0.1:8501/_stcore/health',timeout=2) as response:assert response.status==200
            break
        except Exception:
            if time.monotonic()>deadline:raise
            time.sleep(.3)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_default_timeout(60000)
        page.goto('http://127.0.0.1:8501/?page=landing');settled(page)
        page.screenshot(path=str(OUT/'landing.png'))
        page.locator('.st-key-landing_open_platform button').click();settled(page)
        routes=['overview','delivery','demand','profitability','cross_risk','orders','explorer','geography','changes','scenarios','copilot','insights','alerts','models','explainability','threshold','drift','health','quality','lineage','data','reports','downloads','settings','comparison','visualizations','uploads']
        if '--lab-only' in sys.argv:routes=['settings','comparison','visualizations','uploads']
        if '--board-diagnosis' in sys.argv:routes=['uploads']
        for route in routes:
            navigate(page,route);checks.append('Navigation and rendered page: '+route);print(checks[-1],flush=True)
        actual=pd.read_csv(ROOT/'data/delivery/final/DataCo_Final_Order_Level_Dataset.csv').head(60)[['Order Id','Order_Date','Market','Sales']]
        buffer=io.BytesIO();actual.to_parquet(buffer,index=False)
        upload(page,buffer.getvalue(),'actual-orders.parquet')
        expect(page.get_by_text('Imported 60 rows and 4 columns.',exact=False)).to_be_visible()
        checks.append('Actual Parquet records profiled and prepared')
        select(page,'upload_date','Order_Date')
        page.get_by_role('button',name='Apply field types',exact=True).click();settled(page)
        # Wait for the date-specific output, not the previous run's idle flag.
        expect(page.get_by_test_id('stPlotlyChart')).to_have_count(3,timeout=60000)
        if '--pdf-only' in sys.argv:
            click(page.locator('.st-key-viz_upload_raw_pdf_create button'));settled(page)
            button=page.locator('.st-key-viz_upload_raw_pdf_download button')
            expose(button)
            try:
                with page.expect_download(timeout=15000) as result:button.click(timeout=5000)
                print('PDF-only download passed: '+result.value.suggested_filename,flush=True)
            except Exception:
                page.screenshot(path=str(OUT/'pdf-click-debug.png'))
                result=button.evaluate("e=>{const b=e.getBoundingClientRect();return {visible:e.checkVisibility(),rect:b.toJSON(),ancestors:[...function*(n){while(n){yield n;n=n.parentElement}}(e)].slice(0,10).map(n=>({tag:n.tagName,testid:n.dataset.testid,open:n.getAttribute('open'),rect:n.getBoundingClientRect().toJSON()})),hit:document.elementsFromPoint(b.x+b.width/2,b.y+b.height/2).map(n=>({tag:n.tagName,class:n.className,testid:n.dataset.testid}))}}")
                print(json.dumps(result,indent=2),flush=True);raise
            browser.close();return
        choices=['Vertical bars','Horizontal bars','Line','Area','Treemap','Histogram','Box plot','Violin plot','ECDF','Donut']
        box=page.locator('.st-key-viz_upload_raw_charts')
        box.get_by_role('button',name='Clear all',exact=True).click()
        # Set native multiselect options through its visible option labels.
        for kind in choices:
            box.get_by_role('button',name='Open',exact=True).click()
            option=page.get_by_role('option',name=kind,exact=True)
            option.click()
            page.keyboard.press('Escape')
        page.get_by_role('button',name='Build visualizations',exact=True).click();settled(page)
        print('Chart cards: '+str(page.locator('[class*="st-key-viz_upload_raw_card_"] h3').all_text_contents()),flush=True)
        print('Chart notices: '+str(page.get_by_test_id('stAlert').all_text_contents()),flush=True)
        page.screenshot(path=str(OUT/'board-built.png'))
        expect(page.get_by_test_id('stPlotlyChart')).to_have_count(10,timeout=30000)
        page.screenshot(path=str(OUT/'ten-chart-board.png'))
        checks.append('Ten simultaneous real-data charts with visible toolbars')
        print(checks[-1],flush=True)
        first=page.get_by_test_id('stPlotlyChart').first
        assert first.locator('.modebar').is_visible()
        with page.expect_download() as dl:click(page.locator('.st-key-viz_upload_raw_settings button'))
        settings=Path(dl.value.path()).read_bytes()
        click(page.locator('.st-key-viz_upload_raw_reset button'));settled(page)
        expect(page.get_by_test_id('stPlotlyChart')).to_have_count(3)
        restore=page.locator('.st-key-viz_upload_raw_restore input[type=file]')
        expose(restore);restore.set_input_files({'name':'settings.json','mimeType':'application/json','buffer':settings})
        settled(page);click(page.locator('.st-key-viz_upload_raw_restore_apply button'));settled(page)
        expect(page.get_by_test_id('stPlotlyChart')).to_have_count(10)
        checks.append('Exported settings restored against the same source and schema')
        click(page.locator('.st-key-viz_upload_raw_remove_9 button'));settled(page)
        expect(page.get_by_test_id('stPlotlyChart')).to_have_count(9)
        click(page.locator('.st-key-viz_upload_raw_duplicate_0 button'));settled(page)
        expect(page.get_by_test_id('stPlotlyChart')).to_have_count(10)
        checks.append('Chart deletion and duplication preserve remaining data context')
        question=page.locator('.st-key-upload_raw_local_question input')
        expose(question);question.fill('top 3 Market by total Sales')
        question.press('Enter');settled(page)
        expect(page.get_by_text('Computed method: top-N',exact=True)).to_be_visible()
        checks.append('Local Sevika question computes an actual uploaded-field ranking')
        with page.expect_download() as dl:
            click(page.locator('.st-key-viz_upload_raw_pdf_create button'));settled(page)
            click(page.locator('.st-key-viz_upload_raw_pdf_download button'))
        assert dl.value.suggested_filename=='analysis_brief.pdf'
        import pymupdf
        folder=ROOT/'tmp/pdfs/master-lab';folder.mkdir(parents=True,exist_ok=True)
        payload=Path(dl.value.path()).read_bytes();(folder/'analysis-brief.pdf').write_bytes(payload)
        document=pymupdf.open(stream=payload,filetype='pdf')
        for index,part in enumerate(document):part.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(str(folder/('page-'+str(index+1)+'.png')))
        checks.append('Current selection analysis PDF generated and downloaded')
        page.locator('.st-key-sevika_launcher [data-testid=stPopoverButton]').click()
        panel=page.get_by_test_id('stPopoverBody')
        expect(panel.get_by_text('60 selected records',exact=False)).to_be_visible()
        assert panel.get_by_role('radio',name='Live AI',exact=True).count()==0
        page.keyboard.press('Escape');checks.append('Floating Sevika follows uploads locally and enforces file-specific live consent')
        for choice,width in [('Light',390),('Dark',320)]:
            theme(page,choice);settled(page)
            if page.get_by_test_id('stSidebar').get_attribute('aria-expanded')=='true':page.locator('[data-testid=stSidebarCollapseButton] button').click()
            page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(400)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            assert page.evaluate("getComputedStyle(document.querySelector('.page-heading')).animationDuration==='0s'")
            page.screenshot(path=str(OUT/(choice.lower()+'-'+str(width)+'.png')))
            page.set_viewport_size({'width':1440,'height':1000})
            # Restore the sidebar when a previous narrow capture collapsed it.
            expand=page.locator('button[data-testid="stExpandSidebarButton"], [data-testid="stExpandSidebarButton"] button')
            if page.get_by_test_id('stSidebar').get_attribute('aria-expanded')!='true':
                expect(expand).to_be_visible();expand.click()
                expect(page.get_by_test_id('stSidebar')).to_have_attribute('aria-expanded','true')
        checks.append('Light/dark 390px/320px layouts and reduced motion')
        page.locator('.st-key-sidebar_logout button').click();settled(page)
        expect(page.get_by_role('button',name='Continue in Demo Mode',exact=True)).to_be_visible()
        checks.append('Logout returns to login and clears the workspace session')
        assert not errors,errors
        browser.close()
    result={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'browser_errors':errors,'screenshots':str(OUT.relative_to(ROOT)), 'analysis_pdf_pages':len(document),'analysis_pdf_visual_inspection':'pending'}
    (ROOT/'metadata/master_browser_qa.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
