# Workspace usability audit: 18 implemented fixes

The supplied audit names `?page=landing`, but its quoted elements are the authenticated Executive Command Center: dataset notices, workspace filters, supplied-risk charts, order investigation, and executive insights. These fixes therefore apply to the authenticated workspace and its shared components. The completed landing and login fixes are retained in [PUBLIC_USABILITY_FIXES.md](PUBLIC_USABILITY_FIXES.md).

The supplied source records and trained artifacts remain in the existing integration layer. Delivery and demand retain separate datasets and filter contexts. Risk scoring, thresholds, missing-score handling, coverage, and model calculations are unchanged. Demo mode remains available.

The workspace style layer is [styles/workspace_audit.css](../styles/workspace_audit.css), loaded by `load_styles()` in [components/app_shell.py](../components/app_shell.py). Its rules are scoped to `.stApp:has(.st-key-top_header)`; `body:has(.stApp .st-key-top_header)` also supplies the same tokens to native popovers rendered outside the application container. The explicit Dark and System-dark overrides are added by `load_styles()`.

## 1. Too many typefaces

**Root cause:** Independent component and native-widget styles used different font stacks; Plotly also declared its own stack.

**Implemented fix:** Define `--wa-font: Inter, "Segoe UI", Arial, sans-serif` and apply it within the authenticated workspace. Code keeps a shared monospace stack through the `pre, code, kbd, samp` selectors. Material-symbol elements retain their icon font, and SVG geometry is excluded from the broad HTML inheritance rule. [components/charts.py](../components/charts.py) uses the same interface stack in `style()`.

Native markdown/expander icons also retain their `Material Symbols Rounded` font through the `span[translate="no"]` exclusion; this prevents the Evidence & provenance icon becoming literal text.

## 2. No consistent type scale

**Root cause:** Shared cards, headings, captions, controls, and chart labels each carried independent small-size declarations.

**Implemented fix:** Replace workspace sizes with the authored tokens `--wa-label:12px`, `--wa-body:14px`, `--wa-title:16px`, `--wa-section:20px`, `--wa-value:24px`, `--wa-heading:32px`, and `--wa-presentation-value:36px`. Native form labels/captions and responsive headings select from the same scale. Plotly uses 14px base and percentage text, 12px legend/source text, and a 20px donut count with a 14px noun. Rendered measurements are produced by the browser QA command below.

## 3. Too many text colours

**Root cause:** Near-identical grays and component-specific accent values accumulated across cards, navigation, notices, and chart text.

**Implemented fix:** Route workspace text through the shared `--wa-ink`, `--wa-muted`, accent, and inverse tokens. Supporting copy uses `--wa-muted`; light chart text uses `#52627a`, and dark chart text uses `#d3dcec`. Dark and System-dark overrides supply readable accent/on-accent combinations. Sidebar inverse colors remain explicit. The palette changes text presentation while retaining chart data and slice colors.

Native caption opacity is reset to 1 within the workspace and its popovers. At 60% opacity the supporting color had only approximately 2.62:1 contrast on white; the opaque color has approximately 6.20:1. Disabled buttons keep their separate opacity treatment.

## 4. Inconsistent corner radii

**Root cause:** Controls, cards, native wrappers, chips, and status indicators defined unrelated radii.

**Implemented fix:** Use `--wa-radius-control:6px`, `--wa-radius-card:10px`, `--wa-radius-panel:16px`, and `--wa-radius-round:999px`. The workspace selectors assign controls/chips, analytical cards/native wrappers, global filters, and circular indicators their relevant token. Plain elements remain square. Popovers inherit the card radius through the scoped body rule.

## 5. Many button styles

**Root cause:** Header actions, popovers, navigation, downloads, filters, and analytical actions had separate backgrounds, borders, and padding.

**Implemented fix:** Normalize workspace buttons to secondary, primary, and quiet treatments. Native `stBaseButton-primary`/`primaryFormSubmit` selectors use the primary accent; `stBaseButton-tertiary` uses a transparent quiet treatment. Sidebar quiet controls use the inverse palette. Shared rules give buttons a 44px minimum target, the control radius, consistent padding, and visible focus; native icon controls retain their accessible labels and behavior.

