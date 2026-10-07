"""Actual connected-browser commands, anomalies and executive PDF evidence."""
import json,sys,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pymupdf
from playwright.sync_api import sync_playwright,expect
expect.set_options(timeout=60000)
from master_browser_qa import navigate,settled,click,select


def run():
    checks=[];errors=[];started=time.perf_counter()
    folder=ROOT/'tmp/pdfs/executive';folder.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as engine:
        browser=engine.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        page.set_default_timeout(60000);page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:8501/?page=landing')
        page.locator('.st-key-landing_open_platform button').click();settled(page)
        expander=page.get_by_text('Observed anomalies and their reference',exact=True).locator('xpath=ancestor::details[1]')
        expander.locator('summary').click()
        select(page,'anomaly_measure_None','Sales')
        if expander.get_attribute('open') is None:expander.locator('summary').click()
        expect(page.get_by_text('IQR of observed day bins; sum of Sales',exact=False)).to_be_visible()
        checks.append('Observed Sales anomaly reference rendered in the connected overview')
        navigate(page,'copilot')
        chat=page.locator('.st-key-copilot_input textarea')
        chat.fill('show table');chat.press('Enter')
        expect(page.locator('.st-key-copilot_answer_0')).to_contain_text('first 500 records')
        settled(page);checks.append('Typed local table command renders bounded connected results')
        chat.fill('filter Market to Pacific Asia');chat.press('Enter')
        click(page.locator('.st-key-copilot_command_1 button'));settled(page)
        expect(page.locator('.st-key-filter_active_summary')).to_contain_text('Pacific Asia')
        checks.append('Validated command applies an available Market filter')
        chat.fill('clear filters');chat.press('Enter')
        click(page.locator('.st-key-copilot_command_2 button'));settled(page)
        expect(page.locator('.st-key-filter_active_summary')).not_to_contain_text('Pacific Asia')
        checks.append('Clear-filter command restores the broader source context')
        navigate(page,'reports')
        click(page.locator('.st-key-connected_brief_generate button'))
        download=page.get_by_role('button',name='Download connected executive briefing',exact=True)
        expect(download).to_be_visible();settled(page)
        with page.expect_download() as result:download.click()
        payload=Path(result.value.path()).read_bytes();(folder/'connected-briefing.pdf').write_bytes(payload)
        document=pymupdf.open(stream=payload,filetype='pdf');text='\n'.join(p.get_text() for p in document)
        for title in ['Delivery orders','Demand product/day web visits','Profitability line observations','Final-delivery line observations','WHAT CHANGED','WHAT TO INVESTIGATE NEXT']:
            assert title in text,title
        for index,part in enumerate(document):part.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(str(folder/f'page-{index+1}.png'))
        checks.append('Actual four-source executive PDF downloaded, parsed and every page rendered')
        assert not errors,errors
        browser.close()
    report={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'browser_errors':errors,
            'pdf_pages':len(document),'pdf_visual_inspection':'pending','elapsed_seconds':round(time.perf_counter()-started,2),
            'scope':'Isolated local Chrome session; current connected data; no provider request or private-account creation'}
    (ROOT/'metadata/master_workflow_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':run()
