"""Rendered visibility and real interaction checks for every shared chart toolbar."""
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from workspace_usability_qa import ROOT, BASE, settled, theme


def inspect_controls(page):
    return page.locator('[data-testid="stPlotlyChart"]:visible').evaluate_all("""charts=>charts.map(chart=>{
      const frame=chart.getBoundingClientRect(), plot=chart.querySelector('.js-plotly-plot');
      const controls=[...chart.querySelectorAll('.modebar-btn')].map(button=>{
        const b=button.getBoundingClientRect(), icon=button.querySelector('svg'), path=button.querySelector('svg path');
        return {label:button.getAttribute('data-title'),width:b.width,height:b.height,rect:b.toJSON(),frame:frame.toJSON(),
          inside:b.left>=frame.left-1&&b.right<=frame.right+1&&b.top>=frame.top-1&&b.bottom<=frame.bottom+1,
          icon_size:icon?icon.getBoundingClientRect().width:0,fill:path?getComputedStyle(path).fill:null};
      });
      const rail=chart.querySelector('.modebar').getBoundingClientRect();
      return {controls,rail_height:rail.height,plot_top:plot._fullLayout._size.t,
        rail_clear:rail.bottom-frame.top<=plot._fullLayout._size.t+1};
    })""")


def verify(page, report, name):
    settled(page)
    page.locator('[data-testid="stPlotlyChart"]:visible').first.wait_for(timeout=60000)
    page.wait_for_function("""()=>{const charts=[...document.querySelectorAll('[data-testid="stPlotlyChart"]')].filter(e=>e.checkVisibility());return charts.length>0&&charts.every(e=>e.querySelector('.js-plotly-plot')?._fullLayout&&e.querySelector('.modebar-btn'));}""",timeout=60000)
    page.wait_for_function("""()=>[...document.querySelectorAll('[data-testid="stPlotlyChart"]')].filter(e=>e.checkVisibility()).every(e=>{const p=e.querySelector('.js-plotly-plot');return p._fullLayout.width<=e.getBoundingClientRect().width+1;})""",timeout=60000)
    page.wait_for_function('()=>[...document.querySelectorAll("[data-testid=stPlotlyChart]")].filter(e=>e.checkVisibility()).every(e=>{const svg=e.querySelector("svg.main-svg");return svg&&Math.abs(svg.getBoundingClientRect().width-e.getBoundingClientRect().width)<2;})',timeout=60000)
    page.wait_for_timeout(300)
    charts=inspect_controls(page)
    report['layouts'][name]=charts
    assert charts, name
    for chart in charts:
        assert chart['rail_clear'], (name, chart)
        for control in chart['controls']:
            assert control['inside'] and control['width']>=44 and control['height']>=44, (name,control)
            assert control['icon_size']>=20 and control['fill'] and not control['fill'].endswith(', 0.3)'), (name,control)
    report['layouts'][name]=charts
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), name


