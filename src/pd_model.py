import numpy as np
import pandas as pd


# Through-the-Cycle (TTC) annual PD by internal rating grade (1=AAA … 8=Default)
TTC_ANNUAL_PD = {1: 0.001, 2: 0.002, 3: 0.005, 4: 0.010,
                 5: 0.025, 6: 0.070, 7: 0.200, 8: 1.000}

# Annual survival probability by rating
ANNUAL_SURVIVAL = {r: 1 - pd for r, pd in TTC_ANNUAL_PD.items()}


class PDModel:
    """
    Probability of Default (PD) model for IFRS 9 ECL calculation.

    Supports:
    - 12-month PD  → Stage 1 loans
    - Lifetime PD  → Stage 2 & 3 loans (survival-function approach)
    - Macro overlay via a simple scalar multiplier
    """

    def __init__(self, macro_scalar: float = 1.0):
        """
        macro_scalar: macroeconomic multiplier applied to base PD.
            0.7 = benign scenario
            1.0 = base scenario
            1.8 = adverse scenario
        """
        self.macro_scalar = macro_scalar

    def compute_12m_pd(self, df: pd.DataFrame) -> pd.Series:
        """Point-in-Time 12-month PD with macro overlay."""
        pd_12m = df["credit_rating_curr"].map(TTC_ANNUAL_PD).fillna(1.0)
        return (pd_12m * self.macro_scalar).clip(0, 1.0)

    def compute_lifetime_pd(self, df: pd.DataFrame) -> pd.Series:
        """
        Lifetime PD via survival approach.
        LifetimePD = 1 − (1 − annual_PD_adj)^remaining_years
        """
        remaining_years = (df["remaining_term_months"] / 12).clip(lower=0)
        annual_pd = df["credit_rating_curr"].map(TTC_ANNUAL_PD).fillna(1.0)
        annual_pd_adj = (annual_pd * self.macro_scalar).clip(0, 1.0)
        annual_survival_adj = 1 - annual_pd_adj
        return (1 - annual_survival_adj ** remaining_years).clip(0, 1.0)

    def assign_pd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assign PD to each loan based on its IFRS 9 stage."""
        df = df.copy()
        df["pd_12m"] = self.compute_12m_pd(df).round(6)
        df["pd_lifetime"] = self.compute_lifetime_pd(df).round(6)
        df["pd_applied"] = np.where(df["stage"] == 1, df["pd_12m"], df["pd_lifetime"])
        df.loc[df["stage"] == 3, "pd_applied"] = 1.0  # already defaulted
        return df

    def pd_term_structure(self, rating: int, max_years: int = 10) -> pd.DataFrame:
        """Marginal and cumulative PD term structure for a given rating grade."""
        annual_pd = min(TTC_ANNUAL_PD[rating] * self.macro_scalar, 1.0)
        s = 1 - annual_pd
        rows, cum_surv = [], 1.0
        for t in range(1, max_years + 1):
            marginal = cum_surv * annual_pd
            cum_surv *= s
            rows.append({"year": t, "marginal_pd": marginal,
                         "cumulative_pd": 1 - cum_surv})
        return pd.DataFrame(rows)
