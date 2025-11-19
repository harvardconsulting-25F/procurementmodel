import io, json, textwrap, datetime as dt
from dateutil import parser as dateparser
import requests
import pandas as pd
import matplotlib.pyplot as plt
import pycountry

pd.set_option("display.max_rows", 10)
pd.set_option("display.width", 120)

END = dt.date.today()
START = END - dt.timedelta(days=540)  # ~18 months lookback

BASE_CCY = "USD"
TARGETS = ["EUR", "JPY", "GBP"]  # extend as needed
DATE_FMT = "%Y-%m-%d"

print("Window:", START, "→", END)


# Fetch FX rates from frankfurter.dev (free, no API key required)
fx_url = "https://api.frankfurter.app"
params = {
    "from": BASE_CCY,
    "to": ",".join(TARGETS)
}

try:
    # Frankfurter API uses the date in the URL path for timeseries
    resp = requests.get(f"{fx_url}/{START.strftime(DATE_FMT)}..{END.strftime(DATE_FMT)}", params=params, timeout=60)
    resp.raise_for_status()
    fx_data = resp.json()


    rows = []
    # Frankfurter returns 'rates' under the 'date' key
    for d_str, rates_obj in fx_data.get("rates", {}).items():
        for ccy, rate in rates_obj.items():
            rows.append({"date": pd.to_datetime(d_str), "pair": f"{BASE_CCY}/{ccy}", "rate": float(rate)})
    fx = pd.DataFrame(rows).sort_values("date")

    if fx.empty:
        print("No FX data received from frankfurter.dev. Check API parameters or date range.")
    else:
        print(f"FX data successfully fetched from frankfurter.dev. ({len(fx)} records)")
        print(fx.head())

        # --- SAVE RESULTS HERE ---
        output_txt = "fx_data.txt"
        output_csv = "fx_data.csv"

        with open(output_txt, "w") as f:
            f.write(f"FX data fetched on {dt.datetime.now()}\n")
            f.write(f"Window: {START} → {END}\n")
            f.write(f"Records: {len(fx)}\n\n")
            f.write(fx.to_string(index=False))

        fx.to_csv(output_csv, index=False)
        print(f"\n✅ Full FX data saved to:\n  - {output_txt}\n  - {output_csv}")


except requests.exceptions.RequestException as e:
    print(f"Error fetching FX data: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"HTTP Status: {e.response.status_code}")
        print(f"Response text: {e.response.text[:200]}")
    fx = pd.DataFrame(columns=["date", "pair", "rate"]) # Initialize empty DataFrame on error
except Exception as e:
    print(f"An unexpected error occurred while processing FX data: {e}")
    fx = pd.DataFrame(columns=["date", "pair", "rate"]) # Initialize empty DataFrame on error

# Plot FX rates
for pair, g in fx.groupby("pair"):
    plt.figure(figsize=(7,3.5))
    plt.plot(g["date"], g["rate"])
    plt.title(f"FX {pair}")
    plt.xlabel("Date"); plt.ylabel("Rate")
    plt.grid(True)
    plt.show()

print(fx["date"].min(), "→", fx["date"].max())
print(f"Records: {len(fx)}")