## 6. Dataset notice text at 11px

**Root cause:** `.demo-notice` and its nested explanatory span inherited small banner-copy styles even when presenting important verified-data context.

**Implemented fix:** The workspace `.demo-notice`, `.demo-notice span`, and `.demo-notice b` rules use `font-size:var(--wa-body)` and `line-height:1.5`. The notice wraps with an explicit gap; its explanatory span can occupy a full line on narrow screens. The DataCo/supplied-prediction provenance wording is retained.

## 7. Demand Outlook subtitle at 11px

**Root cause:** The generic section subtitle rule made the product/day-row and forecast-bounds explanation too small.

**Implemented fix:** `.section-heading p` uses `font-size:var(--wa-body)` and the supporting-text token. [components/section_header.py](../components/section_header.py) retains its `h3` plus paragraph structure, and [views/overview.py](../views/overview.py) retains the row-count/forecast-bound copy and calculations.

## 8. Executive insight body copy at 12px

**Root cause:** `.insight-card p` had a compact card-specific size that reduced the readability of the recommended investigation.

**Implemented fix:** Set `.insight-card p` to the 14px body token with `line-height:1.5` and muted text. The existing description, native Investigate action, and route callback are preserved. The card title uses the shared 16px title token.

## 9. Supplied-record caption at 10px

**Root cause:** The insight-card count inherited the global `.eyebrow` treatment intended for compact decorative labels.

**Implemented fix:** The scoped `.eyebrow` rule uses the 12px label token and a readable line height. [components/insights.py](../components/insights.py) still formats the actual record count with `:,`; the caption remains meaningful visible text rather than an inaccessible graphic.

## 10. Long all-caps supplied-record caption

**Root cause:** `insight_card()` hardcoded `SUPPLIED RECORDS`/`DEMO RECORDS`, and the eyebrow styling could uppercase the replacement copy.

**Implemented fix:** Change the native Python copy to `"supplied records"`/`"demo records"`. Add `.insight-card .eyebrow { text-transform:none !important; }` in the scoped workspace layer. Examples now read `636 supplied records` and `1,918 supplied records`; the counts and evidence are unchanged.

## 11. Heading level skipped from H1 to H3

**Root cause:** The primary page title was an H1, while the greeting was rendered through a native H3 markdown heading.

**Implemented fix:** [components/app_shell.py](../components/app_shell.py) renders the greeting using `st.html('<div class="workspace-greeting"><h2>…</h2><p>…</p></div>')`. The page title remains H1, the greeting becomes H2, and analytical sections retain their H3 headings. `.workspace-greeting h2` and its supporting paragraph use the shared scale and spacing.

## 12. Ragged secondary filters and record summary

**Root cause:** The advanced-filter expander, active date chip, and record count formed independent vertical blocks below the main filter grid.

**Implemented fix:** [components/filters.py](../components/filters.py) groups them in `st.container(key="filter_secondary_row")` with vertically aligned columns. A native More filters popover contains `advanced_filter_controls`; active chips live in `filter_active_summary`, and the record count lives in `filter_record_summary`. The `.st-key-filter_secondary_row` rules provide a shared border, padding, and gap. Active chips wrap, and the popover uses a viewport-bounded width with mobile stacking. Existing dataset-scoped filters, save/reset behavior, and chip callbacks remain connected.

The record caption's native negative bottom margin is removed so it stays inside the filter card. Multi-selection chips show two values plus a remaining count, with complete values in the native tooltip. Advanced controls receive a new widget revision after reset or chip removal, preventing stale selections from a closed popover returning on the next action; primary filter keys and dataset scopes remain stable.

## 13. Donut legend detached from its chart

**Root cause:** The shared Plotly layout positioned its legend at `y=1.14`, above the plotting area, allowing the donut legend to appear near the section heading rather than next to the risk distribution.

**Implemented fix:** [components/charts.py](../components/charts.py) adds a keyword-only `legend_below` option to `style()`/`show()`. `risk_donut()` enables it: `legend` uses horizontal orientation, centered `x=.5`, `y=-.03`, and `yanchor="top"`; the bottom margin reserves space for the legend and a lower source note. Shared styling therefore preserves the intended final placement. Percentages use 14px text outside slices, avoiding weak contrast on the existing fill colors. The actual grouped risk values, scored-order total, excluded-unscored caption, chart key, and PNG export configuration are retained.

