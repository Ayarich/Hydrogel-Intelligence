# Reproducing the Hydrogel Intelligence analyses

## Scope and source
This repository contains an independent *computational reanalysis* of experimental GelMA hydrogel compression measurements from the [Hydrogel Characterization Data dataset](https://doi.org/10.17632/cx8cfgrhnn.1). It does not represent newly performed laboratory tests.

The source-reported measurements are primary for the modeling results. A separate strain-window reproduction audit should be documented alongside the original instrument-export calculations. **140/144** reported modulus values were matched within 0.01 kPa, with **four discrepancies retained**.

## Setup (Windows PowerShell, from the repository root)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Input choices

The modeling script `src/reproduce.py` reconstructs the authoritative formulation-level source table from `data/raw/GelMA_Characterization_Data.xlsx`. If the source workbook currently lives in the repository root, copy it into `data/raw`:

```powershell
New-Item -ItemType Directory -Force data\raw | Out-Null
Copy-Item .\GelMA_Characterization_Data.xlsx .\data\raw\GelMA_Characterization_Data.xlsx
```

The script rebuilds `data/processed/gelma_source_specimens.csv`, `gelma_source_formulations.csv`, `source_model_metrics.csv`, and `source_loocv_predictions.csv`. It also calculates a **fresh retrospective** active-learning benchmark and writes the corresponding tables under `data/processed`. It does **not** use the separate specimen-level derived modulus table as the ML target.

## Run

```powershell
python src/reproduce.py
python src/figures.py
```

All plots are saved as publication-resolution PNG and vector PDF in `reports/figures/`. The plotting script reads **actual saved CSV results**, not embedded results or placeholders.

### Figures
- `01_formulation_stiffness`: source-reported mean modulus versus curing time (SD where present)
- `02_formulation_heatmap`: modulus as concentration × curing-time matrix
- `03_loocv_predictions`: observed versus held-out predicted stiffness
- `04_active_learning_benchmark`: mean experiment counts from the historical benchmark summary

## Interpretation limits
- 144 specimens contribute to only 12 distinct formulation conditions. Cross-validation must be **formulation-level**, not random specimen-level.
- LOOCV performance is **exploratory** because model development occurred on this same small dataset, even though each individual prediction is out of fold.
- The active-learning benchmark locates the **best already-measured condition** using a fixed historical candidate grid; it does not validate future experiments, optimize untested concentrations, or prove a global optimum.
- Standard deviations across specimens are not evidence of independent manufacture batches.
- The acquisition metric is **total evaluations including three initial observations**; the 37.8% reduction is relative to a random-search expected total of eight.
- Confirm original dataset attribution, license conditions, and any redistribution terms before public reuse.

## Quick verification

```powershell
python -c "import pandas as pd; d=pd.read_csv('data/processed/gelma_source_formulations.csv'); print(len(d), d['mean_modulus_kPa'].max())"
```
Expected number of formulation rows: **12**. The highest source-reported mean modulus is approximately **193.382 kPa** for 20% GelMA, 90 s.