def run():
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'layouts':{},'functional':[],'errors':[],'passed':False}
    output=ROOT/'tmp/screenshots/chart-controls'
    output.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
            page=browser.new_page(viewport={'width':1512,'height':1060},reduced_motion='reduce')
            page.on('pageerror',lambda error:report['errors'].append(str(error)))
            page.goto(f'{BASE}/?page=landing')
            page.locator('.st-key-landing_open_platform').get_by_role('button').click()
            page.locator('.st-key-table_footer_overview').wait_for(timeout=60000)
            verify(page,report,'overview-desktop')
            chart=page.locator('[data-testid="stPlotlyChart"]').first
            chart.scroll_into_view_if_needed()
            page.mouse.move(10,10)
            page.screenshot(path=str(output/'desktop-visible.png'))
            plot=chart.locator('.js-plotly-plot')
            span=plot.evaluate('e=>e._fullLayout.yaxis.range[1]-e._fullLayout.yaxis.range[0]')
            chart.locator('.modebar-btn[data-title="Zoom in"]').click()
            page.wait_for_function('before=>{const e=document.querySelector(".js-plotly-plot");return e._fullLayout.yaxis.range[1]-e._fullLayout.yaxis.range[0]<before*.9}',arg=span)
            small=plot.evaluate('e=>e._fullLayout.yaxis.range[1]-e._fullLayout.yaxis.range[0]')
            chart.locator('.modebar-btn[data-title="Zoom out"]').click()
            page.wait_for_function('before=>{const e=document.querySelector(".js-plotly-plot");return e._fullLayout.yaxis.range[1]-e._fullLayout.yaxis.range[0]>before*1.1}',arg=small)
            chart.locator('.modebar-btn[data-title="Pan"]').click()
            assert plot.evaluate('e=>e._fullLayout.dragmode')=='pan'
            chart.locator('.modebar-btn[data-title="Zoom"]').click()
            assert plot.evaluate('e=>e._fullLayout.dragmode')=='zoom'
            chart.locator('.modebar-btn[data-title="Autoscale"]').click()
            assert plot.evaluate('e=>e._fullLayout.yaxis.autorange')
            chart.locator('.modebar-btn[data-title="Reset axes"]').click()
            reset=plot.evaluate('e=>e._fullLayout.yaxis.range[1]-e._fullLayout.yaxis.range[0]')
            assert abs(reset-span)<max(1,span)*1e-6
            report['functional'].append('Zoom in/out change ranges; Pan/Zoom change drag mode; Autoscale and Reset axes restore the view')
            original=chart.bounding_box()
            chart.locator('.modebar-btn[data-title="Fullscreen"]').click()
            page.wait_for_function('width=>document.querySelector("[data-testid=stPlotlyChart]").getBoundingClientRect().width>width+100',arg=original['width'])
            verify(page,report,'overview-fullscreen')
            page.screenshot(path=str(output/'fullscreen.png'))
            page.keyboard.press('Escape')
            if chart.bounding_box()['width']>original['width']+100:
                chart.locator('.modebar-btn').filter(has=page.locator('svg')).last.click()
            report['functional'].append('Fullscreen expands the chart and exits successfully')
            with page.expect_download() as downloaded:
                chart.locator('.modebar-btn[data-title="Download plot as a PNG"]').click()
            assert Path(downloaded.value.path()).read_bytes().startswith(b'\x89PNG')
            report['functional'].append('PNG export downloads a valid image')
            for width in [820,390,320]:
                page.set_viewport_size({'width':width,'height':1060})
                verify(page,report,f'overview-{width}')
                chart.scroll_into_view_if_needed()
                page.screenshot(path=str(output/f'mobile-{width}.png'))
            page.set_viewport_size({'width':1512,'height':1060})
            theme(page,'Dark')
            verify(page,report,'overview-dark')
            chart.scroll_into_view_if_needed()
            page.screenshot(path=str(output/'dark.png'))
            theme(page,'Light')
            page.locator('.st-key-nav_delivery').get_by_role('button').click()
            page.locator('.st-key-table_footer_delivery').wait_for(timeout=60000)
            verify(page,report,'delivery-overview')
            for tab in ['Operational Segments','Model Diagnostics']:
                page.get_by_role('tab',name=tab,exact=True).click()
                settled(page)
                verify(page,report,f'delivery-{tab}')
            for tab in ['Threshold','Calibration','Explainability']:
                page.get_by_role('tab',name=tab,exact=True).click()
                verify(page,report,f'delivery-{tab}')
            page.locator('.st-key-nav_demand').get_by_role('button').click()
            verify(page,report,'demand-overview')
            seasonality=page.get_by_role('tab',name='Seasonality',exact=True)
            seasonality.scroll_into_view_if_needed(timeout=60000)
            seasonality.click(timeout=60000)
            verify(page,report,'demand-seasonality')
            assert not report['errors'],report['errors']
            report['passed']=True
            browser.close()
    except Exception as error:
        report['failure']=str(error)
        raise
    finally:
        (ROOT/'metadata/chart_controls_qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps({'passed':report['passed'],'layouts':len(report['layouts']),'functional':report['functional']}),flush=True)


if __name__=='__main__':
    run()
