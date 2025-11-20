"""
Flask API server to expose the price prediction model to the UI
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
import subprocess
import sys
from typing import Dict, List, Optional

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# === CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(BASE_DIR, "data")
compiled_file = os.path.join(data_dir, "compiled_percentage_changes.csv")
data_pipeline_scripts = [
    "download_labor.py",
    "download_capital.py",
    "download_materials.py",
    "download_energy.py",
    "compute_percentages.py",
]
_data_initialized = False

# Default coefficients (matching the model.py formula exactly)
# These are the raw coefficients used in model.py before the subtraction
DEFAULT_COEFFICIENTS = {
    "labor_t": 0.14,
    "capital_t": 0.07,
    "materials_t": 0.07,
    "energy_t": 0.04,
    "other_t": 0.06,
    "labor_t1": 0.07,
    "capital_t1": 0.07,
    "materials_t1": 0.07,
    "energy_t1": 0.08,
    "other_t1": 0.06,
    "labor_t2": 0.05,  # Will be subtracted in formula
    "capital_t2": 0.01,  # Will be subtracted in formula
    "materials_t2": 0.04,  # Will be subtracted in formula
    "energy_t2": 0.08,  # Will be subtracted in formula
    "other_t2": 0.02,  # Will be subtracted in formula
    "labor_t3": 0.06,  # Will be subtracted in formula
    "capital_t3": -0.11,  # Negative in model.py, becomes positive when subtracted
    "materials_t3": 0.04,  # Will be subtracted in formula
    "energy_t3": 0.08,  # Will be subtracted in formula
    "other_t3": 0.02,  # Will be subtracted in formula
}


def run_data_pipeline():
    """
    Rebuild the compiled percentage change data by running the downloader
    scripts followed by compute_percentages.py. This is useful for hosted
    environments (e.g., Render) where the data directory starts empty.
    """
    for script_name in data_pipeline_scripts:
        script_path = os.path.join(BASE_DIR, script_name)
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Data pipeline script missing: {script_name}")
        print(f"🔄 Running data prep script: {script_name}")
        subprocess.run([sys.executable, script_path], cwd=BASE_DIR, check=True)

    if not os.path.exists(compiled_file):
        raise FileNotFoundError(
            f"Data pipeline completed but {compiled_file} was not generated."
        )
    print("✅ Data pipeline completed successfully.")


def ensure_compiled_data():
    """
    Ensure compiled_percentage_changes.csv exists before serving API requests.
    """
    global _data_initialized
    if _data_initialized and os.path.exists(compiled_file):
        return

    if not os.path.exists(compiled_file):
        os.makedirs(data_dir, exist_ok=True)
        run_data_pipeline()

    _data_initialized = True


def load_latest_data() -> Dict[str, List[float]]:
    """
    Load the latest 4 percentage changes for each category from CSV.
    Returns data in format: {category: [t-3, t-2, t-1, t]}
    """
    try:
        ensure_compiled_data()
        if not os.path.exists(compiled_file):
            raise FileNotFoundError(f"Data file not found: {compiled_file}")
        
        df = pd.read_csv(compiled_file)
        df = df[["category", "pct_change"]].dropna().reset_index(drop=True)
        
        capital = df[df["category"] == "capital"]["pct_change"].tail(4).tolist()
        energy = df[df["category"] == "energy"]["pct_change"].tail(4).tolist()
        materials = df[df["category"] == "materials"]["pct_change"].tail(4).tolist()
        
        # Check if labor data exists, otherwise use dummy data
        labor_df = df[df["category"] == "labor"]
        if len(labor_df) >= 4:
            labor = labor_df["pct_change"].tail(4).tolist()
        else:
            # Dummy data as fallback
            labor = [1, 2, 3, 4]
        
        # Ensure we have at least some data for each category
        if len(capital) == 0:
            capital = [0, 0, 0, 0]
        if len(energy) == 0:
            energy = [0, 0, 0, 0]
        if len(materials) == 0:
            materials = [0, 0, 0, 0]
        
        return {
            "labor": labor,
            "capital": capital,
            "materials": materials,
            "energy": energy,
            "other": [0, 0, 0, 0],  # Placeholder manual input channel
        }
    except Exception as e:
        import traceback
        error_msg = f"Error loading data: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # Log to console
        raise Exception(error_msg)


def calculate_prediction(
    labor: List[float],
    capital: List[float],
    materials: List[float],
    energy: List[float],
    other: List[float],
    coefficients: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Calculate price prediction (ΔP_t%) using the model formula.
    
    Args:
        labor: [t-3, t-2, t-1, t] percentage changes
        capital: [t-3, t-2, t-1, t] percentage changes
        materials: [t-3, t-2, t-1, t] percentage changes
        energy: [t-3, t-2, t-1, t] percentage changes
        other: [t-3, t-2, t-1, t] manual adjustments
        coefficients: Optional custom coefficients dict
    
    Returns:
        Dictionary with prediction results
    """
    if (
        len(labor) < 4
        or len(capital) < 4
        or len(materials) < 4
        or len(energy) < 4
        or len(other) < 4
    ):
        raise ValueError("Need at least 4 periods of data for all categories")
    
    # Use default coefficients if not provided
    coeffs = coefficients or DEFAULT_COEFFICIENTS
    
    # Map indices: [0]=t-3, [1]=t-2, [2]=t-1, [3]=t
    L_t, L_t1, L_t2, L_t3 = labor[3], labor[2], labor[1], labor[0]
    K_t, K_t1, K_t2, K_t3 = capital[3], capital[2], capital[1], capital[0]
    M_t, M_t1, M_t2, M_t3 = materials[3], materials[2], materials[1], materials[0]
    E_t, E_t1, E_t2, E_t3 = energy[3], energy[2], energy[1], energy[0]
    O_t, O_t1, O_t2, O_t3 = other[3], other[2], other[1], other[0]
    
    # Apply formula (matching model.py logic)
    # term1 and term2 are added, term3 and term4 are subtracted
    term1 = (
        coeffs["labor_t"] * L_t
        + coeffs["capital_t"] * K_t
        + coeffs["materials_t"] * M_t
        + coeffs["energy_t"] * E_t
        + coeffs.get("other_t", 0) * O_t
    )
    term2 = (
        coeffs["labor_t1"] * L_t1
        + coeffs["capital_t1"] * K_t1
        + coeffs["materials_t1"] * M_t1
        + coeffs["energy_t1"] * E_t1
        + coeffs.get("other_t1", 0) * O_t1
    )
    
    # For term3 and term4, if coefficients come as negative from UI, use them directly
    # Otherwise, calculate with positive values and subtract
    # The UI sends negative values for t2 and t3 (except capital_t3), so we use them directly
    term3 = (
        coeffs["labor_t2"] * L_t2
        + coeffs["capital_t2"] * K_t2
        + coeffs["materials_t2"] * M_t2
        + coeffs["energy_t2"] * E_t2
        + coeffs.get("other_t2", 0) * O_t2
    )
    term4 = (
        coeffs["labor_t3"] * L_t3
        + coeffs["capital_t3"] * K_t3
        + coeffs["materials_t3"] * M_t3
        + coeffs["energy_t3"] * E_t3
        + coeffs.get("other_t3", 0) * O_t3
    )
    
    # Formula: delta_P = term1 + term2 - term3 - term4
    # The UI sends coefficients where t2 and t3 are already negative (except capital_t3)
    # So if coefficients are negative, term3/term4 will be negative, and adding them is equivalent to subtracting
    # If coefficients are positive (default), we explicitly subtract term3 and term4
    
    # Check if we're using UI-style coefficients (negative for t2/t3) or model.py style (positive)
    if coeffs.get("labor_t2", 0) < 0:
        # UI sends negative coefficients, so term3 and term4 are already negative
        # Adding negative values is equivalent to subtracting positive values
        delta_P_raw = term1 + term2 + term3 + term4
    else:
        # Using model.py style (positive coefficients), so subtract term3 and term4
        delta_P_raw = term1 + term2 - term3 - term4
    
    delta_P = max(0.0, delta_P_raw)
    
    # Calculate standard deviation (simple approximation for now)
    # In a real model, this would come from historical variance
    std_dev = abs(delta_P) * 0.15 + 0.5
    min_val = max(0.0, delta_P - 3 * std_dev)
    max_val = max(min_val, delta_P + 3 * std_dev)
    
    return {
        "delta_P": delta_P,
        "mean": delta_P,
        "stdDev": std_dev,
        "min": min_val,
        "max": max_val,
        "term1": term1,
        "term2": term2,
        "term3": term3,
        "term4": term4,
        "inputs": {
            "labor": {"t": L_t, "t-1": L_t1, "t-2": L_t2, "t-3": L_t3},
            "capital": {"t": K_t, "t-1": K_t1, "t-2": K_t2, "t-3": K_t3},
            "materials": {"t": M_t, "t-1": M_t1, "t-2": M_t2, "t-3": M_t3},
            "energy": {"t": E_t, "t-1": E_t1, "t-2": E_t2, "t-3": E_t3},
            "other": {"t": O_t, "t-1": O_t1, "t-2": O_t2, "t-3": O_t3},
        }
    }


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        "name": "AZ Model API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /api/health",
            "latest_data": "GET /api/data/latest",
            "predict": "POST /api/predict",
            "default_coefficients": "GET /api/coefficients/default"
        },
        "documentation": "See README_API.md for detailed API documentation"
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "API is running"})


