// Reveal content once when it enters view; content remains readable without JS.
(() => {
  if (window.supplychainExperience) return;
  window.supplychainExperience = true;
  const seen = new WeakSet();
  const observer = new IntersectionObserver(entries => entries.forEach(({target,isIntersecting}) => {
    if (isIntersecting) { target.classList.add('sc-in-view'); observer.unobserve(target); }
  }), {threshold:.12});
  let queued = false;
  const discover = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      document.querySelectorAll('.problem-panel,.capability-card,.flow-stage,.section-heading,.auth-feature-list > div').forEach(element => {
        if (!seen.has(element)) { seen.add(element); observer.observe(element); }
      });
    });
  };
  new MutationObserver(discover).observe(document.body, {childList:true,subtree:true});
  discover();
})();
