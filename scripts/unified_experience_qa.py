"""Browser checks for the integrated public/login/workspace experience."""
import json
import sys
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, expect
from workspace_usability_qa import ROOT, BASE, settled, theme, MEASURE

REPORT = ROOT / 'metadata/unified_experience_qa.json'
OUTPUT = ROOT / 'tmp/screenshots/unified-experience'


def ready(page):
    settled(page)
    page.wait_for_timeout(500)
    page.wait_for_function("()=>document.getAnimations().filter(a=>['sc-enter','sc-surface'].includes(a.animationName)).every(a=>a.playState!=='running')")
    assert page.locator('[data-testid="stException"]').count() == 0


def geometry(page):
    return page.evaluate('''()=>Object.fromEntries(['stSidebar','stMain'].map(id=>{const e=document.querySelector(`[data-testid="${id}"]`);return [id,e.getBoundingClientRect().toJSON()]}))''')


def contrast(page):
    failures=page.evaluate(MEASURE)['contrast_failures']
    assert not failures, failures




def complete_preferences(page, report):
    page.emulate_media(reduced_motion='reduce');ready(page)
    assert page.locator('.page-heading h1').evaluate('e=>getComputedStyle(e).animationName')=='none'
    assert page.locator('[data-testid="stSidebar"]').evaluate('e=>getComputedStyle(e).transitionDuration')=='0s'
    report['checks'].append('Device reduced-motion disables page and sidebar animations')
    page.emulate_media(reduced_motion='no-preference')
    system=page.locator('[data-testid="stSidebar"] summary').filter(has_text='Settings & system')
    system.click();page.locator('.st-key-nav_settings button').click();ready(page)
    page.get_by_text('Interface animations',exact=True).click();ready(page)
    expect(page.get_by_role('switch',name='Interface animations',exact=True)).not_to_be_checked()
    assert page.locator('.page-heading h1').evaluate('e=>getComputedStyle(e).animationName')=='none'
    page.get_by_role('switch',name='Interface animations',exact=True).focus()
    page.get_by_role('switch',name='Interface animations',exact=True).press('Space');ready(page)
    expect(page.get_by_role('switch',name='Interface animations',exact=True)).to_be_checked()
    report['checks'].append('Interface animations preference disables/enables workspace motion')
    page.locator('.st-key-sidebar_logout button').click();ready(page)
    expect(page.locator('.st-key-login_password input')).to_have_value('')
    page.locator('.st-key-login_back button').click();ready(page)
    expect(page.locator('.st-key-public_header')).to_be_visible()
    page.locator('.st-key-landing_open_platform button').click();ready(page)
    expect(page.locator('.st-key-top_header')).to_be_visible()
    report['checks'].append('Logout -> cleared login -> website -> Open platform remains connected')


