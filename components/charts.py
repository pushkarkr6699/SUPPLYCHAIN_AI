import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from services.analytics import aggregate, trend, classification

BLUE, PURPLE, GREEN, AMBER, RED = "#4169dc", "#8970dc", "#219880", "#d39c47", "#d65b68"
PALETTE = [BLUE, PURPLE, GREEN, AMBER, RED, "#7896b6"]
RISK_COLORS = {"Low": GREEN, "Medium": AMBER, "Attention": AMBER, "High": "#e18445", "Critical": RED}


def style(fig, height=290, *, legend_below=False, category_footer=False):
    dark = st.session_state.get("theme") == "Dark"
    text, grid = ("#d3dcec", "#293951") if dark else ("#52627a", "#edf0f6")
    fig.update_layout(template="plotly_dark" if dark else "plotly_white", height=height + (100 if st.session_state.get("presentation") else 0),
        margin=dict(l=12, r=12, t=16, b=170 if category_footer else 92 if legend_below else 40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=14, color=text), colorway=PALETTE,
        legend=dict(orientation="h", y=-.03 if legend_below else 1.14, x=.5 if legend_below else 0,
                    xanchor="center" if legend_below else "left", yanchor="top" if legend_below else "bottom", font=dict(size=12)),
        hoverlabel=dict(font_size=14), transition=dict(duration=250 if st.session_state.get("animation") else 0))
    fig.update_xaxes(showgrid=False, zeroline=False, title=None)
    fig.update_yaxes(showgrid=st.session_state.get("gridlines", True), gridcolor=grid, zeroline=False, title=None)
    fig.add_annotation(text="Supplied data" if st.session_state.get("verified_context") else "Demo UI data", x=1,
        y=0 if category_footer else -.37 if legend_below else -.17,
        yshift=-150 if category_footer else 0, yanchor="top" if category_footer else "auto",
        xref="paper", yref="paper", xanchor="right", showarrow=False, font=dict(size=12, color=text))
    return fig


def show(fig, key=None, height=290, *, legend_below=False, category_footer=False):
    st.plotly_chart(style(fig, height, legend_below=legend_below, category_footer=category_footer), width="stretch", theme=None, key=key,
        config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                "toImageButtonOptions": {"format": "png", "filename": "supplychain-chart", "scale": 2}})


def forecast_chart(df, key=None, height=300):
    data = trend(df)
    verified = df.attrs.get("verified_artifacts", False)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.Date, y=data.Upper, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=data.Date, y=data.Lower, fill="tonexty", fillcolor="rgba(137,112,220,.12)", line=dict(width=0), name="Sum of supplied bounds" if verified else "Illustrative range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=data.Date, y=data["Actual Demand"], name="Actual" if verified else "Actual · demo", line=dict(color=BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=data.Date, y=data["Forecast Demand"], name="Forecast" if verified else "Forecast · demo", line=dict(color=PURPLE, width=2.5, dash="dot")))
    show(fig, key, height)


def bar(df, dimension, metric="Risk Probability", key=None, horizontal=False):
    data = aggregate(df, dimension, metric).sort_values(metric, ascending=horizontal)
    data = data.dropna(subset=[metric])
    if data.empty:
        st.info("No measured values for these filters. Broaden the period or reset filters.")
        return
    fig = px.bar(data, x=metric if horizontal else dimension, y=dimension if horizontal else metric,
        orientation="h" if horizontal else "v", color_discrete_sequence=[BLUE],
        text_auto=(".1%" if metric == "Risk Probability" else True) if st.session_state.get("labels") else False)
    fig.update_traces(marker_line_width=0, marker_cornerradius=4)
    if metric == "Risk Probability":
        (fig.update_xaxes if horizontal else fig.update_yaxes)(tickformat=".0%")
    show(fig, key, height=290 if horizontal else 350, category_footer=not horizontal)


def risk_donut(df, key=None):
    data = df.groupby("Risk", as_index=False).size()
    if data.empty:
        st.info("No scored risk bands in this period. Broaden the date range or reset filters.")
        return
    fig = px.pie(data, names="Risk", values="size", hole=.73, color="Risk", color_discrete_map=RISK_COLORS)
    text_color = "#d3dcec" if st.session_state.get("theme") == "Dark" else "#52627a"
    fig.update_traces(textinfo="percent", textposition="outside", textfont=dict(size=14, color=text_color), marker=dict(line=dict(color="white", width=2)))
    count = int(df.Risk.notna().sum())
    noun = "scored orders" if df.attrs.get("verified_artifacts") else "demo orders"
    fig.add_annotation(text=f'<b>{count:,}</b><br><span style="font-size:14px">{noun}</span>', showarrow=False, font_size=20)
    show(fig, key, legend_below=True)
    if count < len(df):
        st.caption(f"{len(df) - count:,} unscored orders excluded from the risk distribution.")


def matrix(df, threshold, key=None):
    m = classification(df, threshold)
    fig = px.imshow([[m["TN"], m["FP"]], [m["FN"], m["TP"]]], x=["Predicted on time", "Predicted late"], y=["Actual on time", "Actual late"], text_auto=True, color_continuous_scale="Blues", aspect="auto")
    fig.update_layout(coloraxis_showscale=False)
    show(fig, key)

