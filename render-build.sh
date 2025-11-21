#!/usr/bin/env bash
set -euo pipefail

echo "==> Preparing az_model data inputs"
cd az_model

python download_labor.py
python download_capital.py
python download_materials.py
python download_energy.py
python compute_percentages.py

echo "==> Data pipeline complete"
