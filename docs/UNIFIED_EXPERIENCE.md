# Unified UI experience ? 6 October 2026

The existing `app.py` entrypoint connects the public landing page, session login and every registered dashboard route. All three now share the decision-network brand mark, the same blue/slate visual identity and one interface-animation preference. Demo and verified-data providers continue to use this shared UI.

## Fixes

- The supplied five-second recording showed a closed sidebar retaining its layout width. Width limits now apply only to the expanded state; the collapsed state has zero width, minimum width, maximum width and flex basis. The main workspace expands into the released space. Mobile retains its native overlay behavior.
- Sidebar disclosure headings have explicit dark surfaces and readable inverse text in closed, open, hover and keyboard-focus states. Selected children retain an accessible accent background and a visible selection marker in Light, Dark and System themes.
- The Copilot context column exists only while open. Both drawer and standard layouts use the same dashboard container and styles. Closing it restores the full dashboard width. Runtime script containers reserve no visible space.
- Landing and login now use the same brand mark as the dashboard.
- Page titles and copy enter with brief fades; cards and sections reveal once; buttons, tabs and disclosure headings have interaction feedback; login, popovers and context panels use short transitions. Charts retain their native controls and immediate resize repair.
- Interface animations default to enabled. **Settings ? Appearance ? Interface animations** turns them off for the current session. Device **Reduce motion** always disables the animations and transitions. Scroll reveals keep content readable when JavaScript is unavailable.
- Unavailable cross-risk preview text remains readable, with its unavailable status stated explicitly.

## Validation

- Full Python regression: 120 passed, two expected malformed-date fixture warnings.
- Public browser audit: 10 landing/login page-width combinations, contrast, keyboard controls, image rendering and connected entry/logout paths passed.
- Chart browser audit: 14 layouts; zoom, pan, autoscale, reset, fullscreen and PNG export passed.
- Integrated browser audit: `metadata/unified_experience_qa.json` records the connected route flow, seven disclosure groups across all themes, sidebar width recovery at five widths, Copilot width recovery, presentation mode, reduced motion and the interface-animation setting.
- Existing local security audit passed with no findings. Its scope and limitations remain recorded in `metadata/security_audit.json`.

Preview: http://127.0.0.1:8501. Refresh with Ctrl+F5 after updating an existing browser tab. Session login remains the documented local preview access flow.
