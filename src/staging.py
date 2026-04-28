import numpy as np
import pandas as pd


STAGE_LABELS = {
    1: "Stage 1 — Performing (12-month ECL)",
    2: "Stage 2 — Underperforming (Lifetime ECL)",
    3: "Stage 3 — Credit-impaired (Lifetime ECL)",
}

# Significant Increase in Credit Risk (SICR) thresholds
RATING_DETERIORATION_NOTCHES = 2
DPD_STAGE2_THRESHOLD = 30
DPD_STAGE3_THRESHOLD = 90


def assign_stage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign IFRS 9 stages based on Significant Increase in Credit Risk (SICR).

    Stage 3: Objective evidence of credit impairment (DPD ≥ 90 or default)
    Stage 2: SICR since origination but not yet impaired
    Stage 1: No significant deterioration — 12-month ECL applies
    """
    df = df.copy()

    rating_deterioration = df["credit_rating_curr"] - df["credit_rating_orig"]

    is_stage3 = (
        (df["is_default"] == 1)
        | (df["days_past_due"] >= DPD_STAGE3_THRESHOLD)
        | (df["credit_rating_curr"] >= 8)
    )

    is_stage2 = ~is_stage3 & (
        (df["days_past_due"] >= DPD_STAGE2_THRESHOLD)
        | (rating_deterioration >= RATING_DETERIORATION_NOTCHES)
        | (df["loan_to_value"] > 1.5)
    )

    df["stage"] = np.where(is_stage3, 3, np.where(is_stage2, 2, 1))
    df["ecl_horizon"] = np.where(df["stage"] == 1, "12-Month", "Lifetime")
    df["stage_label"] = df["stage"].map(STAGE_LABELS)

    return df


def stage_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Portfolio breakdown by IFRS 9 stage."""
    total_balance = df["outstanding_balance"].sum()
    total_count = len(df)

    summary = (
        df.groupby("stage")
        .agg(
            n_loans=("loan_id", "count"),
            outstanding_balance=("outstanding_balance", "sum"),
            avg_dpd=("days_past_due", "mean"),
            avg_ltv=("loan_to_value", "mean"),
            avg_rating=("credit_rating_curr", "mean"),
        )
        .assign(
            pct_count=lambda x: (x["n_loans"] / total_count * 100).round(1),
            pct_balance=lambda x: (x["outstanding_balance"] / total_balance * 100).round(1),
            stage_label=lambda x: x.index.map(STAGE_LABELS),
        )
        .round({"avg_dpd": 1, "avg_ltv": 3, "avg_rating": 2})
    )
    return summary
