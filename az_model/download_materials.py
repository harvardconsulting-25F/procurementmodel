import pandas as pd
import datetime as dt
import requests
import io
import os

# Series info
series_id = "PCU325211325211"
friendly_name = "materials"  # for output filenames

# URL for full historical data
csv_url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd=1970-01-01&coed=2030-12-31"

# Download the CSV data
resp = requests.get(csv_url, timeout=120)
resp.raise_for_status()

# Read into DataFrame
df = pd.read_csv(io.StringIO(resp.text))

# Rename first two columns (usually date + value)
df = df.rename(columns={df.columns[0]: "date", df.columns[1]: "value"})
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# Filter to the last 5 months
latest_date = df["date"].max()
five_months_ago = latest_date - pd.DateOffset(months=5)
df_last5 = df[df["date"] > five_months_ago].reset_index(drop=True)

print(f"Loaded {len(df_last5)} records (last 5 months)")
print(df_last5.head())

# Create output folder if needed
os.makedirs("worldbank_excels", exist_ok=True)

# Save outputs
output_csv = os.path.join("data", f"{friendly_name}_last5months.csv")
output_txt = os.path.join("data", f"{friendly_name}_last5months.txt")

df_last5.to_csv(output_csv, index=False)

with open(output_txt, "w") as f:
    f.write(f"FRED series {series_id} ({friendly_name}) — last 5 months data fetched on {dt.datetime.now()}\n")
    f.write(f"Total records: {len(df_last5)}\n\n")
    f.write(df_last5.to_string(index=False))

print(f"\n✅ Last 5 months of {friendly_name} data saved to:\n  - {output_txt}\n  - {output_csv}")
