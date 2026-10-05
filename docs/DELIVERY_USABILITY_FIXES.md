# Delivery usability audit — 16 issues

Implemented against the existing Streamlit UI, preserving verified-data and demo providers.

| # | Root cause | Implemented fix |
|---|---|---|
| 1 | Native widgets, HTML and charts used unrelated font stacks. | Shared workspace font tokens; preserve native icon and code fonts. |
| 2 | Individual components specified arbitrary sizes. | Shared heading, body and label scale in `styles/workspace_audit.css`. |
| 3 | Components carried independent text colors. | Shared semantic colors with Light/Dark/System overrides. |
| 4 | Widgets and cards specified unrelated radii. | Five radius values: square, control, card, panel and round. |
| 5 | Native and custom button rules diverged. | Primary, secondary and quiet treatments; visible focus and 44px targets. |
| 6 | Data source notice inherited 11px text. | Disclosure body copy is 14px with wrapping. |
| 7 | Connected-data badge used 10px. | All workspace badges use the 12px label token. |
| 8 | Chart subtitle used 11px. | Section subtitles use 14px body text. |
| 9 | Shared section helper always emitted H3. | Helper accepts a validated heading level; Delivery sections emit H2 below H1. |
| 10 | Full-width expander resembled a divider. | Content-width native More filters button opens a keyboard-accessible popover. |
| 11 | Expander and chips formed disconnected rows. | Unified filter card with a compact secondary action/chips/count row. |
| 12 | Intraday timestamps created overlapping points. | Calendar-day mean probability, sorted dates, daily markers and hover order counts. Missing scores remain excluded, never zero-filled. |
| 13 | Model Context repeated the table investigation action. | Retain the table's selected-order investigation; remove the redundant action. |
| 14 | Advanced filters used inconsistent widths. | Equal-width advanced grid columns, stacked on narrow screens. |
| 15 | Page number occupied a full-width input. | Previous / Page X of Y / Next footer and bounded Jump popover. |
| 16 | Primary controls were repeated as removable chips. | Delivery omits Date and other visible primary filters from chips; advanced chips remain removable, with Reset available. |

## Verification

`tests/test_delivery_usability.py` checks daily aggregation, sorting, missing scores and source immutability. `scripts/delivery_usability_qa.py` checks computed typography, colors, radii, button styles, contrast, targets and overflow at five viewport widths, plus Dark/System, chart dates, headings, pagination, investigation and tabs. Results are recorded in `metadata/delivery_usability_qa.json`.

The preceding 18-issue workspace audit is documented separately in `WORKSPACE_USABILITY_FIXES.md`. Security checks target the local classroom/demo deployment; they do not provide production authentication or penetration-test certification.
