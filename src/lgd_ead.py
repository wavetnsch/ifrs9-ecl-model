import numpy as np
import pandas as pd


# Credit Conversion Factor (CCF) by product — Basel III reference values
CCF_BY_PRODUCT = {
    "Term Loan":       1.00,
    "Revolving Credit": 0.75,
    "Letter of Credit": 0.50,
    "Trade Finance":   0.40,
    "Mortgage":        1.00,
}

# Unsecured LGD baseline by product (senior unsecured, pre-collateral adjustment)
BASE_LGD = {
    "Term Loan":       0.45,
    "Revolving Credit": 0.65,
    "Letter of Credit": 0.55,
    "Trade Finance":   0.35,
    "Mortgage":        0.25,
}


def compute_ead(df: pd.DataFrame) -> pd.Series:
    """
    Exposure at Default (EAD).
    EAD = Outstanding Balance + Undrawn Commitment × CCF
    """
    ccf = df["product_type"].map(CCF_BY_PRODUCT).fillna(1.0)
    return (df["outstanding_balance"] + df["undrawn_commitment"] * ccf).round(2)


def compute_lgd(df: pd.DataFrame, collateral_haircut: float = 0.20) -> pd.Series:
    """
    Loss Given Default (LGD) with collateral adjustment.

    LGD = max(0, EAD − Collateral × (1 − haircut)) / EAD

    A 20% haircut on collateral accounts for liquidation costs and time value.
    Final LGD blends collateral-based estimate (70%) with product-based floor (30%).
    """
    base_lgd = df["product_type"].map(BASE_LGD).fillna(0.45)
    ead = compute_ead(df)
    net_collateral = df["collateral_value"] * (1 - collateral_haircut)
    lgd_collateral = ((ead - net_collateral) / ead.clip(lower=1)).clip(0, 1)
    lgd = (0.70 * lgd_collateral + 0.30 * base_lgd).clip(0, 1)
    return lgd.round(4)


def lgd_ead_summary(df: pd.DataFrame) -> pd.DataFrame:
    """EAD and LGD summary by product type."""
    return (
        df.groupby("product_type")
        .agg(
            n_loans=("loan_id", "count"),
            total_ead=("ead", "sum"),
            avg_lgd=("lgd", "mean"),
            avg_ltv=("loan_to_value", "mean"),
        )
        .assign(
            pct_ead=lambda x: (x["total_ead"] / x["total_ead"].sum() * 100).round(1),
            avg_lgd=lambda x: x["avg_lgd"].round(4),
            avg_ltv=lambda x: x["avg_ltv"].round(3),
        )
        .sort_values("total_ead", ascending=False)
    )
