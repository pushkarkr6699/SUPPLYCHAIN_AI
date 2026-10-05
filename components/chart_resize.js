// Repair stale Plotly SVG dimensions after Streamlit fullscreen/column changes.
(() => {
  if (window.supplychainChartResize) return;
  window.supplychainChartResize = true;
  const observed = new Set(), timers = new WeakMap(), busy = new WeakSet();
  const repair = async chart => {
    const plot = chart.querySelector('.js-plotly-plot');
    if (!chart.isConnected || !chart.checkVisibility() || !plot?._fullLayout || !window.Plotly || busy.has(plot)) return;
    const box = chart.getBoundingClientRect(), svg = plot.querySelector('svg.main-svg');
    if (!svg || box.width < 100 || box.height < 100) return;
    const drawn = svg.getBoundingClientRect();
    if (Math.abs(drawn.width - box.width) < 2 && Math.abs(drawn.height - box.height) < 2) return;
    busy.add(plot);
    try {
      await window.Plotly.relayout(plot, {width: box.width, height: box.height});
      // Plotly can already hold the new layout while retaining an old SVG.
      const current = plot.querySelector('svg.main-svg').getBoundingClientRect();
      if (Math.abs(current.width-box.width)>2 || Math.abs(current.height-box.height)>2) await window.Plotly.redraw(plot);
    } catch (error) { console.warn('Chart resize could not complete', error); }
    finally { busy.delete(plot); }
  };
  const schedule = chart => { clearTimeout(timers.get(chart)); timers.set(chart, setTimeout(() => repair(chart), 150)); };
  const sizes = new ResizeObserver(entries => entries.forEach(entry => schedule(entry.target)));
  const discover = () => {
    for (const chart of observed) if (!chart.isConnected) { sizes.unobserve(chart); observed.delete(chart); }
    document.querySelectorAll('[data-testid="stPlotlyChart"]').forEach(chart => {
      if (!observed.has(chart)) { observed.add(chart); sizes.observe(chart); }
      schedule(chart);
    });
  };
  new MutationObserver(discover).observe(document.body, {childList:true, subtree:true});
  discover();
})();
