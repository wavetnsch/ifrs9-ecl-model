# IFRS 9 Expected Credit Loss (ECL) Model

An end-to-end implementation of the IFRS 9 Expected Credit Loss (ECL) framework built with Python, applied to the **Lending Club 2007–2011** loan dataset. Designed to reflect real-world practices at commercial and development banks.

## Overview

IFRS 9 (effective 1 January 2018) replaced the incurred loss model (IAS 39) with a forward-looking **expected credit loss** model. This project implements all three ECL components:

| Component | Description |
|-----------|-------------|
| **PD** | Probability of Default — 12-month and lifetime |
| **LGD** | Loss Given Default — product-based with unsecured baseline |
| **EAD** | Exposure at Default — outstanding + undrawn × CCF |

$$ECL = PD \times LGD \times EAD \times \text{Discount Factor}$$

## Dataset

**Lending Club 2007–2011** — real peer-to-peer personal loan data

| Field | Source | Notes |
|-------|--------|-------|
| Outstanding balance | `out_prncp` | Remaining principal |
| Credit rating | `grade` (A–G → 1–7) | Origination rating |
| Default flag | `loan_status` | Charged Off = default |
| Days past due | `mths_since_last_delinq` | Proxy: 0 / 30 / 60 / 120 days |
| Product type | `purpose` | Mapped to Term Loan / Revolving / Mortgage / Trade Finance |
| Sector | `purpose` | Mapped to Financial / Real Estate / Trading / Services / Manufacturing |

> **Note:** Lending Club loans are unsecured. Collateral value is set to 0 and the LTV-based SICR criterion is disabled. Staging is driven by DPD and credit rating changes only.

## IFRS 9 Stage Classification

| Stage | Condition | ECL Horizon |
|-------|-----------|-------------|
| **Stage 1** | No significant increase in credit risk (SICR) | 12-month ECL |
| **Stage 2** | SICR since origination (DPD ≥ 30 or rating ↓ 2+ notches) | Lifetime ECL |
| **Stage 3** | Credit-impaired (DPD ≥ 90 or default) | Lifetime ECL |

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

### LGD — Product-Based Unsecured Baseline
$$LGD = 0.70 \times LGD_{\text{collateral}} + 0.30 \times LGD_{\text{base}}$$

For unsecured loans, `collateral = 0`, so LGD approaches the product-based floor (45% for Term Loans).

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
│   ├── data_loader.py      # Lending Club data loading and IFRS 9 field mapping
│   ├── data_generator.py   # Synthetic portfolio (fallback / unit testing)
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
├── data/                   # Data directory (add dataset here — see below)
└── requirements.txt
```

## Getting Started

```bash
# Clone the repository
git clone https://github.com/wavetnsch/ifrs9-ecl-model.git
cd ifrs9-ecl-model

# Install dependencies
pip install -r requirements.txt

# Download dataset from Kaggle
pip install kaggle
# Place kaggle.json at ~/.kaggle/kaggle.json first
kaggle datasets download -d imsparsh/lending-club-loan-dataset-2007-2011 -p data/
unzip data/lending-club-loan-dataset-2007-2011.zip -d data/

# Run notebooks in order
jupyter notebook notebooks/
```

## Key Results (Lending Club 2007–2011, n = 39,717 loans)

| Metric | Value |
|--------|-------|
| Total Portfolio (USD) | ~$418M |
| Default Rate | 14.2% |
| Stage 1 (% of balance) | ~80% |
| Stage 2 (% of balance) | ~4% |
| Stage 3 (% of balance) | ~16% |
| Base ECL | run notebooks |
| Adverse Scenario ECL | run notebooks |

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
