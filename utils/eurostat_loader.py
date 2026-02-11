import pandas as pd
import eurostat
import streamlit as st


def _detect_time_cols(cols):
    out = []
    for c in cols:
        if not isinstance(c, str):
            continue
        if len(c) == 4 and c.isdigit():
            out.append(c)
        elif len(c) == 7 and c[:4].isdigit() and c[4] == "-" and c[5:7].isdigit():
            out.append(c)
    return out


def _to_datetime_index(idx):
    s = idx.astype(str)
    if s.str.match(r"^\d{4}-\d{2}$").all():
        return pd.to_datetime(s, format="%Y-%m")
    if s.str.match(r"^\d{4}$").all():
        return pd.to_datetime(s + "-01-01", format="%Y-%m-%d")
    return pd.to_datetime(s, errors="coercester")


def _merge_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    
    if df.columns.duplicated().any():
        df = df.groupby(level=0, axis=1).mean(numeric_only=True)
    return df


def _load_wide(dataset_code: str, geo_list, filters: dict, rename_geo=None):
    """
    Loads eurostat wide format:
    - filters
    - keeps only time columns
    - ensures 1 row per geo (fixes duplicates)
    - returns: index=datetime, columns=geo
    """
    df = eurostat.get_data_df(dataset_code)

    geo_raw = "geo\\TIME_PERIOD" if "geo\\TIME_PERIOD" in df.columns else "geo"
    df["geo"] = df[geo_raw]

    # filter geo + other filters
    mask = df["geo"].isin(list(geo_list))
    for k, v in (filters or {}).items():
        if k in df.columns:
            mask &= (df[k] == v)
    df = df[mask].copy()

    time_cols = _detect_time_cols(df.columns)
    df = df[["geo"] + time_cols].copy()

    # numeric time columns
    df[time_cols] = df[time_cols].apply(pd.to_numeric, errors="coerce")

    # multiple rows per geo -> aggregate to 1 row per geo
    df = df.groupby("geo", as_index=False)[time_cols].mean(numeric_only=True)

    # wide -> time rows
    out = df.set_index("geo").T
    out.index = _to_datetime_index(out.index)
    out = out.sort_index()

    # rename geo codes
    if rename_geo:
        out = out.rename(columns=rename_geo)

    #  rename can create duplicates -> merge duplicates safely
    out = _merge_duplicate_columns(out)

    # drop empty columns
    out = out.dropna(axis=1, how="all")

    return out




@st.cache_data
def load_inflation(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    # HICP Index 2015=100
    return _load_wide(
        "prc_hicp_midx",
        geo_list,
        filters={"coicop": "CP00", "unit": "I15"},
        rename_geo={"EU27_2020": "EU"},
    )


@st.cache_data
def load_unemployment(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    # Monthly unemployment rate, seasonally adjusted
    return _load_wide(
        "une_rt_m",
        geo_list,
        filters={"age": "Y15-74", "sex": "T", "unit": "PC_ACT", "s_adj": "SA"},
        rename_geo={"EU27_2020": "EU"},
    )


@st.cache_data
def load_population(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    # Population on 1 January (yearly)
    return _load_wide(
        "demo_pjan",
        geo_list,
        filters={"sex": "T", "age": "TOTAL"},
        rename_geo={"EU27_2020": "EU"},
    )


@st.cache_data
def load_gdp(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    # GDP in million euro (yearly)
    return _load_wide(
        "nama_10_gdp",
        geo_list,
        filters={"na_item": "B1GQ", "unit": "CP_MEUR"},
        rename_geo={"EU27_2020": "EU"},
    )


@st.cache_data
def load_gdp_per_capita(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    """
    GDP per capita (EUR/person) = GDP(MEUR)*1_000_000 / population
    """
    gdp = load_gdp(geo_list=geo_list)        # MEUR
    pop = load_population(geo_list=geo_list) # persons

    common_idx = gdp.index.intersection(pop.index)
    gdp = gdp.loc[common_idx]
    pop = pop.loc[common_idx]

    gdp_pc = (gdp * 1_000_000) / pop
    gdp_pc = gdp_pc.round(0)

    return gdp_pc.dropna(axis=1, how="all")


@st.cache_data
def load_interest_rates(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    """
    irt_st_m can contain MANY rows per geo => we must aggregate.
    We keep it simple: filter geo, keep time columns, mean per geo.
    """
    df = eurostat.get_data_df("irt_st_m")

    geo_raw = "geo\\TIME_PERIOD" if "geo\\TIME_PERIOD" in df.columns else "geo"
    df["geo"] = df[geo_raw]

    df = df[df["geo"].isin(list(geo_list))].copy()

    time_cols = _detect_time_cols(df.columns)
    df = df[["geo"] + time_cols].copy()

    df[time_cols] = df[time_cols].apply(pd.to_numeric, errors="coerce")

    df = df.groupby("geo", as_index=False)[time_cols].mean(numeric_only=True)

    out = df.set_index("geo").T
    out.index = _to_datetime_index(out.index)
    out = out.sort_index()

    # rename EU
    out = out.rename(columns={"EU27_2020": "EU"})

    #  merge duplicates if any
    out = _merge_duplicate_columns(out)

    return out.dropna(axis=1, how="all")