@app.route('/api/data/latest', methods=['GET'])
def get_latest_data():
    """
    Get the latest 4 periods of data for each category.
    Returns the most recent values (t) for each category.
    """
    try:
        data = load_latest_data()
        
        # Return the most recent values (index 3, which is t)
        # Handle cases where we might not have 4 values
        def get_latest_value(values, default=0):
            if len(values) >= 4:
                return values[3]
            elif len(values) > 0:
                return values[-1]  # Return the last available value
            else:
                return default
        
        result = {
            "labor": get_latest_value(data["labor"]),
            "capital": get_latest_value(data["capital"]),
            "materials": get_latest_value(data["materials"]),
            "energy": get_latest_value(data["energy"]),
            "other": get_latest_value(data.get("other", [0, 0, 0, 0]), 0),
            "full_data": {
                "labor": data["labor"],
                "capital": data["capital"],
                "materials": data["materials"],
                "energy": data["energy"],
                "other": data.get("other", [0, 0, 0, 0]),
            }
        }
        
        return jsonify(result)
    except Exception as e:
        import traceback
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(f"Error in get_latest_data: {error_detail}")  # Log to console
        return jsonify({"error": str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Calculate price prediction with custom inputs and/or coefficients.
    
    Request body:
    {
        "labor": [t-3, t-2, t-1, t] or percentage weight (0-100),
        "capital": [t-3, t-2, t-1, t] or percentage weight,
        "materials": [t-3, t-2, t-1, t] or percentage weight,
        "energy": [t-3, t-2, t-1, t] or percentage weight,
        "other": [t-3, t-2, t-1, t] or percentage weight,
        "coefficients": {optional custom coefficients}
    }
    
    When single percentages are provided, the function scales the latest
    baseline data by the supplied share (must total 100% across categories).
    """
    try:
        req_data = request.get_json()
        
        # Load latest data as baseline
        latest_data = load_latest_data()
        
        def ensure_series(series: List[float]) -> List[float]:
            if len(series) >= 4:
                return series[-4:]
            return ([0.0] * (4 - len(series))) + series
        
        def process_input(value, category_key: str):
            base_series = ensure_series(latest_data.get(category_key, []))
            if isinstance(value, list) and len(value) == 4:
                return value
            if isinstance(value, (int, float)):
                weight = max(0.0, min(float(value), 100.0)) / 100.0
                if latest_data.get(category_key):
                    return [round(val * weight, 6) for val in base_series]
                manual_value = round(weight * 100, 6)
                return [manual_value] * 4
            return base_series if base_series else [0.0, 0.0, 0.0, 0.0]
        
        labor = process_input(req_data.get("labor"), "labor")
        capital = process_input(req_data.get("capital"), "capital")
        materials = process_input(req_data.get("materials"), "materials")
        energy = process_input(req_data.get("energy"), "energy")
        other = process_input(req_data.get("other"), "other")
        
        # Get custom coefficients if provided
        coefficients = req_data.get("coefficients")
        
        # Calculate prediction
        result = calculate_prediction(labor, capital, materials, energy, other, coefficients)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/coefficients/default', methods=['GET'])
def get_default_coefficients():
    """Get the default model coefficients"""
    return jsonify(DEFAULT_COEFFICIENTS)


if __name__ == '__main__':
    print("Starting Flask API server...")
    print("API will be available at http://localhost:5001")
    print("Endpoints:")
    print("  GET  /api/health - Health check")
    print("  GET  /api/data/latest - Get latest data from CSV")
    print("  POST /api/predict - Calculate prediction")
    print("  GET  /api/coefficients/default - Get default coefficients")
    app.run(debug=True, port=5001, host='127.0.0.1')
