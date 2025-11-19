# API Server Setup

This Flask API server connects the `az_model` Python model with the `az_ui_demo` React UI.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the API server:**
   ```bash
   python api.py
   ```

   The server will start on `http://localhost:5001`

## API Endpoints

### Health Check
- **GET** `/api/health`
- Returns API status

### Get Latest Data
- **GET** `/api/data/latest`
- Returns the most recent percentage changes from the CSV files
- Response format:
  ```json
  {
    "labor": 4.0,
    "capital": -1.54,
    "materials": 0.38,
    "energy": 7.53,
    "full_data": {
      "labor": [1, 2, 3, 4],
      "capital": [...],
      "materials": [...],
      "energy": [...]
    }
  }
  ```

### Calculate Prediction
- **POST** `/api/predict`
- Calculates price prediction (ΔP_t%) using the model formula
- Request body:
  ```json
  {
    "labor": 4.0,  // Single value (t) or [t-3, t-2, t-1, t] array
    "capital": -1.54,
    "materials": 0.38,
    "energy": 7.53,
    "coefficients": {  // Optional, uses defaults if not provided
      "labor_t": 0.14,
      "capital_t": 0.07,
      ...
    }
  }
  ```
- Response format:
  ```json
  {
    "delta_P": 2.45,
    "mean": 2.45,
    "stdDev": 0.87,
    "min": -0.16,
    "max": 5.06,
    "term1": 1.23,
    "term2": 0.89,
    "term3": 0.45,
    "term4": 0.22,
    "inputs": {
      "labor": {"t": 4.0, "t-1": 3.0, "t-2": 2.0, "t-3": 1.0},
      ...
    }
  }
  ```

### Get Default Coefficients
- **GET** `/api/coefficients/default`
- Returns the default model coefficients

## Connecting to UI

The React UI in `az_ui_demo` is configured to connect to `http://localhost:5001` by default.

To use a different API URL, set the environment variable:
```bash
VITE_API_URL=http://your-api-url:5001
```

Then rebuild the UI:
```bash
cd ../az_ui_demo
npm run build
```

## Running Both Projects

1. **Terminal 1 - Start API:**
   ```bash
   cd az_model
   python api.py
   ```

2. **Terminal 2 - Start UI:**
   ```bash
   cd az_ui_demo
   npm run dev
   ```

The UI will be available at `http://localhost:5173` (or the port shown by Vite).

