import pandas as pd
import eurostat
import streamlit as st
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import time as _time

# --- Local file cache ---
_CACHE_DIR = Path(__file__).resolve().parent.parent / ".data_cache"
_CACHE_MAX_AGE_HOURS = 6
_START_YEAR = "1990"

# All Eurostat dataset codes used by this app
_ALL_DATASETS = ("prc_hicp_midx", "une_rt_m", "demo_pjan", "nama_10_gdp", "irt_lt_mcby_m", "gov_10dd_edpt1", "irt_st_m")


def _cache_path(dataset_code: str) -> Path:
    return _CACHE_DIR / f"{dataset_code}.parquet"


def _is_cache_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age_hours = (_time.time() - path.stat().st_mtime) / 3600
    return age_hours < _CACHE_MAX_AGE_HOURS


def _fetch_and_cache(dataset_code: str) -> pd.DataFrame:
    """Fetch from Eurostat API and save to local parquet."""
    path = _cache_path(dataset_code)
    if _is_cache_fresh(path):
        return pd.read_parquet(path)
    df = eurostat.get_data_df(dataset_code)
    _CACHE_DIR.mkdir(exist_ok=True)
    df.to_parquet(path, index=False)
    return df


def prefetch_all():
    """Fetch all datasets in parallel, saving to local parquet cache."""
    stale = [d for d in _ALL_DATASETS if not _is_cache_fresh(_cache_path(d))]
    if not stale:
        return  # all cached — nothing to do
    with ThreadPoolExecutor(max_workers=len(stale)) as pool:
        list(pool.map(_fetch_and_cache, stale))


def _get_dataset(dataset_code: str) -> pd.DataFrame:
    """Read from local cache (fast) or fetch if stale."""
    path = _cache_path(dataset_code)
    if _is_cache_fresh(path):
        return pd.read_parquet(path)
    return _fetch_and_cache(dataset_code)


# --- Helpers ---

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
    return pd.to_datetime(s, errors="coerce")


def _merge_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.columns.duplicated().any():
        df = df.T.groupby(level=0).mean(numeric_only=True).T
    return df


