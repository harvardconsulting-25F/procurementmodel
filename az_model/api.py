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

# Vercel expects a module-level variable named `app`.
# Some Vercel builds look for `app = ...` in `api/index.py` or similar.
# Expose an alias so `app` is discoverable even if the module is imported differently.
flask_app = app

# === CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(BASE_DIR, "data")
compiled_file = os.path.join(data_dir, "compiled_percentage_changes.csv")
AUTO_BUILD_DATA = os.environ.get("AUTO_BUILD_DATA", "1") not in {"0", "false", "False"}
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


if AUTO_BUILD_DATA:
    try:
        ensure_compiled_data()
    except Exception as exc:
        # Log but keep app running; first request will retry if needed.
        print(f"⚠️ Auto data build failed during startup: {exc}")


def load_latest_data(history_points: int = 24) -> Dict[str, Dict[str, List]]:
    """Return historical pct-change series for each category."""
    try:
        ensure_compiled_data()
        if not os.path.exists(compiled_file):
            raise FileNotFoundError(f"Data file not found: {compiled_file}")

        df = pd.read_csv(compiled_file)
        if "date" not in df.columns:
            df["date"] = pd.date_range(end=pd.Timestamp.today(), periods=len(df))
        df = df[["category", "pct_change", "date"]].dropna().reset_index(drop=True)

        response: Dict[str, Dict[str, List]] = {}
        categories = ["labor", "capital", "materials", "energy"]
        for category in categories:
            category_df = df[df["category"] == category].tail(history_points)
            history_records = []
            for _, row in category_df.iterrows():
                history_records.append({
                    "date": str(row["date"]),
                    "pct_change": float(row["pct_change"])
                })

            values = [record["pct_change"] for record in history_records]
            recent = values[-4:] if len(values) >= 4 else values
            if not recent:
                recent = [0.0, 0.0, 0.0, 0.0]

            response[category] = {
                "history": history_records,
                "recent": recent,
                "latest": recent[-1] if recent else 0.0,
            }

        # placeholder for manual/other channel
        response["other"] = {
            "history": [{"date": "", "pct_change": 0.0} for _ in range(min(4, history_points))],
            "recent": [0.0, 0.0, 0.0, 0.0],
            "latest": 0.0,
        }
        return response
    except Exception as e:
        import traceback
        error_msg = f"Error loading data: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
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

        def latest_value(category: str) -> float:
            return float(data.get(category, {}).get("latest", 0.0))

        result = {
            "labor": latest_value("labor"),
            "capital": latest_value("capital"),
            "materials": latest_value("materials"),
            "energy": latest_value("energy"),
            "other": latest_value("other"),
            "full_data": {
                "labor": data.get("labor", {}).get("recent", []),
                "capital": data.get("capital", {}).get("recent", []),
                "materials": data.get("materials", {}).get("recent", []),
                "energy": data.get("energy", {}).get("recent", []),
                "other": data.get("other", {}).get("recent", []),
            },
            "history": {
                "labor": data.get("labor", {}).get("history", []),
                "capital": data.get("capital", {}).get("history", []),
                "materials": data.get("materials", {}).get("history", []),
                "energy": data.get("energy", {}).get("history", []),
                "other": data.get("other", {}).get("history", []),
            },
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


@app.route('/api/data/history', methods=['GET'])
def get_history_data():
    try:
        data = load_latest_data()
        return jsonify({
            "labor": data.get("labor", {}).get("history", []),
            "capital": data.get("capital", {}).get("history", []),
            "materials": data.get("materials", {}).get("history", []),
            "energy": data.get("energy", {}).get("history", []),
        })
    except Exception as e:
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
        
        latest_data = load_latest_data()
        weights_payload = req_data.get("weights")
        series_override = req_data.get("series") if isinstance(req_data.get("series"), dict) else {}

        def ensure_series(series: List[float]) -> List[float]:
            if len(series) >= 4:
                return series[-4:]
            return ([0.0] * (4 - len(series))) + series

        def get_base_series(category_key: str) -> List[float]:
            override_series = series_override.get(category_key)
            if isinstance(override_series, list) and len(override_series) > 0:
                normalized: List[float] = []
                for val in override_series:
                    try:
                        normalized.append(float(val))
                    except (TypeError, ValueError):
                        continue
                if normalized:
                    return ensure_series(normalized)
                return ensure_series(override_series)
            category_payload = latest_data.get(category_key, {})
            return ensure_series(category_payload.get("recent", []))

        def apply_weight(series: List[float], weight_value) -> List[float]:
            try:
                weight = float(weight_value)
            except (TypeError, ValueError):
                weight = 0.0
            weight = max(0.0, min(weight, 100.0)) / 100.0
            return [round(val * weight, 6) for val in series]

        def process_input(value, category_key: str):
            base_series = get_base_series(category_key)
            if isinstance(value, list) and len(value) == 4:
                return value
            if isinstance(value, (int, float)):
                weight = max(0.0, min(float(value), 100.0)) / 100.0
                if base_series:
                    return [round(val * weight, 6) for val in base_series]
                manual_value = round(weight * 100, 6)
                return [manual_value] * 4
            return base_series if base_series else [0.0, 0.0, 0.0, 0.0]

        if isinstance(weights_payload, dict):
            labor = apply_weight(get_base_series("labor"), weights_payload.get("labor", 0))
            capital = apply_weight(get_base_series("capital"), weights_payload.get("capital", 0))
            materials = apply_weight(get_base_series("materials"), weights_payload.get("materials", 0))
            energy = apply_weight(get_base_series("energy"), weights_payload.get("energy", 0))
            other = apply_weight(get_base_series("other"), weights_payload.get("other", 0))
        else:
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
