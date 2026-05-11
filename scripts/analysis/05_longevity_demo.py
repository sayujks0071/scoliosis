"""Synthetic longevity demo: sit-to-stand frequency vs survival."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from lifelines import CoxPHFitter, KaplanMeierFitter

    HAVE_LIFELINES = True
except Exception:
    CoxPHFitter = None  # type: ignore[assignment]
    KaplanMeierFitter = None  # type: ignore[assignment]
    HAVE_LIFELINES = False

from spinalmodes.utils.provenance import write_provenance
from spinalmodes.utils.seeds import set_seed


def synth_cohort(n: int = 10000) -> pd.DataFrame:
    """Generate a clearly marked synthetic cohort."""
    age = np.random.normal(60, 12, n).clip(35, 90)
    sit2stand = np.random.poisson(25, n)
    male = np.random.binomial(1, 0.55, n)
    bmi = np.random.normal(24, 3.5, n).clip(17, 38)
    baseline_hazard = 0.01 + 0.0005 * (age - 60) + 0.0002 * (bmi - 24) + 0.002 * male
    baseline_hazard = np.clip(baseline_hazard, 0.001, None)
    hazard = baseline_hazard * np.exp(-0.01 * (sit2stand - 20))
    hazard = np.clip(hazard, 0.001, None)
    t = np.random.exponential(1 / hazard)
    cens = np.random.binomial(1, 0.7, n)  # 70% censored
    time = np.minimum(t, 10.0)
    event = (t <= 10.0) * (1 - cens)
    return pd.DataFrame(
        dict(time=time, event=event, age=age, male=male, bmi=bmi, sit2stand=sit2stand)
    )


def _save_fallback_outputs(df: pd.DataFrame) -> None:
    """Create a labeled fallback figure when lifelines is unavailable."""
    times = np.linspace(0.0, 10.0, 200)
    fig, ax = plt.subplots()
    for label, scale in [("low", 0.14), ("mid", 0.10), ("high", 0.06)]:
        sub = df.loc[df["tertile"] == label]
        event_rate = max(scale, float(sub["event"].mean()) / 10.0)
        survival = np.exp(-event_rate * times)
        ax.plot(times, survival, linewidth=2, label=label)

    ax.set_title("SYNTHETIC-ILLUSTRATIVE: Survival by sit-to-stand tertile")
    ax.set_xlabel("years")
    ax.set_ylabel("S(t)")
    ax.grid(alpha=0.3)
    ax.legend(title="tertile")
    Path("figures").mkdir(parents=True, exist_ok=True)
    plt.savefig("figures/km_curves.pdf", bbox_inches="tight")
    plt.close(fig)

    fallback_summary = pd.DataFrame(
        [
            {
                "variable": "sit2stand",
                "coef": np.nan,
                "exp(coef)": np.nan,
                "p": np.nan,
                "note": "lifelines unavailable; fallback illustrative output",
            }
        ]
    )
    fallback_summary.to_csv("tables/cox_results.csv", index=False)
    write_provenance(
        "tables/cox_results.provenance.json",
        1337,
        {"n": len(df), "mode": "fallback"},
    )
    print("lifelines unavailable; wrote fallback illustrative survival outputs.")


def main() -> None:
    set_seed(1337)
    df = synth_cohort()
    Path("tables").mkdir(parents=True, exist_ok=True)
    df.to_csv("tables/longevity_synthetic.csv", index=False)

    df["tertile"] = pd.qcut(df["sit2stand"], 3, labels=["low", "mid", "high"])

    if not HAVE_LIFELINES:
        _save_fallback_outputs(df)
        return

    km = KaplanMeierFitter()
    fig, ax = plt.subplots()
    for g in ["low", "mid", "high"]:
        km.fit(df.loc[df.tertile == g, "time"], df.loc[df.tertile == g, "event"], label=g)
        km.plot(ci_show=False, ax=ax)

    ax.set_title("SYNTHETIC-ILLUSTRATIVE: Survival by sit-to-stand tertile")
    ax.set_xlabel("years")
    ax.set_ylabel("S(t)")
    ax.grid(alpha=0.3)
    Path("figures").mkdir(parents=True, exist_ok=True)
    fig.savefig("figures/km_curves.pdf", bbox_inches="tight")
    plt.close(fig)

    cph = CoxPHFitter()
    cph.fit(
        df[["time", "event", "age", "male", "bmi", "sit2stand"]],
        duration_col="time",
        event_col="event",
    )
    cph.summary.to_csv("tables/cox_results.csv")
    write_provenance("tables/cox_results.provenance.json", 1337, {"n": len(df), "mode": "lifelines"})
    print(cph.summary)


if __name__ == "__main__":
    main()
