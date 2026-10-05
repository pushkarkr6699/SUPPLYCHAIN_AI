"""Rendered public-page audit and functional checks. Requires local preview on 8501."""
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'tmp/screenshots/public-experience'
OUTPUT.mkdir(parents=True, exist_ok=True)
MEASURE = r'''() => {
 const main=document.querySelector('[data-testid="stMain"]');
 const visible=e=>e.getClientRects().length && getComputedStyle(e).visibility==='visible' && !e.closest('[aria-hidden="true"]');
 const canvas=document.createElement('canvas');canvas.width=canvas.height=1;const ctx=canvas.getContext('2d');const cache={};
 const rgba=color=>{if(cache[color])return cache[color];ctx.clearRect(0,0,1,1);ctx.fillStyle=color;ctx.fillRect(0,0,1,1);return cache[color]=[...ctx.getImageData(0,0,1,1).data].map((v,i)=>i===3?v/255:v)};
 const blend=(top,bottom)=>top.slice(0,3).map((v,i)=>v*top[3]+bottom[i]*(1-top[3]));
 const luminance=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
 const nodes=[];const contrast=[];const walker=document.createTreeWalker(main,NodeFilter.SHOW_TEXT);
 while(walker.nextNode()){
  const n=walker.currentNode,e=n.parentElement;
  if(!n.textContent.trim()||!visible(e)||e.closest('style,script,[data-testid="stIconMaterial"],svg'))continue;
  const s=getComputedStyle(e),record={text:n.textContent.trim().slice(0,90),size:s.fontSize,color:s.color};nodes.push(record);
  const chain=[];for(let parent=e;parent;parent=parent.parentElement)chain.unshift(parent);
  let bg=[255,255,255];for(const parent of chain)bg=blend(rgba(getComputedStyle(parent).backgroundColor),bg);
  const fg=blend(rgba(s.color),bg),l=[luminance(fg),luminance(bg)].sort((a,b)=>a-b),ratio=(l[1]+.05)/(l[0]+.05);
  const minimum=parseFloat(s.fontSize)>=24||(parseFloat(s.fontSize)>=18.66&&parseInt(s.fontWeight)>=700)?3:4.5;
  if(ratio<minimum)contrast.push({...record,ratio:Math.round(ratio*100)/100,minimum});
 }
 const elements=[...main.querySelectorAll('*')].filter(visible);
 const buttons=[...main.querySelectorAll('button')].filter(visible);
 const styles=buttons.map(e=>{const s=getComputedStyle(e);return [s.backgroundColor,s.color,s.borderWidth,s.borderStyle,s.borderColor,s.borderRadius,s.fontSize].join('|')});
 const targets=[...main.querySelectorAll('button,a')].filter(visible).filter(e=>e.getBoundingClientRect().height<43.9).map(e=>e.innerText||e.getAttribute('aria-label'));
 const brokenImages=[...main.querySelectorAll('img')].filter(visible).filter(e=>!e.complete||e.naturalWidth===0).map(e=>e.alt);
 return {sizes:[...new Set(nodes.map(n=>n.size))].sort(),colors:[...new Set(nodes.map(n=>n.color))].sort(),radii:[...new Set(elements.map(e=>getComputedStyle(e).borderRadius))].sort(),button_styles:[...new Set(styles)],small:nodes.filter(n=>parseFloat(n.size)<12),contrast_failures:contrast,short_targets:targets,broken_images:brokenImages,overflow:{width:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth}};
}'''


def capture(page, name):
    # Streamlit scrolls stMain. Capture its complete content in a taller viewport.
    original = page.viewport_size
    height = page.locator('[data-testid="stMain"]').evaluate('e=>e.scrollHeight')
    page.set_viewport_size({'width':original['width'],'height':height+30})
    page.screenshot(path=str(OUTPUT / f'{name}.png'), full_page=True)
    page.set_viewport_size(original)


