import numpy as np
import pandas as pd
from datetime import date, timedelta


def generate_loan_portfolio(
    n_loans: int = 5000,
    reporting_date: date = date(2024, 12, 31),
    random_state: int = 42,
) -> pd.DataFrame:
    """Generate synthetic loan portfolio for IFRS 9 ECL modeling."""
    rng = np.random.default_rng(random_state)

    days_since_orig = rng.integers(30, 1825, n_loans)
    origination_dates = [reporting_date - timedelta(days=int(d)) for d in days_since_orig]

    loan_term_months = rng.choice(
        [12, 24, 36, 48, 60, 84, 120], n_loans,
        p=[0.05, 0.10, 0.25, 0.20, 0.20, 0.10, 0.10],
    )
    maturity_dates = [
        orig + timedelta(days=int(t * 30.5))
        for orig, t in zip(origination_dates, loan_term_months)
    ]
    remaining_months = np.array([
        max(0.0, (mat - reporting_date).days / 30.5)
        for mat in maturity_dates
    ])

    outstanding_balance = rng.lognormal(np.log(500_000), 0.9, n_loans).clip(10_000, 10_000_000)
    original_balance = outstanding_balance * rng.uniform(1.0, 2.0, n_loans)

    credit_rating_orig = rng.choice([1, 2, 3, 4, 5, 6, 7], n_loans,
                                     p=[0.05, 0.10, 0.20, 0.30, 0.20, 0.10, 0.05])
    rating_change = rng.integers(-1, 4, n_loans)
    credit_rating_curr = (credit_rating_orig + rating_change).clip(1, 8)

    dpd_base = rng.choice(
        [0, 0, 0, 0, 0, 0, 30, 60, 90, 120, 180], n_loans,
        p=[0.50, 0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.03, 0.03, 0.02, 0.02],
    )
    dpd = (dpd_base + rng.integers(-5, 10, n_loans)).clip(0, 365)

    collateral_value = outstanding_balance * rng.uniform(0.3, 2.5, n_loans)
    loan_to_value = (outstanding_balance / collateral_value.clip(1)).round(4)

    product_type = rng.choice(
        ["Term Loan", "Revolving Credit", "Letter of Credit", "Trade Finance", "Mortgage"],
        n_loans, p=[0.35, 0.20, 0.15, 0.20, 0.10],
    )
    sector = rng.choice(
        ["Manufacturing", "Trading", "Services", "Agriculture", "Real Estate", "Financial"],
        n_loans, p=[0.25, 0.20, 0.20, 0.10, 0.15, 0.10],
    )

    default_prob = (
        0.01
        + 0.03 * (credit_rating_curr - 3).clip(0, 5) / 5
        + 0.20 * (dpd > 90).astype(float)
        + 0.05 * (loan_to_value > 1.2).astype(float)
    ).clip(0, 1)

    is_default = (rng.uniform(0, 1, n_loans) < default_prob).astype(int)
    dpd = np.where(is_default == 1, dpd.clip(90, 365), dpd)

    undrawn_commitment = np.where(
        np.isin(product_type, ["Revolving Credit", "Letter of Credit"]),
        outstanding_balance * rng.uniform(0, 1.5, n_loans),
        0.0,
    )

    return pd.DataFrame({
        "loan_id": [f"LOAN{i:05d}" for i in range(n_loans)],
        "origination_date": origination_dates,
        "maturity_date": maturity_dates,
        "reporting_date": reporting_date,
        "product_type": product_type,
        "sector": sector,
        "outstanding_balance": outstanding_balance.round(2),
        "original_balance": original_balance.round(2),
        "undrawn_commitment": undrawn_commitment.round(2),
        "collateral_value": collateral_value.round(2),
        "loan_to_value": loan_to_value,
        "credit_rating_orig": credit_rating_orig,
        "credit_rating_curr": credit_rating_curr,
        "days_past_due": dpd,
        "is_default": is_default,
        "remaining_term_months": remaining_months.round(1),
        "loan_term_months": loan_term_months,
    })
