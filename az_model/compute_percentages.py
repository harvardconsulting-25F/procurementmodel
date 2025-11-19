import pandas as pd
import os
import datetime as dt

# Folder containing all data
data_dir = "data"

# Define expected files
datasets = {
    "capital": "capital_last5months.csv",
    "energy": "energy_data_last5months.csv",
    "labor": "labor_last5months.csv",
    "materials": "materials_last5months.csv"
}

compiled = []

for name, filename in datasets.items():
    path = os.path.join(data_dir, filename)
    if not os.path.exists(path):
        print(f"⚠️ Missing file for {name}: {filename}, skipping.")
        continue

    df = pd.read_csv(path)
    if "value" not in df.columns:
        print(f"❌ File {filename} missing 'value' column, skipping.")
        continue

    # Keep only last 5 data points
    df = df.sort_values("date").tail(5).reset_index(drop=True)

    # Calculate % change
    df["pct_change"] = df["value"].pct_change() * 100  # % change

    # Drop the first row (no change)
    df = df.dropna(subset=["pct_change"]).reset_index(drop=True)

    # Store only valid % change rows
    for i in range(len(df)):
        compiled.append({
            "category": name,
            "date": df.loc[i, "date"],
            "value": df.loc[i, "value"],
            "pct_change": df.loc[i, "pct_change"]
        })

compiled_df = pd.DataFrame(compiled)

# Sort by category/date
compiled_df = compiled_df.sort_values(["category", "date"]).reset_index(drop=True)

# Save outputs
output_csv = os.path.join(data_dir, "compiled_percentage_changes.csv")
output_txt = os.path.join(data_dir, "compiled_percentage_changes.txt")

compiled_df.to_csv(output_csv, index=False)

with open(output_txt, "w") as f:
    f.write(f"Compiled percentage changes across factors (as of {dt.datetime.now()})\n\n")
    for cat in compiled_df["category"].unique():
        f.write(f"== {cat.upper()} ==\n")
        sub = compiled_df[compiled_df["category"] == cat]
        f.write(sub.to_string(index=False))
        f.write("\n\n")

print(f"✅ Percentage changes calculated for {len(compiled_df['category'].unique())} datasets.")
print(f"Saved outputs:\n - {output_csv}\n - {output_txt}")
