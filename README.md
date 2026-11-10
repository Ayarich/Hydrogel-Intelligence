
# Hydrogel Intelligence

### Machine Learning-Guided Prediction and Active-Learning Optimization of GelMA Hydrogel Mechanical Properties

**Researcher:** Ebenezer Ayaaba  
**Research Areas:** Materials Informatics, Polymer Mechanics, Machine Learning, Active Learning

## Research Overview

Hydrogel Intelligence is an independent computational materials research project investigating how machine learning can predict the mechanical properties of gelatin methacryloyl (GelMA) hydrogels and guide experimental formulation selection.

The project combines experimental compression-data analysis, mechanical-property extraction, regression modeling, Gaussian Process Regression, and retrospective active-learning simulations.

## Research Objectives

1. Reproduce Young's modulus values from published hydrogel compression measurements.
2. Examine relationships between GelMA concentration, curing time, and compressive stiffness.
3. Develop and evaluate predictive models for hydrogel mechanical properties.
4. Compare machine-learning-guided experiment selection with random and greedy strategies.

## Dataset

- 12 GelMA formulation conditions
- 144 reported specimen measurements
- Concentrations: 10%, 15%, and 20%
- Curing times: 30, 60, 90, and 120 seconds

The experimental data originate from the publicly available Hydrogel Characterization Data dataset.

Source: https://doi.org/10.17632/cx8cfgrhnn.1

The original dataset is attributed to its creators and should not be described as independently generated experimental data.

## Key Research Results

| Metric | Result |
|---|---|
| Modulus calculations reproduced within 0.01 kPa | 140/144 |
| Best point-prediction model | Log-target Quadratic Ridge |
| Leave-one-formulation-out R² | 0.950 |
| Leave-one-formulation-out RMSE | 13.330 kPa |
| Best observed formulation | 20% GelMA, 90 seconds |
| Highest observed mean modulus | 193.382 kPa |
| Best retrospective selection policy | GPR-UCB |
| Mean total experiments, GPR-UCB | 4.976 |
| Mean total experiments, random selection | 8.000 |

The active-learning benchmark showed approximately 37.8% fewer total formulation evaluations under the GPR-UCB policy than under random selection.

These are exploratory, retrospective results obtained from a small fixed experimental design. The model has not yet undergone prospective laboratory validation.

## Methodology

### Mechanical Characterization

Stress-strain measurements were processed to reproduce the original reported Young's modulus values.

The analysis investigated:

- Linear regression with and without an intercept
- Strain-window sensitivity
- Nonlinear mechanical behavior
- Specimen-level reproducibility

### Predictive Modeling

Regression models were evaluated using leave-one-formulation-out cross-validation.

Methods included linear regression, polynomial Ridge regression, log-transformed targets, and Gaussian Process Regression.

### Active Learning

A Gaussian Process Upper Confidence Bound (GPR-UCB) acquisition policy was evaluated in a retrospective search benchmark against greedy, uncertainty-only, and random selection.

## Limitations

- Only 12 unique formulation conditions were available.
- Model development and comparison used the same historical dataset.
- Experimental batch independence requires further verification.
- Four modulus calculations retain discrepancies with reported values.
- The active-learning results have not been prospectively validated.

## Future Research

Future work will investigate independent experimental validation, multi-property optimization, improved uncertainty calibration, and data-driven polymer formulation design.

## Author

**Ebenezer Ayaaba**  
Materials Engineering | Systems & Data Engineering  
Portfolio: https://ebenezerayaaba.vercel.app/

## Data Attribution

Original experimental dataset:
https://doi.org/10.17632/cx8cfgrhnn.1

Please cite the original dataset creators when using their experimental measurements.
