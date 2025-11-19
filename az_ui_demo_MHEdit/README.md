# AstraZeneca Procurement Model UI

A modern web interface for AstraZeneca procurement managers to visualize and configure the biological resin process procurement model.

## Features

- **Cost Input Management**: Manual entry or external data source integration for 4 input factors (Labor, Capital, Materials, Energy)
- **Coefficient Editor**: Adjustable coefficients for the Cobb-Douglas/regression model across multiple time periods
- **Price Prediction Visualization**: Normal distribution chart showing predicted price change ranges with confidence intervals
- **Modern UI**: Clean, professional interface built with React, TypeScript, and Tailwind CSS

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

## Integration Points

The following functions are marked with TODO comments and should be connected to the backend:

1. **`calculatePrediction`** in `src/App.tsx`: Connect to the actual algorithm for price prediction
2. **`loadExternalData`** in `src/App.tsx`: Connect to external data sources for automatic cost input loading

## Project Structure

```
src/
├── components/
│   ├── CostInputs.tsx          # Input form for cost percentages
│   ├── CoefficientEditor.tsx   # Coefficient editing interface
│   └── NormalDistributionChart.tsx  # Price prediction visualization
├── types.ts                    # TypeScript type definitions
├── App.tsx                     # Main application component
└── main.tsx                    # Application entry point
```

## Default Coefficients

The model uses default coefficients based on the time-series regression structure:
- Current period (t): Labor (0.14), Capital (0.07), Materials (0.07), Energy (0.04)
- One period lag (t-1): Labor (0.07), Capital (0.07), Materials (0.07), Energy (0.08)
- Two period lag (t-2): Labor (-0.05), Capital (-0.01), Materials (-0.04), Energy (-0.08)
- Three period lag (t-3): Labor (-0.06), Capital (0.11), Materials (-0.04), Energy (-0.08)

