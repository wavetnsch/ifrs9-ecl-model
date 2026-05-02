import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date

DATA_PATH = Path(__file__).parent.parent / "data" / "loan.csv"

GRADE_MAP = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}

PURPOSE_TO_PRODUCT = {
    "credit_card":       "Revolving Credit",
    "home_improvement":  "Mortgage",
    "house":             "Mortgage",
    "small_business":    "Trade Finance",
    "debt_consolidation":"Term Loan",
    "medical":           "Term Loan",
    "major_purchase":    "Term Loan",
    "car":               "Term Loan",
    "moving":            "Term Loan",
    "vacation":          "Term Loan",
    "wedding":           "Term Loan",
    "educational":       "Term Loan",
    "renewable_energy":  "Term Loan",
    "other":             "Term Loan",
}

PURPOSE_TO_SECTOR = {
    "credit_card":       "Financial",
    "debt_consolidation":"Financial",
    "home_improvement":  "Real Estate",
    "house":             "Real Estate",
    "small_business":    "Trading",
    "major_purchase":    "Manufacturing",
    "car":               "Manufacturing",
    "medical":           "Services",
    "moving":            "Services",
    "vacation":          "Services",
    "wedding":           "Services",
    "educational":       "Services",
    "renewable_energy":  "Services",
    "other":             "Services",
}


def load_loan_portfolio(
    path: str = None,
    reporting_date: date = None,
) -> pd.DataFrame:
    """Load Lending Club (2007-2011) and reshape into IFRS 9 portfolio format."""
    if path is None:
        path = DATA_PATH

    raw = pd.read_csv(path, low_memory=False)
    raw = raw[raw["loan_status"].isin(["Fully Paid", "Charged Off", "Current"])].copy()

    # Dates
    raw["issue_d"] = pd.to_datetime(raw["issue_d"], format="%b-%y")
    raw["term_months"] = raw["term"].str.extract(r"(\d+)").astype(int)
    raw["maturity_date"] = raw["issue_d"] + pd.to_timedelta(raw["term_months"] * 30.5, unit="D")

    if reporting_date is None:
        reporting_date = raw["issue_d"].max().date()
    reporting_ts = pd.Timestamp(reporting_date)

    # Balances
    # out_prncp = 0 for closed loans → use funded_amnt as proxy for snapshot balance
    outstanding = raw["out_prncp"].where(raw["out_prncp"] > 0, raw["funded_amnt"])
    original = raw["loan_amnt"]

    # Default
    is_default = (raw["loan_status"] == "Charged Off").astype(int)

    # Credit rating: grade A=1 … G=7, default to D=4 if missing
    rating_orig = raw["grade"].map(GRADE_MAP).fillna(4).astype(int)

    # Proxy current rating: deteriorate +2 notches if recently delinquent or defaulted
    rating_curr = rating_orig.copy()
    recently_delinq = raw["mths_since_last_delinq"].fillna(999) < 12
    rating_curr[recently_delinq] = (rating_orig[recently_delinq] + 2).clip(upper=8)
    rating_curr[is_default == 1] = 8

    # Days past due proxy
    dpd = pd.Series(0, index=raw.index)
    dpd[is_default == 1] = 120
    dpd[(raw["mths_since_last_delinq"].fillna(999) < 3) & (is_default == 0)] = 60
    dpd[
        (raw["mths_since_last_delinq"].fillna(999) >= 3) &
        (raw["mths_since_last_delinq"].fillna(999) < 12) &
        (is_default == 0)
    ] = 30

    # Remaining term
    remaining_months = (
        (raw["maturity_date"] - reporting_ts).dt.days / 30.5
    ).clip(lower=0).round(1)

    # LTV: unsecured loans — set to 0 so LTV criterion doesn't trigger SICR
    collateral_value = pd.Series(0.0, index=raw.index)
    loan_to_value = pd.Series(0.0, index=raw.index)

    # Product type and sector
    product_type = raw["purpose"].map(PURPOSE_TO_PRODUCT).fillna("Term Loan")
    sector = raw["purpose"].map(PURPOSE_TO_SECTOR).fillna("Services")

    df = pd.DataFrame({
        "loan_id":              raw["id"].astype(str).values,
        "origination_date":     raw["issue_d"].dt.date.values,
        "maturity_date":        raw["maturity_date"].dt.date.values,
        "reporting_date":       reporting_date,
        "product_type":         product_type.values,
        "sector":               sector.values,
        "outstanding_balance":  outstanding.round(2).values,
        "original_balance":     original.round(2).values,
        "undrawn_commitment":   0.0,
        "collateral_value":     collateral_value.values,
        "loan_to_value":        loan_to_value.values,
        "credit_rating_orig":   rating_orig.values,
        "credit_rating_curr":   rating_curr.values,
        "days_past_due":        dpd.values,
        "is_default":           is_default.values,
        "remaining_term_months": remaining_months.values,
        "loan_term_months":     raw["term_months"].values,
    })

    return df.reset_index(drop=True)
