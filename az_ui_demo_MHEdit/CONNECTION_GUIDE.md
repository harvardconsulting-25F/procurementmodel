# Connecting az_ui_demo to az_model API

Your existing `az_ui_demo` UI project has been updated to connect to the `az_model` API.

## Quick Start

### 1. Start the API Server (from az_model directory)

```bash
cd ../az_model
pip install -r requirements.txt  # If you haven't already
python api.py
```

The API will run on `http://localhost:5001`

### 2. Start the UI (from az_ui_demo directory)

```bash
# Make sure you're in az_ui_demo directory
npm install  # If you haven't already installed dependencies
npm run dev
```

The UI will run on `http://localhost:5173` (or the port shown by Vite)

## What's Connected

✅ **Load External Data** button - Now loads real data from `az_model/data/compiled_percentage_changes.csv`

✅ **Cost Inputs** - When you change values, predictions are calculated using the actual model from `az_model/model.py`

✅ **Coefficient Editor** - Adjusting coefficients triggers real-time calculations via the API

✅ **Prediction Chart** - Displays results from the actual model calculations

## API Configuration

By default, the UI connects to `http://localhost:5001`. 

To use a different API URL, create a `.env` file in `az_ui_demo`:

```bash
VITE_API_URL=http://your-api-url:port
```

Then restart the dev server.

## Troubleshooting

- **"Failed to load external data"** - Make sure the API server is running on port 5001
- **CORS errors** - The API has CORS enabled, but if you see errors, check that the API server is running
- **Connection refused** - Verify the API server is running: `python api.py` in the `az_model` directory

