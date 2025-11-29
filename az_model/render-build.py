#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AZ_MODEL = ROOT / "az_model"

scripts = [
    "download_labor.py",
    "download_capital.py",
    "download_materials.py",
    "download_energy.py",
    "compute_percentages.py",
]

for script in scripts:
    print(f"==> Running {script}")
    subprocess.run([sys.executable, script], cwd=AZ_MODEL, check=True)

print("==> Data pipeline complete")
