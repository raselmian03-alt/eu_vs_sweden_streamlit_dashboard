import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def _latest_value(x):
    if isinstance(x, pd.DataFrame):
        x = x.iloc[:, 0]
    if isinstance(x, pd.Series):
        x = x.dropna()
        if x.empty:
            return None
        return float(x.iloc[-1])
    try:
        return float(x)
    except Exception:
        return None


def _yoy(series: pd.Series, periods=12):
    series = series.dropna()
    if len(series) < periods + 1:
        return None
    return (series.iloc[-1] / series.iloc[-1 - periods] - 1) * 100


def _safe_key(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in s)


def _line_chart(df, title, y_title, cols_to_plot, name_map=None, key="chart"):
    name_map = name_map or {}

    # only cols
    cols_ok = []
    for c in cols_to_plot:
        if c in df.columns and df[c].dropna().shape[0] > 0:
            cols_ok.append(c)

    if len(cols_ok) == 0:
        st.info("No data available for this chart (filters/dataset may not include this country).")
        return

    fig = go.Figure()
    for c in cols_ok:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[c],
            mode="lines",
            name=name_map.get(c, c)
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Year",
        yaxis_title=y_title,
        hovermode="x unified",
        template="plotly_white",
        legend_title_text=""
    )
    fig.update_xaxes(rangeslider_visible=True)

    #  Unique key 
    st.plotly_chart(fig, use_container_width=True, key=_safe_key(key))


def big_numbers_block(title, inflation_df, interest_df, unemp_df, pop_df, gdp_df, gdp_pc_df, geo):
    st.subheader(title)

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    # Inflation YoY
    if geo in inflation_df.columns:
        yoy = _yoy(inflation_df[geo], 12)
        last = _latest_value(inflation_df[geo])
        c1.metric("Inflation YoY", "—" if yoy is None else f"{yoy:.2f}%", "Index" if last is None else f"Index {last:.1f}")
    else:
        c1.metric("Inflation YoY", "—")

    # Interest
    if geo in interest_df.columns:
        last = _latest_value(interest_df[geo])
        c2.metric("Interest (latest)", "—" if last is None else f"{last:.2f}")
    else:
        c2.metric("Interest (latest)", "—")

    # Unemployment
    if geo in unemp_df.columns:
        last = _latest_value(unemp_df[geo])
        c3.metric("Unemployment (latest)", "—" if last is None else f"{last:.2f}%")
    else:
        c3.metric("Unemployment (latest)", "—")

    # Population
    if geo in pop_df.columns:
        last = _latest_value(pop_df[geo])
        c4.metric("Population (latest)", "—" if last is None else f"{last:,.0f}")
    else:
        c4.metric("Population (latest)", "—")

    

    # GDP per capita
    if geo in gdp_pc_df.columns:
        last = _latest_value(gdp_pc_df[geo])
        c6.metric("GDP per capita", "—" if last is None else f"{last:,.0f} EUR")
    else:
        c6.metric("GDP per capita", "—")


def inflation_chart(inflation_df, key_prefix=""):
    st.header("Inflation")
    _line_chart(
        inflation_df,
        "Inflation (HICP Index 2015=100)",
        "Index (2015=100)",
        ["SE", "EU"],
        name_map={"SE": "Sweden", "EU": "Europe"},
        key=f"{key_prefix}_inflation"
    )


def interest_chart(interest_df, geo, key_prefix=""):
    st.header("Interest rate")
    _line_chart(
        interest_df,
        f"Interest rate ({geo})",
        "Rate",
        [geo],
        name_map={"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"},
        key=f"{key_prefix}_interest_{geo}"
    )


def unemployment_chart(unemp_df, geo, key_prefix=""):
    st.header("Unemployment rate")
    _line_chart(
        unemp_df,
        f"Unemployment rate ({geo})",
        "%",
        [geo],
        name_map={"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"},
        key=f"{key_prefix}_unemp_{geo}"
    )


def comparison_section(inflation_df, interest_df, unemp_df, key_prefix=""):
    st.header("Comparison")

    all_opts = ["SE", "EU", "DK", "FI", "NO"]
    available = [c for c in all_opts if (c in inflation_df.columns or c in interest_df.columns or c in unemp_df.columns)]

    selected = st.multiselect(
        "Select countries/regions",
        options=available,
        default=[c for c in ["SE", "EU", "DK", "FI"] if c in available],
        key=f"{key_prefix}_cmp_select"
    )

    name_map = {"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}

    st.subheader("Inflation")
    _line_chart(inflation_df, "Inflation comparison", "Index (2015=100)", selected, name_map, key=f"{key_prefix}_cmp_inflation")

    st.subheader("Interest rate")
    _line_chart(interest_df, "Interest comparison", "Rate", selected, name_map, key=f"{key_prefix}_cmp_interest")

    st.subheader("Unemployment")
    _line_chart(unemp_df, "Unemployment comparison", "%", selected, name_map, key=f"{key_prefix}_cmp_unemp")
