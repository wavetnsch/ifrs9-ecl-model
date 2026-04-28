import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List


SCENARIO_WEIGHTS: Dict[str, float] = {"base": 0.50, "benign": 0.30, "adverse": 0.20}
MACRO_SCALARS: Dict[str, float] = {"base": 1.0, "benign": 0.70, "adverse": 1.80}


class ECLCalculator:
    """
    IFRS 9 Expected Credit Loss (ECL) calculator.

    ECL = PD × LGD × EAD × Discount Factor

    Features:
    - Probability-weighted multi-scenario ECL (base / benign / adverse)
    - Effective interest rate discounting
    - Sensitivity analysis to PD and LGD shocks
    """

    def __init__(self, discount_rate: float = 0.05):
        self.discount_rate = discount_rate

    def compute_ecl(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute scenario-weighted ECL for the portfolio."""
        df = df.copy()
        for scenario, scalar in MACRO_SCALARS.items():
            df[f"ecl_{scenario}"] = self._ecl_scenario(df, scalar)

        df["ecl"] = sum(
            df[f"ecl_{s}"] * w for s, w in SCENARIO_WEIGHTS.items()
        )
        df["coverage_ratio"] = (df["ecl"] / df["ead"].clip(lower=1)).round(4)
        return df

    def ecl_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """ECL breakdown by IFRS 9 stage."""
        return (
            df.groupby("stage")
            .agg(
                n_loans=("loan_id", "count"),
                total_ead=("ead", "sum"),
                total_ecl=("ecl", "sum"),
                avg_pd=("pd_applied", "mean"),
                avg_lgd=("lgd", "mean"),
                avg_coverage=("coverage_ratio", "mean"),
            )
            .assign(
                ecl_pct_of_ead=lambda x: (x["total_ecl"] / x["total_ead"] * 100).round(2),
                pct_of_portfolio=lambda x: (x["total_ead"] / x["total_ead"].sum() * 100).round(1),
            )
            .round({"avg_pd": 4, "avg_lgd": 4, "avg_coverage": 4})
        )

    def sensitivity_analysis(
        self,
        df: pd.DataFrame,
        pd_shocks: List[float] = [-0.50, -0.25, 0.0, 0.25, 0.50, 1.0],
        lgd_shocks: List[float] = [-0.20, -0.10, 0.0, 0.10, 0.20],
    ) -> Dict[str, pd.DataFrame]:
        """ECL sensitivity to independent PD and LGD shocks."""
        base_ecl = df["ecl"].sum()

        pd_rows = []
        for shock in pd_shocks:
            stressed_pd = (df["pd_applied"] * (1 + shock)).clip(0, 1)
            stressed_ecl = (stressed_pd * df["lgd"] * df["ead"]).sum()
            pd_rows.append({
                "pd_shock": f"{shock:+.0%}",
                "total_ecl_thb_m": round(stressed_ecl / 1e6, 2),
                "change_thb_m": round((stressed_ecl - base_ecl) / 1e6, 2),
                "pct_change": round((stressed_ecl - base_ecl) / base_ecl * 100, 2),
            })

        lgd_rows = []
        for shock in lgd_shocks:
            stressed_lgd = (df["lgd"] * (1 + shock)).clip(0, 1)
            stressed_ecl = (df["pd_applied"] * stressed_lgd * df["ead"]).sum()
            lgd_rows.append({
                "lgd_shock": f"{shock:+.0%}",
                "total_ecl_thb_m": round(stressed_ecl / 1e6, 2),
                "change_thb_m": round((stressed_ecl - base_ecl) / 1e6, 2),
                "pct_change": round((stressed_ecl - base_ecl) / base_ecl * 100, 2),
            })

        return {"pd_sensitivity": pd.DataFrame(pd_rows), "lgd_sensitivity": pd.DataFrame(lgd_rows)}

    def plot_ecl_dashboard(self, df: pd.DataFrame, figsize=(16, 10)):
        summary = self.ecl_summary(df)
        sens = self.sensitivity_analysis(df)
        stage_colors = {1: "#2196F3", 2: "#FF9800", 3: "#F44336"}
        colors = [stage_colors[s] for s in summary.index]

        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle("IFRS 9 ECL Dashboard", fontsize=14, fontweight="bold")

        stages = [f"Stage {s}" for s in summary.index]

        # EAD by stage
        axes[0, 0].bar(stages, summary["total_ead"] / 1e6, color=colors, alpha=0.85)
        axes[0, 0].set_title("EAD by Stage (THB M)")
        axes[0, 0].set_ylabel("THB Million")

        # ECL by stage
        axes[0, 1].bar(stages, summary["total_ecl"] / 1e6, color=colors, alpha=0.85)
        axes[0, 1].set_title("ECL by Stage (THB M)")
        axes[0, 1].set_ylabel("THB Million")

        # Coverage ratio
        axes[0, 2].bar(stages, summary["avg_coverage"] * 100, color=colors, alpha=0.85)
        axes[0, 2].set_title("Average Coverage Ratio (%)")
        axes[0, 2].set_ylabel("Coverage Ratio (%)")

        # Scenario ECL comparison
        scenario_ecl = {
            s: df[f"ecl_{s}"].sum() / 1e6 for s in ["benign", "base", "adverse"]
        }
        sc_colors = ["#27ae60", "#3498db", "#e74c3c"]
        axes[1, 0].bar(list(scenario_ecl.keys()), list(scenario_ecl.values()),
                       color=sc_colors, alpha=0.85)
        axes[1, 0].set_title("ECL by Macro Scenario (THB M)")
        axes[1, 0].set_ylabel("THB Million")

        # PD sensitivity
        pd_sens = sens["pd_sensitivity"]
        bar_colors = ["#e74c3c" if v > 0 else "#27ae60" for v in pd_sens["pct_change"]]
        axes[1, 1].bar(pd_sens["pd_shock"], pd_sens["pct_change"], color=bar_colors, alpha=0.85)
        axes[1, 1].axhline(0, color="black", linewidth=0.8)
        axes[1, 1].set_title("ECL Sensitivity to PD Shock (%)")
        axes[1, 1].set_ylabel("ECL Change (%)")
        axes[1, 1].set_xlabel("PD Shock")

        # LGD sensitivity
        lgd_sens = sens["lgd_sensitivity"]
        bar_colors2 = ["#e74c3c" if v > 0 else "#27ae60" for v in lgd_sens["pct_change"]]
        axes[1, 2].bar(lgd_sens["lgd_shock"], lgd_sens["pct_change"], color=bar_colors2, alpha=0.85)
        axes[1, 2].axhline(0, color="black", linewidth=0.8)
        axes[1, 2].set_title("ECL Sensitivity to LGD Shock (%)")
        axes[1, 2].set_ylabel("ECL Change (%)")
        axes[1, 2].set_xlabel("LGD Shock")

        plt.tight_layout()
        return fig

    def _ecl_scenario(self, df: pd.DataFrame, macro_scalar: float) -> pd.Series:
        pd_adj = (df["pd_applied"] * macro_scalar).clip(0, 1)
        years = (df["remaining_term_months"] / 12).clip(lower=1 / 12)
        discount = 1 / (1 + self.discount_rate) ** years
        return (pd_adj * df["lgd"] * df["ead"] * discount).round(2)