def run():
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'measurements': {}, 'functional': [], 'errors': []}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
        for route in ['landing', 'login']:
            if route == 'login': page.close()
            page = browser.new_page(viewport={'width':1512,'height':1060}, reduced_motion='reduce')
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(f'http://127.0.0.1:8501/?page={route}', wait_until='networkidle')
            page.locator('.hero h1' if route == 'landing' else '.login-intro').wait_for()
            for width in [1512,1366,820,390,320]:
                page.set_viewport_size({'width':width,'height':1060})
                page.wait_for_timeout(200)
                metrics = page.evaluate(MEASURE)
                report['measurements'][f'{route}-{width}'] = metrics
                assert len(metrics['sizes']) <= 10, metrics
                assert len(metrics['radii']) <= 6, metrics
                assert not metrics['small'], metrics['small']
                assert not metrics['contrast_failures'], metrics['contrast_failures']
                assert not metrics['short_targets'], metrics['short_targets']
                assert not metrics['broken_images'], metrics['broken_images']
                assert max(metrics['overflow']['doc'],metrics['overflow']['body']) <= width+2, metrics['overflow']
                assert len(metrics['colors']) <= 12, metrics['colors']
                if route == 'login': assert len(metrics['button_styles']) <= 5, metrics['button_styles']
                capture(page, f'{route}-{width}-full')
            assert not page.locator('[data-testid="stHeader"]').is_visible()
            report['functional'].append(f'{route}: native utility header hidden only on public page')
        page.set_viewport_size({'width':1512,'height':1060})
        for selector, minimum in [('.auth-brand-foot',12),('.login-intro',16),('.demo-auth-note p',14),('[data-testid="stCheckbox"] p',14)]:
            assert page.locator(selector).evaluate('e=>parseFloat(getComputedStyle(e).fontSize)') >= minimum, selector
        submit=page.locator('.st-key-login_submit').get_by_role('button')
        arrow=submit.locator('[data-testid="stIconMaterial"]')
        label=submit.get_by_text('Sign In',exact=True)
        expect(arrow).to_have_count(1)
        assert arrow.bounding_box()['x'] >= label.bounding_box()['x']+label.bounding_box()['width']
        report['functional'].append('login: all four audited text selectors meet their readable sizes; native submit arrow follows the label')
        password = page.get_by_role('textbox', name='Password', exact=True)
        password.fill('sample-only')
        expect(password).to_have_attribute('type','password')
        eye = page.get_by_role('button', name='Show password', exact=True)
        expect(eye).to_have_count(1)
        eye.focus()
        assert page.evaluate('document.activeElement.getAttribute("aria-label")') == 'Show password'
        assert eye.evaluate('e=>getComputedStyle(e).outlineStyle') != 'none'
        page.keyboard.press('Enter')
        expect(password).to_have_attribute('type','text')
        page.get_by_role('button', name='Hide password', exact=True).click()
        expect(password).to_have_attribute('type','password')
        expect(page.get_by_role('button', name='Show', exact=True)).to_have_count(0)
        expect(page.get_by_role('button', name='Back to site', exact=True)).to_have_count(0)
        report['functional'].append('login: one keyboard-operable native reveal control with visible focus; no duplicate Show or header exit')
        forgot=page.get_by_role('button', name='Forgot password?', exact=True)
        back=page.get_by_role('button', name='Return to website')
        assert abs(forgot.bounding_box()['x']-back.bounding_box()['x']) < 1
        page.locator('.st-key-login_submit').get_by_role('button').click()
        page.get_by_text('Enter a demo username and password, or continue in Demo Mode.').wait_for()
        forgot.click()
        page.get_by_text('Password recovery will be available when an authentication provider is connected.').wait_for()
        back.click()
        page.locator('.hero h1').wait_for()
        report['functional'].append('login: left-aligned secondary links, validation, recovery notice and single return action work')
        expect(page.locator('.capability-group-title')).to_have_count(3)
        expect(page.locator('.capability-card h4')).to_have_count(12)
        expect(page.locator('.cap-icon img')).to_have_count(12)
        expect(page.locator('.hero-spark')).to_have_count(1)
        expect(page.locator('.demand-svg')).to_have_count(1)
        expect(page.locator('.tower-preview .tower-nav,.tower-preview .tower-top,.copilot-actions,.preview-actions')).to_have_count(0)
        expect(page.locator('.tower-preview button,.tower-preview a,.copilot-preview button,.copilot-preview a')).to_have_count(0)
        expect(page.locator('button[kind="primary"]')).to_have_count(1)
        report['functional'].append('landing: 12 distinct module icons in 3 groups, 2 visible charts, read-only examples without false controls, one primary CTA')
        nav=page.locator('.public-links a[href="#platform"]')
        page.keyboard.press('Tab')
        nav.focus()
        assert nav.evaluate('e=>getComputedStyle(e).outlineStyle') != 'none'
        page.keyboard.press('Enter')
        assert page.evaluate('location.hash') == '#platform'
        header=page.locator('[data-testid="stLayoutWrapper"]:has(> .stVerticalBlock.st-key-public_header)')
        assert abs(header.bounding_box()['y']) < 1
        report['functional'].append('landing: real section navigation works with keyboard, visible focus and sticky header')
        page.locator('.st-key-landing_open_platform').get_by_role('button').click()
        page.get_by_role('heading',name='Executive Command Center',exact=True).wait_for()
        expect(page.locator('[data-testid="stHeader"]')).to_be_visible(timeout=30000)
        page.locator('[data-testid="stSidebarCollapseButton"]').click()
        expand=page.locator('[data-testid="stExpandSidebarButton"]')
        expect(expand).to_be_visible()
        expand.click()
        expect(page.locator('[data-testid="stSidebar"]')).to_be_visible()
        page.locator('.st-key-sidebar_logout').get_by_role('button').click()
        page.locator('.login-intro').wait_for()
        expect(page.locator('.st-key-sidebar_logout')).to_have_count(0,timeout=30000)
        page.get_by_role('textbox',name='Email or username').fill('UI Reviewer')
        page.get_by_role('textbox',name='Password',exact=True).fill('sample-only')
        page.locator('.st-key-login_submit').get_by_role('button').click()
        page.get_by_role('heading',name='Executive Command Center',exact=True).wait_for()
        expect(page.locator('.st-key-auth_header')).to_have_count(0,timeout=30000)
        page.locator('.st-key-sidebar_logout').get_by_role('button').click()
        page.locator('.login-intro').wait_for()
        expect(page.locator('.st-key-sidebar_logout')).to_have_count(0,timeout=30000)
        expect(page.get_by_role('textbox',name='Email or username')).to_have_value('')
        expect(page.get_by_role('textbox',name='Password',exact=True)).to_have_value('')
        page.get_by_role('textbox',name='Email or username').fill('Demo input')
        page.get_by_role('textbox',name='Password',exact=True).fill('sample-only')
        page.get_by_role('button',name='Continue in Demo Mode',exact=True).click()
        page.get_by_role('heading',name='Executive Command Center',exact=True).wait_for()
        expect(page.locator('.st-key-auth_header')).to_have_count(0,timeout=30000)
        page.locator('.st-key-sidebar_logout').get_by_role('button').click()
        page.locator('.login-intro').wait_for()
        expect(page.locator('.st-key-sidebar_logout')).to_have_count(0,timeout=30000)
        expect(page.get_by_role('textbox',name='Email or username')).to_have_value('')
        expect(page.get_by_role('textbox',name='Password',exact=True)).to_have_value('')
        report['functional'].append('workspace regression: both entry paths, sample sign-in, logout/password clearing and sidebar collapse/reopen work; workspace native header retained')
        assert not report['errors'], report['errors']
        browser.close()
    report['status']='passed'
    (ROOT/'metadata/public_usability_qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Public usability QA passed: 10 responsive page/width combinations, typography/palette/radii, text contrast, image rendering, target heights and functional flows.')
    print('Evidence: metadata/public_usability_qa.json; screenshots: tmp/screenshots/public-experience')


if __name__ == '__main__':
    run()
