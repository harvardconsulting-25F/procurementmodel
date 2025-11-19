import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
import os
import io

# --- Step 1: Download the latest Monthly Excel file ---
url = "https://www.worldbank.org/en/research/commodity-markets"
save_dir = "data"

if not os.path.exists(save_dir):
    os.makedirs(save_dir)
else:
    print(f"Saving files to existing folder: {save_dir}")

# Get the World Bank commodity markets page
response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

# Find all .xls and .xlsx links
links = soup.find_all("a", href=True)
excel_links = [link['href'] for link in links if link['href'].endswith(('.xls', '.xlsx'))]

# Filter only the "Monthly" file
monthly_links = [link for link in excel_links if "Monthly" in link or "monthly" in link]

if not monthly_links:
    raise Exception("❌ No monthly Excel file found on the World Bank commodity markets page.")

# Download the first matching monthly link
file_url = monthly_links[0]
if file_url.startswith("/"):
    file_url = "https://www.worldbank.org" + file_url

excel_path = os.path.join(save_dir, "CMO-Historical-Data-Monthly.xlsx")
print(f"Downloading latest monthly commodities file from:\n{file_url}")

r = requests.get(file_url)
r.raise_for_status()
with open(excel_path, "wb") as f:
    f.write(r.content)

print(f"✅ Downloaded: {excel_path}")

# --- Step 2: Process the Excel file for 'Natural gas, US' ---

xls = pd.ExcelFile(excel_path)
# Pick the sheet that contains monthly prices
sheet_name = [s for s in xls.sheet_names if "monthly" in s.lower() or "prices" in s.lower()][0]
raw = pd.read_excel(xls, sheet_name=sheet_name, header=4)

# Drop first row (units)
df = raw.iloc[1:].copy()

# Identify columns
period_col_name = df.columns[0]
commodity_val_cols = df.columns[1:].tolist()

# Reshape long format
cm = df.melt(
    id_vars=[period_col_name],
    value_vars=commodity_val_cols,
    var_name="commodity",
    value_name="value"
).dropna()

cm = cm.rename(columns={period_col_name: "period"})

# Helper function to parse dates
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

# --- Step 3: Filter by target commodity ---
targets_like = ["Natural gas, US"]
sel = pd.concat([
    cm[cm["commodity"].astype(str).str.contains(t, case=False, na=False)]
    for t in targets_like
]).copy()

# Convert and filter
sel["value"] = pd.to_numeric(sel["value"], errors='coerce')
sel = sel.dropna(subset=["value"])

# Keep last 5 months
latest_date = sel["date"].max()
five_months_ago = latest_date - pd.DateOffset(months=5)
sel = sel[sel["date"] > five_months_ago]

sel = sel[["date", "commodity", "value"]].sort_values(["commodity", "date"]).reset_index(drop=True)

print(f"\n✅ Commodities data loaded (last 5 months): {len(sel)} records")
print(sel.head())

# --- Step 4: Save outputs ---
output_txt = os.path.join(save_dir, "energy_data_last5months.txt")
output_csv = os.path.join(save_dir, "energy_data_last5months.csv")

with open(output_txt, "w") as f:
    f.write(f"World Bank Pink Sheet commodities data (last 5 months) fetched on {dt.datetime.now()}\n")
    f.write(f"Total records: {len(sel)}\n\n")
    f.write(sel.to_string(index=False))

sel.to_csv(output_csv, index=False)

print(f"\n✅ Last 5 months 'Natural gas, US' data saved to:\n  - {output_txt}\n  - {output_csv}")
