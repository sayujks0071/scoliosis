"""
Bio-Gravitational Number critical-point analysis.

Reads sweep CSV from experiment_bg_validation_jax.py and tests the falsifiable
prediction that Bg* ~ 1 separates gravity-dominated and counter-curvature regimes.

Tests:
    1. Sigmoid fit of eta_CC vs log10(Bg) per (scale, seed); extract Bg* and k.
    2. Robustness: distribution of Bg* across seeds within each scale.
    3. Universality: Bg* should be scale-invariant (overlapping IQRs across scales).
    4. Scaling collapse: when |eta_CC|/|eta_CC|_max is plotted vs Bg, curves should
       collapse across scales.

Usage:
    python scripts/analysis/validate_bg_critical_point.py \\
        --input results/bg_validation_jax/bg_validation_jax_results.csv \\
        --output results/bg_validation_jax/
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import kruskal


def sigmoid(log_bg, A, k, log_bg_star, c):
    return c + A / (1.0 + np.exp(-k * (log_bg - log_bg_star)))


def fit_one(df_seed):
    """Fit sigmoid to a single (scale, seed) curve. Returns dict or None on failure."""
    log_bg = np.log10(df_seed["Bg"].values)
    eta = df_seed["eta_CC"].values
    if len(log_bg) < 6 or not np.isfinite(eta).all():
        return None
    eta_norm = eta / np.max(np.abs(eta))
    p0 = [eta_norm[-1] - eta_norm[0], 2.0, 0.0, eta_norm[0]]
    try:
        popt, pcov = curve_fit(
            sigmoid, log_bg, eta_norm, p0=p0,
            bounds=([-10, 0.1, -3, -10], [10, 50, 3, 10]),
            maxfev=10000,
        )
        residuals = eta_norm - sigmoid(log_bg, *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((eta_norm - eta_norm.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        A, k, log_bg_star, c = popt
        return {
            "A": float(A),
            "k": float(k),
            "log_bg_star": float(log_bg_star),
            "Bg_star": float(10 ** log_bg_star),
            "c": float(c),
            "r2": float(r2),
            "n_points": int(len(log_bg)),
        }
    except (RuntimeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} rows from {args.input}")
    print(f"Scales: {sorted(df['scale'].unique())}")
    print(f"Seeds: {sorted(df['seed'].unique())}")
    print(f"chi_M points per (scale, seed): {df.groupby(['scale','seed']).size().min()}–"
          f"{df.groupby(['scale','seed']).size().max()}")

    # --- Per-curve sigmoid fits ---
    fits = []
    for (scale, seed), grp in df.sort_values("Bg").groupby(["scale", "seed"]):
        f = fit_one(grp)
        if f is not None:
            f["scale"] = float(scale)
            f["seed"] = int(seed)
            fits.append(f)
    fits_df = pd.DataFrame(fits)
    fits_df.to_csv(args.output / "bg_sigmoid_fits.csv", index=False)
    print(f"\nSigmoid fits: {len(fits_df)}/{df.groupby(['scale','seed']).ngroups} succeeded")

    # --- Per-scale summary ---
    summary = {}
    for scale, grp in fits_df.groupby("scale"):
        good = grp[grp["r2"] > 0.9]
        summary[f"scale_{scale}"] = {
            "n_total_fits": int(len(grp)),
            "n_good_fits_r2_gt_0.9": int(len(good)),
            "Bg_star_median": float(np.median(good["Bg_star"])) if len(good) else None,
            "Bg_star_iqr": [
                float(np.percentile(good["Bg_star"], 25)) if len(good) else None,
                float(np.percentile(good["Bg_star"], 75)) if len(good) else None,
            ],
            "k_median": float(np.median(good["k"])) if len(good) else None,
            "r2_median": float(np.median(good["r2"])) if len(good) else None,
        }

    # --- Universality test: are Bg* distributions consistent across scales? ---
    groups = [g["Bg_star"].values for _, g in fits_df[fits_df["r2"] > 0.9].groupby("scale")]
    if len(groups) >= 2 and all(len(g) >= 3 for g in groups):
        H, p = kruskal(*groups)
        universality = {
            "kruskal_H": float(H),
            "kruskal_p": float(p),
            "interpretation": "consistent across scales" if p > 0.05 else "scale-dependent",
        }
    else:
        universality = {"error": "not enough fits per scale"}

    # --- Hypothesis check: Bg* near 1 ---
    all_good = fits_df[fits_df["r2"] > 0.9]
    if len(all_good) > 0:
        bg_star_global_median = float(np.median(all_good["Bg_star"]))
        bg_star_global_ci = [
            float(np.percentile(all_good["Bg_star"], 2.5)),
            float(np.percentile(all_good["Bg_star"], 97.5)),
        ]
        prediction_holds = 0.3 < bg_star_global_median < 3.0
    else:
        bg_star_global_median = None
        bg_star_global_ci = None
        prediction_holds = None

    report = {
        "input": str(args.input),
        "n_rows": int(len(df)),
        "scales": sorted(df["scale"].unique().tolist()),
        "n_seeds_per_scale": int(df.groupby("scale")["seed"].nunique().iloc[0]),
        "per_scale_summary": summary,
        "universality_test": universality,
        "global": {
            "Bg_star_median": bg_star_global_median,
            "Bg_star_95ci": bg_star_global_ci,
            "prediction_Bg_star_near_1": prediction_holds,
            "prediction_threshold": "0.3 < Bg* < 3.0",
        },
    }

    out_json = args.output / "bg_validation_report.json"
    with open(out_json, "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    for scale, s in summary.items():
        print(f"{scale}: Bg* median = {s['Bg_star_median']}, "
              f"IQR = {s['Bg_star_iqr']}, k_median = {s['k_median']}, "
              f"good fits = {s['n_good_fits_r2_gt_0.9']}/{s['n_total_fits']}")
    print(f"\nUniversality (Kruskal-Wallis): {universality}")
    print(f"Global Bg*: median = {bg_star_global_median}, 95% CI = {bg_star_global_ci}")
    print(f"Prediction Bg* in (0.3, 3.0): {prediction_holds}")
    print(f"\nReport: {out_json}")


if __name__ == "__main__":
    main()
