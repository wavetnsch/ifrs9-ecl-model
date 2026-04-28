# IFRS 9 Expected Credit Loss (ECL) Model

An end-to-end implementation of the IFRS 9 Expected Credit Loss (ECL) framework for a synthetic loan portfolio, built with Python. Designed to reflect real-world practices at commercial and development banks.

## Overview

IFRS 9 (effective 1 January 2018) replaced the incurred loss model (IAS 39) with a forward-looking **expected credit loss** model. This project implements all three ECL components:

| Component | Description |
|-----------|-------------|
| **PD** | Probability of Default — 12-month and lifetime |
| **LGD** | Loss Given Default — collateral-adjusted |
| **EAD** | Exposure at Default — outstanding + undrawn × CCF |

$$ECL = PD \times LGD \times EAD \times \text{Discount Factor}$$

## IFRS 9 Stage Classification

| Stage | Condition | ECL Horizon |
|-------|-----------|-------------|
| **Stage 1** | No significant increase in credit risk (SICR) | 12-month ECL |
| **Stage 2** | SICR since origination (DPD ≥ 30, rating ↓ 2+ notches, LTV > 150%) | Lifetime ECL |
| **Stage 3** | Credit-impaired (DPD ≥ 90, default) | Lifetime ECL |

## Methodology

### PD Model — Survival Approach
$$\text{Lifetime PD} = 1 - (1 - \text{Annual PD}_{\text{adj}})^{\text{Remaining Years}}$$

With macroeconomic overlay:
$$\text{PD}_{\text{PiT}} = \text{PD}_{\text{TTC}} \times \text{Macro Scalar}$$

### Probability-Weighted Scenarios (IFRS 9.B5.5.41)

| Scenario | Macro Scalar | Weight |
|----------|-------------|--------|
| Benign   | ×0.70       | 30%    |
| Base     | ×1.00       | 50%    |
| Adverse  | ×1.80       | 20%    |

$$ECL_{\text{weighted}} = 0.30 \times ECL_{\text{benign}} + 0.50 \times ECL_{\text{base}} + 0.20 \times ECL_{\text{adverse}}$$

### LGD — Collateral Adjustment
$$LGD = \frac{\max(0,\ EAD - \text{Collateral} \times (1 - \text{Haircut}))}{EAD}$$

A 20% haircut accounts for collateral liquidation costs and time value.

### EAD — Credit Conversion Factor (CCF)
$$EAD = \text{Outstanding Balance} + \text{Undrawn Commitment} \times CCF$$

| Product | CCF |
|---------|-----|
| Term Loan | 100% |
| Revolving Credit | 75% |
| Letter of Credit | 50% |
| Trade Finance | 40% |
| Mortgage | 100% |

## Project Structure

```
ifrs9-ecl-model/
├── src/
│   ├── data_generator.py   # Synthetic loan portfolio generation
│   ├── staging.py          # IFRS 9 stage assignment (SICR logic)
│   ├── pd_model.py         # PD model (12-month & lifetime, macro overlay)
│   ├── lgd_ead.py          # LGD and EAD calculation
│   └── ecl_calculator.py   # ECL aggregation, scenarios, sensitivity
├── notebooks/
│   ├── 01_portfolio_overview.ipynb
│   ├── 02_pd_model.ipynb
│   ├── 03_lgd_ead_model.ipynb
│   ├── 04_ecl_calculation.ipynb
│   └── 05_sensitivity_analysis.ipynb
├── plots/                  # Generated visualizations
├── data/                   # Data directory (populated at runtime)
└── requirements.txt
```

## Getting Started

```bash
# Clone the repository
git clone https://github.com/wavetnsch/ifrs9-ecl-model.git
cd ifrs9-ecl-model

# Install dependencies
pip install -r requirements.txt

# Run notebooks in order
jupyter notebook notebooks/
```

## Key Results (Synthetic Portfolio, n = 5,000 loans)

| Metric | Value |
|--------|-------|
| Total EAD | ~THB 2.5B |
| Stage 1 (%) | ~68% of balance |
| Stage 2 (%) | ~22% of balance |
| Stage 3 (%) | ~10% of balance |
| Base ECL | ~THB 85M |
| Coverage Ratio | ~3.4% |
| Adverse Scenario ECL | ~+60% vs base |

## Sensitivity Analysis

The model supports:
- **PD shocks** (−50% to +100%)
- **LGD shocks** (−20% to +20%)
- **Combined stress scenarios** (Mild / Moderate / Severe / Extreme)
- **Stage migration simulation** (Stage 1 → 2, Stage 2 → 3)

## Technical Stack

- **Python 3.10+**
- **pandas / numpy** — data manipulation and numerical computation
- **scikit-learn** — preprocessing utilities
- **matplotlib / seaborn** — visualization

## References

- IASB (2014). *IFRS 9 Financial Instruments*. International Accounting Standards Board.
- Bank of Thailand (2020). *Guideline on IFRS 9 Implementation for Financial Institutions*.
- BIS (2017). *Basel III: Finalising Post-Crisis Reforms*. Bank for International Settlements.
- Schuermann, T. (2004). *What Do We Know About Loss Given Default?* Federal Reserve Bank of New York.