The visual review also identified a source note overlapping rotated labels in Demand by category. Vertical bars now enable `category_footer`: a 170px bottom margin reserves space for the complete labels and source note, which is anchored 150px below the baseline. A 350px chart height retains useful plotting space. Horizontal bars keep their existing dimensions, and all bar values are unchanged.

## 14. Floating order-investigation controls

**Root cause:** `records_table()` rendered an order selector and Open order button immediately after the table without a titled group.

**Implemented fix:** [components/tables.py](../components/tables.py) wraps them in `st.container(key=f"table_investigation_{key}")` with `<h3 class="table-investigation-title">Order investigation</h3>` and `<p class="table-investigation-copy">Choose an order from the matching records to inspect its evidence.</p>`. The workspace layer gives this group a card background, border, spacing, and shared radius. The selector keeps its accessible `Investigate an order` label and `investigate_{key}` key; Open order retains `open_{key}` and the existing `go("orders", selected_order=selected)` callback.

## 15. Search trigger resembles a text input

**Root cause:** A stretched header popover button looked like an editable search field although typing was only possible after opening the popover.

**Implemented fix:** [components/header.py](../components/header.py) renders the trigger inside `st.container(key="workspace_search_trigger")` and calls `st.popover("Search", icon=":material/search:", width="content", help="Open workspace search")`. `.st-key-workspace_search_trigger button` keeps content width. The popover retains the actual search input, native dialog semantics, keyboard operation, and result navigation.

The keyed container and its direct layout wrapper also use content width and transparent backgrounds, removing the blank white strip behind the compact trigger. The mobile toolbar retains a separate row for its remaining icons.

## 16. Presentation Mode action lacks an icon

**Root cause:** The verified overview branch omitted the icon argument that the demo branch and neighboring actions already used.

**Implemented fix:** [views/overview.py](../views/overview.py) uses `st.button("Presentation Mode", icon=":material/fullscreen:", key="overview_presentation", on_click=toggle_presentation, width="stretch")` in both overview branches. The native screen icon is consistent with the action group; the button label, key, and callback remain unchanged.

## 17. Full-width numeric pagination input

**Root cause:** The primary page selector was an unrestricted-width number input placed above the table rather than a compact footer navigation group.

**Implemented fix:** [components/tables.py](../components/tables.py) adds `table_footer_{key}` and right-aligned `table_pagination_{key}` containers. Native Previous/Next buttons update the existing `page_{key}` state through `change_table_page()` and disable at the first/last page. A visible `<p class="table-page-status" role="status" aria-live="polite">Page X of N</p>` announces position. A Jump popover contains the labeled number input with `min_value=1`, `max_value=maximum`, and `step=1`, preserving direct page entry. Page state is clamped after filtering. Footer controls wrap on mobile; the table's rows, search, columns, filters, and export behavior are preserved.

## 18. Greeting heading-link icon adds noise

**Root cause:** Native markdown headings automatically injected a documentation-style Link to heading anchor into the executive greeting.

**Implemented fix:** The custom `.workspace-greeting` H2 markup in [components/app_shell.py](../components/app_shell.py) creates an ordinary semantic heading without the native permalink control. This also implements issue 11 while preserving the visible greeting and time-of-day selection. No focusable control is hidden with CSS.

## Reproduce verification

Run the local app in verified mode (`SUPPLYCHAIN_PROVIDER=verified` in `.env`) in one PowerShell terminal:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

From another terminal in `D:\SUPPLYCHAIN_AI`, run the browser audit and automated tests:

```powershell
.\.venv\Scripts\python.exe scripts\workspace_usability_qa.py
.\.venv\Scripts\python.exe -m pytest -q
```

The browser audit records rendered measurements and checks responsive layouts, native interactions, and theme behavior. Use its actual output and saved evidence for measured counts and pass totals; the token declarations alone are not a browser measurement. Previous public-page checks remain documented in [PUBLIC_USABILITY_FIXES.md](PUBLIC_USABILITY_FIXES.md).
