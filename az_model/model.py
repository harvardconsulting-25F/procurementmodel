import pandas as pd
import os
import datetime as dt

# === CONFIGURATION ===
data_dir = "data"
compiled_file = os.path.join(data_dir, "compiled_percentage_changes.csv")

# === LOAD DATA ===
df = pd.read_csv(compiled_file)
df = df[["category", "pct_change"]].dropna().reset_index(drop=True)

# Separate each category - get last 4 observations
capital = df[df["category"] == "capital"]["pct_change"].tail(4).tolist()
energy = df[df["category"] == "energy"]["pct_change"].tail(4).tolist()
materials = df[df["category"] == "materials"]["pct_change"].tail(4).tolist()

# === LABOR (dummy data for now) ===
# Uncomment below when labor data is added to compiled_percentage_changes.csv
labor = df[df["category"] == "labor"]["pct_change"].tail(4).tolist()

# Dummy data for now - representing t-3, t-2, t-1, t (oldest to newest)
# labor = [1, 2, 3, 4]  # percentage changes

print("=== Loaded last 4 % changes (oldest to newest) ===")
print("Labor:", labor)
print("Capital:", capital)
print("Energy:", energy)
print("Materials:", materials)
print()

# === CALCULATE ΔP_t% ===
# The formula requires data from t, t-1, t-2, t-3
# We can only compute ΔP for the most recent period (index 3)
# since it needs 3 prior periods of data

results = []

# Check if we have enough data
if len(labor) >= 4 and len(capital) >= 4 and len(materials) >= 4 and len(energy) >= 4:
    # Map indices: [0]=t-3, [1]=t-2, [2]=t-1, [3]=t
    L_t = labor[3]
    L_t1 = labor[2]
    L_t2 = labor[1]
    L_t3 = labor[0]
    
    K_t = capital[3]
    K_t1 = capital[2]
    K_t2 = capital[1]
    K_t3 = capital[0]
    
    M_t = materials[3]
    M_t1 = materials[2]
    M_t2 = materials[1]
    M_t3 = materials[0]
    
    E_t = energy[3]
    E_t1 = energy[2]
    E_t2 = energy[1]
    E_t3 = energy[0]
    
    # Apply formula
    term1 = (0.14*L_t + 0.07*K_t + 0.07*M_t + 0.04*E_t)
    term2 = (0.07*L_t1 + 0.07*K_t1 + 0.07*M_t1 + 0.08*E_t1)
    term3 = (0.05*L_t2 + 0.01*K_t2 + 0.04*M_t2 + 0.08*E_t2)
    # Note: The formula shows -0.11 for capital in term4, which when subtracted gives +0.11
    term4 = (0.06*L_t3 - 0.11*K_t3 + 0.04*M_t3 + 0.08*E_t3)
    
    delta_P_raw = term1 + term2 - term3 - term4
    delta_P = max(0.0, delta_P_raw)
    
    results.append({
        "period": "t (most recent)",
        "Δw_L_t%": L_t,
        "Δw_K_t%": K_t,
        "Δw_M_t%": M_t,
        "Δw_E_t%": E_t,
        "Δw_L_t-1%": L_t1,
        "Δw_K_t-1%": K_t1,
        "Δw_M_t-1%": M_t1,
        "Δw_E_t-1%": E_t1,
        "Δw_L_t-2%": L_t2,
        "Δw_K_t-2%": K_t2,
        "Δw_M_t-2%": M_t2,
        "Δw_E_t-2%": E_t2,
        "Δw_L_t-3%": L_t3,
        "Δw_K_t-3%": K_t3,
        "Δw_M_t-3%": M_t3,
        "Δw_E_t-3%": E_t3,
        "ΔP_t_raw%": delta_P_raw,
        "ΔP_t%": delta_P,
        "term1": term1,
        "term2": term2,
        "term3": term3,
        "term4": term4
    })
    
    print("✅ Model computed successfully!")
else:
    print("❌ Error: Need at least 4 periods of data for all categories")

# === OUTPUT RESULTS ===
if results:
    results_df = pd.DataFrame(results)
    
    output_csv = os.path.join(data_dir, "model_price_change_results.csv")
    output_txt = os.path.join(data_dir, "model_price_change_results.txt")
    
    results_df.to_csv(output_csv, index=False)
    
    with open(output_txt, "w") as f:
        f.write(f"ΔP_t% Computation Results (as of {dt.datetime.now()})\n")
        f.write("="*60 + "\n\n")
        
        row = results[0]
        f.write("CURRENT PERIOD (t):\n")
        f.write(f"  Δw_L_t% = {row['Δw_L_t%']:.3f}\n")
        f.write(f"  Δw_K_t% = {row['Δw_K_t%']:.3f}\n")
        f.write(f"  Δw_M_t% = {row['Δw_M_t%']:.3f}\n")
        f.write(f"  Δw_E_t% = {row['Δw_E_t%']:.3f}\n\n")
        
        f.write("FORMULA COMPUTATION:\n")
        f.write(f"  Term 1 (coeffs at t)   = {row['term1']:.4f}\n")
        f.write(f"  Term 2 (coeffs at t-1) = {row['term2']:.4f}\n")
        f.write(f"  Term 3 (coeffs at t-2) = {row['term3']:.4f}\n")
        f.write(f"  Term 4 (coeffs at t-3) = {row['term4']:.4f}\n\n")
        
        f.write(f"RESULT:\n")
        f.write(f"  ΔP_t% = {row['term1']:.4f} + {row['term2']:.4f} - {row['term3']:.4f} - {row['term4']:.4f}\n")
        f.write(f"  Raw ΔP_t% = {row['ΔP_t_raw%']:.4f}%\n")
        f.write(f"  ΔP_t% (floor at 0) = {row['ΔP_t%']:.4f}%\n")
    
    print(f"\n✅ Results saved to:\n   • {output_csv}\n   • {output_txt}")
    print(f"\nPredicted price change (ΔP_t%): {results[0]['ΔP_t%']:.4f}% (raw {results[0]['ΔP_t_raw%']:.4f}%)")
else:
    print("No results to save.")