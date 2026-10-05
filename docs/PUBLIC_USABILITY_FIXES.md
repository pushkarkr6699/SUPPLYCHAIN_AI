# Public landing and login usability fixes

The attached landing audit has 19 issues; the login audit has 12. This document keeps each audit's numbering and records the root cause and implemented change. Source datasets, trained models and the demo/verified provider configuration are preserved.

Source changes: [login controls](../components/auth_components.py), [login layout](../views/login.py), [login styles](../styles/auth.css), [landing components](../components/landing_components.py), [landing layout](../views/landing.py), and [shared public tokens / landing styles](../styles/landing.css).

## Login: 12 issues

1. **Type scale.** Independent fractional `rem` declarations produced 11 sizes. `auth.css` now uses the shared `--landing-label`, `--landing-body`, `--landing-copy`, `--landing-value` and heading tokens. For example, `.login-intro{font-size:var(--landing-copy)}`. Display size adapts at existing breakpoints. The rendered login uses at most five text sizes per tested width.
2. **Corner radii.** Separate values for panel, form, feature tiles and widgets produced eight radii. Replace them with `--landing-radius-small:6px`, `--landing-radius-card:10px`, `--landing-radius-panel:16px` and `--landing-pill:999px`. Native checkbox and square elements retain their own shapes; six computed radius values remain, including zero.
3. **Button styles.** The custom password toggle and duplicate header exit added special variants. Remove both controls and their unused styles. Keep primary Sign In, outlined Demo, plain secondary links and the native icon controls. All form buttons use `min-height:44px` and the shared small radius/type token.
4. **Brand footer at 8px.** `.auth-brand-foot` used `.49rem` and even smaller mobile overrides. Set `font-size:var(--landing-label)` (12px), reduce tracking to `.04em` and allow wrapping. The mobile override also uses the label token.
5. **Intro at 12px.** `.login-intro` used `.72rem`. Set `.st-key-login_card .login-intro{font-size:var(--landing-copy);line-height:1.7}` (16px).
6. **Demo disclosure at 9px.** `.demo-auth-note p` used `.59rem`, making the access limitations difficult to read. Set `font-size:var(--landing-body);line-height:1.6` (14px). Preserve the prominent bold disclosure and sample-value guidance. The copy accurately says credentials are not verified by an identity provider; it does not claim browser input never reaches the Streamlit server. Hide the decorative information glyph from screen readers.
7. **Remember-me label at 10px.** The checkbox had its own `.65rem` rule. Set `.st-key-login_card [data-testid="stCheckbox"] p{font-size:var(--landing-body)}` (14px); give its label a 44px minimum height. Remember-me retains its session-only wording and help.
8. **Duplicate password controls.** A custom Show/Hide button changed the input type while Streamlit also supplied an eye button. Remove `toggle_password`, its columns and its button. Render one `st.text_input("Password", type="password", ...)`; the native eye exposes Show password/Hide password and pressed state. Keyboard behavior remains native.
9. **Duplicate return links.** `views/login.py` rendered Back to site while the form rendered Return to website. Remove the header button and unnecessary navigation import. Keep the existing `login_back` action after the form disclosure.
10. **Secondary-link alignment.** Forgot password used stretch width and default centered button content. Remove its stretch width and apply `justify-content:flex-start;padding-left:0;padding-right:0;text-align:left` to both `.st-key-forgot_password button` and `.st-key-login_back button`. Both retain 44px heights and their existing callbacks.
11. **Leading submit arrow.** Streamlit's `icon` argument defaults to a leading icon. Use the installed native API: `st.button("Sign In", icon=":material/arrow_forward:", icon_position="right", ...)`. The arrow now follows the label; its callback remains unchanged. Browser QA checks the actual icon and label positions.
12. **Overweight Show button.** The custom reveal button had a surface background and border. Removing it resolves the hierarchy problem; the remaining native eye is transparent and has a 44px target and visible keyboard focus.

## Landing: 19 issues