def run(finish_only=False):
    OUTPUT.mkdir(parents=True,exist_ok=True)
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':False,'checks':[],'errors':[],'geometry':{}}
    if finish_only:
        report=json.loads(REPORT.read_text(encoding='utf-8'))
        assert len(report['checks']) >= 6, 'Run the full audit before resuming preference checks'
        report.pop('failure',None)
        report['completion_checked_at']=datetime.now(timezone.utc).isoformat()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
            page=browser.new_page(viewport={'width':1512,'height':1060},reduced_motion='no-preference',color_scheme='light')
            page.on('pageerror',lambda e: report['errors'].append(str(e)))
            page.goto(BASE+'/?page=landing');ready(page)
            if finish_only:
                page.locator('.st-key-landing_open_platform button').click();ready(page)
                complete_preferences(page,report)
                assert not report['errors'],report['errors']
                report['checks']=list(dict.fromkeys(report['checks']))
                report['passed']=True;browser.close();return
            expect(page.locator('.st-key-public_header .brand-network')).to_have_count(1)
            assert page.locator('.hero h1').evaluate('e=>getComputedStyle(e).animationName')=='sc-enter'
            page.screenshot(path=str(OUTPUT/'landing.png'))
            page.locator('.st-key-landing_signin button').click();ready(page)
            expect(page.locator('.st-key-auth_header .brand-network')).to_have_count(1)
            assert page.locator('.auth-brand h1').evaluate('e=>getComputedStyle(e).animationName')=='sc-enter'
            page.locator('.st-key-login_submit button').click();ready(page)
            expect(page.get_by_text('Enter a demo username and password, or continue in Demo Mode.')).to_be_visible()
            page.locator('.st-key-forgot_password button').click();ready(page)
            expect(page.get_by_text('Password recovery will be available when an authentication provider is connected.')).to_be_visible()
            page.screenshot(path=str(OUTPUT/'login.png'))
            page.locator('.st-key-login_username input').fill('UI QA')
            page.locator('.st-key-login_password input').fill('sample-only')
            page.locator('.st-key-login_submit button').click()
            page.locator('.st-key-table_footer_overview').wait_for(timeout=60000);ready(page)
            expect(page.locator('.brand .brand-network')).to_have_count(1)
            assert page.locator('.page-heading h1').evaluate('e=>getComputedStyle(e).animationName')=='sc-enter'
            report['checks'].append('Landing -> login validation/recovery -> session sign-in -> dashboard; shared brand and entry motion')
            for choice in ['Light','Dark','System']:
                if choice=='System':page.emulate_media(color_scheme='dark')
                theme(page,choice);ready(page)
                sidebar=page.locator('[data-testid="stSidebar"]')
                summaries=sidebar.locator('summary')
                for i in range(summaries.count()):
                    summary=summaries.nth(i)
                    if not summary.evaluate('e=>e.parentElement.open'):summary.click()
                    page.wait_for_timeout(220)
                    summary.hover();contrast(page)
                    summary.focus();page.mouse.move(1000,20);contrast(page)
                    summary.click();page.wait_for_timeout(220);contrast(page)
                summaries.first.click();ready(page)
                page.locator('.st-key-nav_cross_risk button').click();ready(page);contrast(page)
                expect(page.locator('.st-key-nav_cross_risk button')).to_have_attribute('data-testid','stBaseButton-primary')
                page.screenshot(path=str(OUTPUT/f'sidebar-{choice.lower()}.png'))
                page.locator('.st-key-nav_overview button').click();ready(page)
            report['checks'].append('All seven sidebar groups: expanded, hover, keyboard focus, collapsed and selected child contrast in Light/Dark/System')
            theme(page,'Light');page.emulate_media(color_scheme='light');ready(page)
            for width in [1512,1366,820,390,320]:
                page.set_viewport_size({'width':width,'height':1060});ready(page)
                sidebar=page.locator('[data-testid="stSidebar"]')
                if sidebar.get_attribute('aria-expanded')!='true':
                    page.locator('[data-testid="stExpandSidebarButton"]').click();ready(page)
                opened=geometry(page)
                page.locator('[data-testid="stSidebarCollapseButton"] button').click();ready(page)
                expect(sidebar).to_have_attribute('aria-expanded','false')
                closed=geometry(page)
                assert closed['stSidebar']['width']<1,closed
                assert abs(closed['stMain']['x'])<1 and abs(closed['stMain']['width']-width)<2,closed
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                report['geometry'][str(width)]={'open':opened,'closed':closed}
                page.screenshot(path=str(OUTPUT/f'closed-{width}.png'))
                page.locator('[data-testid="stExpandSidebarButton"]').click();ready(page)
                assert geometry(page)['stSidebar']['width']>=255
            report['checks'].append('Sidebar repeatedly closes to zero reserved width and reopens at 1512/1366/820/390/320px')
            page.set_viewport_size({'width':1512,'height':1060});ready(page)
            baseline=page.locator('.st-key-dashboard').bounding_box()['width']
            page.locator('.st-key-header_copilot button:visible').click();ready(page)
            expect(page.locator('.st-key-copilot_drawer')).to_be_visible()
            assert page.locator('.st-key-dashboard').bounding_box()['width']<baseline-100
            page.locator('.st-key-header_copilot button:visible').click();ready(page)
            expect(page.locator('.st-key-copilot_drawer')).to_have_count(0)
            assert abs(page.locator('.st-key-dashboard').bounding_box()['width']-baseline)<2
            report['checks'].append('Copilot panel releases its column when closed')
            page.locator('.st-key-presentation_button button:visible').click();ready(page)
            assert abs(geometry(page)['stMain']['x'])<1
            page.locator('.st-key-presentation_button button:visible').click();ready(page)
            report['checks'].append('Presentation mode enters and exits without a sidebar gap')
            complete_preferences(page, report)
            assert not report['errors'],report['errors']
            report['passed']=True;browser.close()
    except Exception as error:
        report['failure']=str(error);raise
    finally:
        REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps({'passed':report['passed'],'checks':len(report['checks']),'browser_errors':len(report['errors']),'widths':list(report['geometry'])}),flush=True)

if __name__=='__main__':run(finish_only='--finish' in sys.argv)