def _clip_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows from 1980 onward."""
    return df[df.index >= "1990-01-01"]


def _load_wide(dataset_code: str, geo_list, filters: dict, rename_geo=None):
    df = _get_dataset(dataset_code).copy()

    geo_raw = "geo\\TIME_PERIOD" if "geo\\TIME_PERIOD" in df.columns else "geo"
    df["geo"] = df[geo_raw]

    mask = df["geo"].isin(list(geo_list))
    for k, v in (filters or {}).items():
        if k in df.columns:
            mask &= (df[k] == v)
    df = df[mask].copy()

    time_cols = _detect_time_cols(df.columns)
    df = df[["geo"] + time_cols]
    numeric = df[time_cols].apply(pd.to_numeric, errors="coerce")
    numeric["geo"] = df["geo"].values
    df = numeric.groupby("geo")[time_cols].mean()  # index = geo, cols = time

    out = df.T
    out.index = _to_datetime_index(out.index)
    out = out.sort_index()

    if rename_geo:
        out = out.rename(columns=rename_geo)

    out = _merge_duplicate_columns(out)
    out = out.dropna(axis=1, how="all")

    return _clip_dates(out)


# --- Public loaders ---

@st.cache_data(ttl="6h")
def load_inflation(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    # Include "EU" geo code which has data from 1996 (EU27_2020 only from 2000)
    extended_geo = set(geo_list) | {"EU"}
    return _load_wide(
        "prc_hicp_midx",
        extended_geo,
        filters={"coicop": "CP00", "unit": "I15"},
        rename_geo={"EU27_2020": "EU"},
    )


@st.cache_data(ttl="6h")
def load_unemployment(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    return _load_wide(
        "une_rt_m",
        geo_list,
        filters={"age": "TOTAL", "sex": "T", "unit": "PC_ACT", "s_adj": "SA"},
        rename_geo={"EU27_2020": "EU"},
    )


@st.cache_data(ttl="6h")
def load_population(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    return _load_wide(
        "demo_pjan",
        geo_list,
        filters={"sex": "T", "age": "TOTAL"},
        rename_geo={"EU27_2020": "EU"},
    )


@st.cache_data(ttl="6h")
def load_gdp(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    return _load_wide(
        "nama_10_gdp",
        geo_list,
        filters={"na_item": "B1GQ", "unit": "CP_MEUR"},
        rename_geo={"EU27_2020": "EU"},
    )


@st.cache_data(ttl="6h")
def load_gdp_per_capita(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    gdp = load_gdp(geo_list=geo_list)
    pop = load_population(geo_list=geo_list)

    common_idx = gdp.index.intersection(pop.index)
    gdp = gdp.loc[common_idx]
    pop = pop.loc[common_idx]

    gdp_pc = (gdp * 1_000_000) / pop
    gdp_pc = gdp_pc.round(0)
    return gdp_pc.dropna(axis=1, how="all")


@st.cache_data(ttl="6h")
def load_unemployment_detail(geo="SE"):
    df = _get_dataset("une_rt_m").copy()

    geo_raw = "geo\\TIME_PERIOD" if "geo\\TIME_PERIOD" in df.columns else "geo"
    df["geo"] = df[geo_raw]
    df = df[(df["geo"] == geo) & (df["unit"] == "PC_ACT") & (df["s_adj"] == "SA")].copy()

    time_cols = _detect_time_cols(df.columns)

    slices = {
        "Total": (df["sex"] == "T") & (df["age"] == "TOTAL"),
        "Men": (df["sex"] == "M") & (df["age"] == "TOTAL"),
        "Women": (df["sex"] == "F") & (df["age"] == "TOTAL"),
        "Under 25": (df["sex"] == "T") & (df["age"] == "Y_LT25"),
        "25-74": (df["sex"] == "T") & (df["age"] == "Y25-74"),
    }

    frames = {}
    for label, mask in slices.items():
        row = df.loc[mask, time_cols].apply(pd.to_numeric, errors="coerce")
        if row.empty:
            continue
        series = row.mean()
        frames[label] = series

    out = pd.DataFrame(frames)
    out.index = _to_datetime_index(out.index)
    out = out.sort_index()
    return _clip_dates(out.dropna(how="all"))


@st.cache_data(ttl="6h")
def load_inflation_yoy(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    """Annual inflation rate (YoY % change of HICP index)."""
    hicp = load_inflation(geo_list=geo_list)
    yoy = hicp.pct_change(periods=12) * 100  # 12-month % change
    return yoy.dropna(how="all")


@st.cache_data(ttl="6h")
def load_debt_to_gdp(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    """Government gross debt as % of GDP (yearly). Norway not available.
    EA20 included for earlier EU data (from 1995 vs EU27_2020 from 2000)."""
    extended_geo = set(geo_list) | {"EA20"}
    return _load_wide(
        "gov_10dd_edpt1",
        extended_geo,
        filters={"unit": "PC_GDP", "sector": "S13", "na_item": "GD"},
        rename_geo={"EU27_2020": "EU", "EA20": "EU"},
    )


@st.cache_data(ttl="6h")
def load_interest_rates(geo_list=("SE", "EU27_2020", "DK", "FI", "NO")):
    """
    Long-term government bond yields (monthly).
    Note: Norway (NO) is not available in Eurostat interest rate datasets.
    """
    extended_geo = set(geo_list) | {"EA", "EA20"}
    return _load_wide(
        "irt_lt_mcby_m",
        extended_geo,
        filters={},
        rename_geo={"EU27_2020": "EU", "EA": "EU", "EA20": "EU"},
    )


@st.cache_data(ttl="6h")
def load_interest_rates_detail(geo="SE"):
    """Money market rates + long-term bond yield for a single country.
    Returns DataFrame with columns: Day-to-day, 1-month, 3-month, 6-month, Govt bond 10Y."""
    df = _get_dataset("irt_st_m").copy()
    geo_raw = "geo\\TIME_PERIOD" if "geo\\TIME_PERIOD" in df.columns else "geo"
    df["geo"] = df[geo_raw]
    df = df[df["geo"] == geo].copy()

    time_cols = _detect_time_cols(df.columns)

    rate_map = {
        "IRT_DTD": "Day-to-day",
        "IRT_M1": "1-month",
        "IRT_M3": "3-month",
        "IRT_M6": "6-month",
    }

    frames = {}
    for code, label in rate_map.items():
        row = df.loc[df["int_rt"] == code, time_cols].apply(pd.to_numeric, errors="coerce")
        if row.empty:
            continue
        frames[label] = row.mean()

    # Add long-term govt bond yield from the other dataset
    bond = _get_dataset("irt_lt_mcby_m").copy()
    geo_raw2 = "geo\\TIME_PERIOD" if "geo\\TIME_PERIOD" in bond.columns else "geo"
    bond["geo"] = bond[geo_raw2]
    bond_row = bond.loc[bond["geo"] == geo, _detect_time_cols(bond.columns)].apply(pd.to_numeric, errors="coerce")
    if not bond_row.empty:
        frames["Govt bond 10Y"] = bond_row.mean()

    out = pd.DataFrame(frames)
    out.index = _to_datetime_index(out.index)
    out = out.sort_index()
    return _clip_dates(out.dropna(how="all"))