1. **Type scale.** Ad hoc sizes in every preview and section produced 18 sizes. Define seven shared sizes: 12, 14, 16, 20, 24, 32 and 64px. Replace individual declarations with the relevant token; display/headings adapt to 48/40 and 24px at smaller breakpoints. Each tested layout has at most seven text sizes.
2. **Text colors.** Numerous near-identical gray and accent hex values produced 60 colors. Replace text declarations with ten shared semantic colors for ink, muted text, accents and inverse text. Preserve chart/background colors. Inverse colors are scoped to the dark public sections; the nested white answer card restores the light palette.
3. **Corner radii.** Independent panel/card/button values produced 12 radii. Use the same four tokens as login. Together with native elements and square elements, the rendered landing has six radius values.
4. **Hero proof at 10px.** `.hero-proof` had its own tiny size. Use `font-size:var(--landing-body)` (14px) and retain wrapping.
5. **Operations workspace at 9px.** `.hero-surface-header` used a small fractional size. Use `font-size:var(--landing-label)` (12px), preserving the layout and synthetic-data badge.
6. **Long uppercase risk label.** The label was hardcoded as HIGH-RISK DELIVERY. Change it to High-risk delivery in both hero and dashboard examples and set label letter spacing to zero. Demand outlook is also sentence case.
7. **Problem-panel paragraphs at 12px.** Change `.problem-panel p` to the 14px body token and remove its fixed minimum text height so wrapping does not create excess gaps.
8. **Problem-panel list at 10px.** Change `.problem-panel li` to the 14px body token. At mobile widths stack the list into one column.
9. **Executive command center at 8px.** Use the shared 12px label token on `.tower-page-title>div>span`; make the label sentence case. Keep the actual Operations at a glance heading.
10. **Copilot answer at 9px.** Set `.tower-preview .copilot-thread>p{font-size:var(--landing-body)}` (14px) without changing the evidence or demo values.
11. **Copilot metric label at 7px.** Use the 12px label token on `.copilot-metric>span` and allow a 140px text width to accommodate wrapping.
12. **Architecture note at 11px.** Set `.architecture-note p` to the 14px body token with the existing supporting-note structure.
13. **Example question at 10px.** Set `.copilot-preview .preview-bubble p` to the 14px body token. The example remains noninteractive with a figure label.
14. **Footer links at 10px.** Set `.footer-group>a` to 14px and use inline flex alignment with a 44px minimum link height. Preserve real section anchors.
15. **False dashboard controls.** Static sidebar, window/header controls and fake action spans resembled live navigation. Remove their markup; retain the chart/KPI/order/answer example as a labeled figure. Add a Read-only example caption and plain guidance. There are no buttons or links inside either analysis figure.
16. **Repeated primary CTA.** Header, hero, Copilot body and closing section competed with the same primary action. Keep one primary Open platform in the sticky header. Make hero Explore the workspace and closing Start an analysis secondary. Replace the Copilot action with a real See analysis examples anchor. Working workspace-entry callbacks remain connected.
17. **Native Deploy utility.** Streamlit's utility header remained part of the public chrome. Hide `[data-testid="stHeader"]`, `[data-testid="stToolbar"]` and decoration under `body:has(:is(.st-key-public_header,.st-key-auth_header))`. This scope disappears in the authenticated workspace, preserving sidebar reopen behavior.
18. **Twelve identical capability cards.** Index-only cards lacked grouping and visual distinction. Keep all 12 capabilities, grouped under Operations, Investigation and Governance & reports. Use `h3` group headings and `h4` module headings with 12 distinct decorative icons. Remove clickable hover movement from static cards.
19. **Two navigation patterns.** Native MainMenu competed with the real section navigation. Hide `#MainMenu` only on public routes. Retain the labeled Main navigation links, visible keyboard focus, sticky placement and wrapping mobile layout.

## Additional implementation findings

Streamlit sanitization removed inline SVG in the installed version, including the existing demand charts. `components/landing_components.py::public_html` renders the trusted, code-defined SVG as embedded image assets instead. Charts have descriptive `alt` text; decorative capability icons have empty `alt` inside `aria-hidden` wrappers. No script execution or external assets are enabled.

The shared bordered-container selector also overrode dark public panel backgrounds. A more specific public-container rule restores `#142644` before applying inverse text colors. Login input boundaries are explicitly visible; public styles do not hide the workspace header.

The repeated login audit also exercises explicit clearing of password input when entering Demo Mode and clearing both login fields on logout. Setting empty widget values resets browser form controls in addition to deleting server session state. Browser checks wait for the previous route to finish unmounting before submitting another action.

## Reproduce validation

With the local app running at port 8501:

```powershell
.\.venv\Scripts\python.exe scripts/public_usability_qa.py
.\.venv\Scripts\python.exe scripts/landing_login_qa.py
.\.venv\Scripts\python.exe -m pytest -q
```

The public audit checks landing/login at 1512, 1366, 820, 390 and 320px: computed type sizes, text palette, radii, small text, solid-background text contrast, target heights, image loading and page overflow. It also checks keyboard password reveal/focus, real anchors, sticky navigation, validation/recovery, both workspace entry paths, logout/password clearing and sidebar collapse/reopen. Computed contrast checks complement visual inspection; they are not a full accessibility certification or pixel-level gradient analysis.

Executed evidence is written to `metadata/public_usability_qa.json`; full scrolling-page screenshots are saved in ignored `tmp/screenshots/public-experience/`. The existing platform regression suite passed **113 tests**, with its two expected malformed-source date parsing warnings.

Final executed result: **PASS** for all ten route/width combinations and all recorded functional flows, including the native right-side arrow and clearing sample inputs after both sign-in and Demo Mode. The latest full regression run passed **113 tests in 41.29s**, with two expected malformed-source date parsing warnings. The original `landing_login_qa.py` workflow also passed. The measurements show at most seven landing text sizes and five login sizes, ten landing text colors and seven login colors, six radii on each page, four login button styles, and no visible text below 12px.

Login continues to provide session-only demo access. This usability work does not connect an identity provider or change model/data behavior.
