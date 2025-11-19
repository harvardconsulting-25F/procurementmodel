import pandas as pd
import datetime as dt
import os

# Relative path to the Excel file
xls_path = os.path.join("worldbank_excels", "CMO-Historical-Data-Monthly.xlsx")

# Load the Excel file
xls = pd.ExcelFile(xls_path)
# Automatically pick the sheet containing monthly prices
sheet_name = [s for s in xls.sheet_names if "monthly" in s.lower() or "prices" in s.lower()][0]
raw = pd.read_excel(xls, sheet_name=sheet_name, header=4)

# Drop the first row which contains units
df = raw.iloc[1:].copy()

# Identify columns
period_col_name = df.columns[0]  # e.g., 'Unnamed: 0'
commodity_val_cols = df.columns[1:].tolist()

# Melt the dataframe to long format
cm = df.melt(
    id_vars=[period_col_name],
    value_vars=commodity_val_cols,
    var_name="commodity",
    value_name="value"
).dropna()

# Rename the period column
cm = cm.rename(columns={period_col_name: "period"})

# Function to parse period strings to datetime
def parse_period(p):
    s = str(p)
    for fmt in ("%b-%Y", "%Y-%m", "%Y.%m", "%YM%m", "%Y M%m", "%YM%M", "%Y"):
        try:
            if len(s) == 4 and s.isdigit():
                return pd.to_datetime(s, format="%Y")
            return pd.to_datetime(s, format=fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return pd.NaT

cm["date"] = cm["period"].apply(parse_period)
cm = cm.dropna(subset=["date"]).sort_values("date")

# Filter by target commodities
targets_like = ["Crude oil, Brent", "Natural gas, Europe", "Copper", "Wheat"]
sel = pd.concat([
    cm[cm["commodity"].astype(str).str.contains(t, case=False, na=False)]
    for t in targets_like
]).copy()

# Convert values to numeric
sel["value"] = pd.to_numeric(sel["value"], errors='coerce')
sel = sel.dropna(subset=["value"])

sel = sel[["date","commodity","value"]].sort_values(["commodity","date"]).reset_index(drop=True)
print(f"Commodities data loaded: {len(sel)} records")
print(sel.head())

# Save outputs
output_txt = "commodities_data.txt"
output_csv = "commodities_data.csv"

with open(output_txt, "w") as f:
    f.write(f"World Bank Pink Sheet commodities data fetched on {dt.datetime.now()}\n")
    f.write(f"Total records: {len(sel)}\n\n")
    f.write(sel.to_string(index=False))

sel.to_csv(output_csv, index=False)
print(f"\n✅ Full commodities data saved to:\n  - {output_txt}\n  - {output_csv}")
