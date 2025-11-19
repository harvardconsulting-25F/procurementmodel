import pandas as pd
import datetime as dt
import requests
import io
import os

# FRED series ID — Total Labor Cost Per Unit of Output, Manufacturing
series_id = "M08324USM350SNBR"

# FRED CSV URL
csv_url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

# Download CSV
resp = requests.get(csv_url, timeout=120)
resp.raise_for_status()

# Read CSV
df = pd.read_csv(io.StringIO(resp.text))

# Rename columns (date, value)
df = df.rename(columns={df.columns[0]: "date", df.columns[1]: "value"})
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date", "value"])

# Sort by date and keep last 5 records
df = df.sort_values("date", ascending=True)
latest_date = df["date"].max()
five_months_ago = latest_date - pd.DateOffset(months=5)
df_last5 = df[df["date"] > five_months_ago].reset_index(drop=True)

print(f"Loaded {len(df_last5)} records (last 5 months)")
print(df_last5.head())

# Create output folder
os.makedirs("data", exist_ok=True)

# Define output file paths
output_csv = os.path.join("data", "labor_last5months.csv")
output_txt = os.path.join("data", "labor_last5months.txt")

# Save outputs
df_last5.to_csv(output_csv, index=False)

with open(output_txt, "w") as f:
    f.write(f"FRED series {series_id} — last 5 months data fetched on {dt.datetime.now()}\n")
    f.write(f"Total records: {len(df_last5)}\n\n")
    f.write(df_last5.to_string(index=False))

print(f"\n✅ Last 5 months of labor cost data saved to:\n  - {output_txt}\n  - {output_csv}")
