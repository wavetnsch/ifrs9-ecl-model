# IFRS 9 Expected Credit Loss (ECL) Model

An end-to-end implementation of the IFRS 9 Expected Credit Loss (ECL) framework built with Python, applied to the **Lending Club 2007–2020 Q3** dataset (2.9 million loans). Designed to reflect real-world practices at commercial and development banks.

**Author:** Thanitsak Chuwittraimeta

---

## Overview

IFRS 9 (effective 1 January 2018) replaced the incurred loss model (IAS 39) with a forward-looking **expected credit loss** model. This project implements the full ECL pipeline in a single self-contained notebook:

| Component | Approach |
|-----------|----------|
| **Stage Classification** | SICR-based (DPD + grade + DTI) |
| **PD** | Logistic Regression with PIT macro overlay (FRED API) |
| **Lifetime PD** | Vintage survival analysis |
| **LGD** | Recovery-based, segment-level |
| **EAD** | Annuity amortisation formula |
| **ECL** | PD × LGD × EAD, probability-weighted across 3 scenarios |

$$ECL = PD \times LGD \times EAD$$

---

## Dataset

**Lending Club 2007–2020 Q3** — real peer-to-peer personal loan data (2.9M loans, 142 columns)

The notebook auto-detects the largest `.gzip` or `.csv` file in `data/`, so it works regardless of filename changes.

> Available on Kaggle: `imsparsh/lending-club-loan-dataset-2007-2020`

---

## IFRS 9 Stage Classification (SICR Logic)

| Stage | Condition | ECL Horizon |
|-------|-----------|-------------|
| **Stage 1** | Performing — no SICR | 12-month ECL |
| **Stage 2** | SICR: DPD 31–120 days, Grade D–G (non-fully-paid), or DTI > 35% | Lifetime ECL |
| **Stage 3** | Credit-impaired: DPD 120+, Default, or Charged Off | Lifetime ECL |

---

## Methodology

### PD Model — Point-in-Time Logistic Regression

Trained on origination-time features only (zero lookahead bias):
- Borrower features: FICO score, DTI, interest rate, annual income, revolving utilisation, open accounts, prior delinquencies
- Macro features: GDP growth, unemployment rate, Treasury yield (via FRED API)

**AUC ~0.70 | KS > 0.30** — reasonable for origination-only features without behavioural data.

### Lifetime PD — Vintage Survival Analysis

Cumulative default rates by origination cohort and grade. Captures the seasoning effect (hazard peaks at 12–24 months, then declines as survivors demonstrate payment discipline).

### Probability-Weighted Scenarios (IFRS 9 §5.5.17)

| Scenario | PD Multiplier | Weight |
|----------|--------------|--------|
| Base     | ×1.0         | 40%    |
| Adverse  | ×1.5         | 40%    |
| Severe   | ×2.0         | 20%    |

---

## Project Structure

```
ifrs9-ecl-model/
├── ifrs9_ecl_model_api.ipynb   ← main notebook (all sections)
├── data/                        ← place dataset here (not tracked)
├── plots/                       ← generated visualisations (not tracked)
└── requirements.txt
```

---

## Getting Started

```bash
git clone https://github.com/wavetnsch/ifrs9-ecl-model.git
cd ifrs9-ecl-model

pip install -r requirements.txt

# Download dataset from Kaggle
pip install kaggle
# Place kaggle.json at ~/.kaggle/kaggle.json first
kaggle datasets download -d imsparsh/lending-club-loan-dataset-2007-2020 -p data/

# Open the notebook
jupyter notebook ifrs9_ecl_model_api.ipynb
```

**Optional:** Set `FRED_API_KEY` in a `.env` file for macro data via the FRED API. The notebook falls back to public CSV endpoints if no key is provided.

---

## References

- IASB (2014). *IFRS 9 Financial Instruments*. International Accounting Standards Board.
- Bank of Thailand (2020). *Guideline on IFRS 9 Implementation for Financial Institutions*.
- BIS (2017). *Basel III: Finalising Post-Crisis Reforms*. Bank for International Settlements.
- Schuermann, T. (2004). *What Do We Know About Loss Given Default?* Federal Reserve Bank of New York.
