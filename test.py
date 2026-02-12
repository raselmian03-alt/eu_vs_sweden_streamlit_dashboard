import pandas as pd
import eurostat

df = eurostat.get_data_df("prc_hicp_midx")

# Column name in this dataset is literally "geo\TIME_PERIOD"
geo_col = "geo\\TIME_PERIOD"

# 1) Filter to what you want (SE + EA, CP00, I15)
df = df[
    df[geo_col].isin(["SE", "EA"]) &
    (df["coicop"] == "CP00") &
    (df["unit"] == "I15")
]

# 2) Keep ONLY the date columns (they look like "YYYY-MM") + geo
date_cols = [c for c in df.columns if isinstance(c, str) and c[:4].isdigit() and c[4:5] == "-" and c[5:7].isdigit()]
df = df[[geo_col] + date_cols]

# 3) Make geo into columns and dates into the index
df = (
    df.set_index(geo_col)   # rows keyed by geo (SE, EA)
      .T                    # dates become rows
)

# 4) Convert index to datetime (monthly)
df.index = pd.to_datetime(df.index, format="%Y-%m")

# Optional: rename EA to EU if you really want the column name "EU"
df = df.rename(columns={"EA": "EU"})

# Optional: sort by date
df = df.sort_index()

print(df.head())
print(df.index)
print(df.columns)
