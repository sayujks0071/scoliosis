#!/usr/bin/env python3
"""
Generate publication figures for the AlphaFold-to-DDE extension.

Figures:
  Fig 6: Molecular parameter mapping schematic (protein flexibility → DDE params)
  Fig 7: Genotype-stratified vulnerability curves (τ sweep)
  Fig 8: K_d sensitivity at healthy vs molecular damping
  Fig 9: Trajectory comparison across genotypes
  Fig 10: Delay decomposition bar chart
"""

import numpy as np
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

FIG = Path("/sessions/gracious-relaxed-dirac/mnt/life/figures_alphafold")
FIG.mkdir(parents=True, exist_ok=True)

# Load results
with open("/sessions/gracious-relaxed-dirac/mnt/life/results/alphafold_molecular_results.json") as f:
    data = json.load(f)

# ─── Color palette ────────────────────────────────────────────────────
C = {
    "baseline": "#2c3e50",
    "molecular": "#2980b9",
    "lbx1": "#e74c3c",
    "combined": "#8e44ad",
    "fbn1": "#e67e22",
    "pax1": "#27ae60",
    "stable": "#27ae60",
    "unstable": "#e74c3c",
    "accent": "#3498db",
}

scenario_colors = {
    "Baseline (default params)": C["baseline"],
    "Molecular-adjusted (AlphaFold)": C["molecular"],
    "LBX1 risk variant": C["lbx1"],
    "Combined risk (LBX1 + PAX1)": C["combined"],
    "FBN1 (Marfan-type)": C["fbn1"],
}

scenario_labels = {
    "Baseline (default params)": "Baseline",
    "Molecular-adjusted (AlphaFold)": "AlphaFold-adjusted",
    "LBX1 risk variant": "LBX1 variant",
    "Combined risk (LBX1 + PAX1)": "Combined risk",
    "FBN1 (Marfan-type)": "FBN1/Marfan",
}

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 6: Protein Flexibility → DDE Parameter Mapping
# ═══════════════════════════════════════════════════════════════════════
fig6, axes = plt.subplots(1, 3, figsize=(12, 4))

# Panel A: Structural proteins → damping
ax = axes[0]
proteins = ["COL1A1", "COL2A1"]
flex_vals = [data["module_a_structural"][p]["domain_flexibility"] for p in proteins]
plddt_vals = [data["module_a_structural"][p]["mean_plddt"] for p in proteins]

bars = ax.bar(proteins, flex_vals, color=[C["accent"], C["molecular"]], width=0.5, edgecolor="black", linewidth=0.5)
ax.set_ylabel("Flexibility Index")
ax.set_title("A. Collagen Flexibility")
ax.set_ylim(0, 0.7)

# Add pLDDT annotations
for bar, p_val in zip(bars, plddt_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f"pLDDT={p_val:.0f}", ha="center", va="bottom", fontsize=8)

# Add mapping arrow/text
b_mol = data["module_a_structural"]["parameter_mapping"]["b_molecular"]
ax.text(0.5, 0.45, f"→ b = {b_mol:.3f}\n(baseline 1.000)",
        transform=ax.transAxes, fontsize=9, ha="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#ecf0f1", alpha=0.8))

# Panel B: Receptor proteins → delay components
ax = axes[1]
delay = data["module_b_receptors"]["delay_decomposition"]
components = ["τ_proprio\n(PIEZO2)", "τ_tissue\n(GPR126)", "τ_growth\n(MTNR1B)"]
values = [delay["tau_proprioceptive_ms"], delay["tau_tissue_remodel_ms"], delay["tau_growth_timing_ms"]]
colors = ["#e74c3c", "#3498db", "#2ecc71"]

bars = ax.bar(components, values, color=colors, width=0.5, edgecolor="black", linewidth=0.5)
ax.set_ylabel("Delay Component (ms)")
ax.set_title("B. Delay Decomposition")

# Total line
ax.axhline(delay["tau_eff_ms"], color="black", linestyle="--", linewidth=1)
ax.text(2.3, delay["tau_eff_ms"] + 1, f"τ_eff = {delay['tau_eff_ms']:.1f} ms",
        fontsize=8, ha="right", va="bottom")

# Panel C: Variant perturbations
ax = axes[2]
variants = ["LBX1", "PAX1"]
perturbations = [data["module_c_variants"][v]["variant_perturbation"] * 100 for v in variants]
targets = [data["module_c_variants"][v]["dde_target"] for v in variants]

bars = ax.bar(variants, perturbations, color=[C["lbx1"], C["pax1"]], width=0.5, edgecolor="black", linewidth=0.5)
ax.set_ylabel("Variant Perturbation (%)")
ax.set_title("C. AIS Variant Effects")

for bar, target in zip(bars, targets):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f"→ {target}", ha="center", va="bottom", fontsize=9, fontweight="bold")

fig6.suptitle("Figure 6: AlphaFold-Derived Molecular Parameters", fontsize=13, fontweight="bold", y=1.02)
plt.tight_layout()
fig6.savefig(FIG / "fig6_molecular_parameters.png")
fig6.savefig(FIG / "fig6_molecular_parameters.pdf")
print("✓ Figure 6 saved")

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 7: Genotype-Stratified Vulnerability Curves
# ═══════════════════════════════════════════════════════════════════════
fig7, ax = plt.subplots(figsize=(8, 5))

vuln = data["vulnerability_analysis"]
for sname in scenario_colors:
    if sname not in vuln:
        continue
    v = vuln[sname]
    tau_ms = v["tau_ms"]
    amps = v["max_amp_deg"]
    # Clip amps for log scale
    amps_clipped = [max(a, 0.1) for a in amps]
    ax.semilogy(tau_ms, amps_clipped, color=scenario_colors[sname],
                linewidth=2, label=scenario_labels[sname])
    # Mark τ*
    tc = v["tau_star_ms"]
    ax.axvline(tc, color=scenario_colors[sname], linestyle=":", linewidth=0.8, alpha=0.6)

# 10° threshold
ax.axhline(10, color="gray", linestyle="--", linewidth=1, alpha=0.5)
ax.text(42, 12, "Clinical threshold (10°)", fontsize=8, color="gray")

# Shade unstable region
ax.axhspan(10, 1e15, alpha=0.05, color="red")

ax.set_xlabel("Sensorimotor Delay τ (ms)")
ax.set_ylabel("Maximum Deflection (degrees)")
ax.set_title("Figure 7: Genotype-Stratified Vulnerability to Delay", fontweight="bold")
ax.set_xlim(40, 140)
ax.set_ylim(0.1, 1e6)
ax.legend(loc="upper left", framealpha=0.9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
fig7.savefig(FIG / "fig7_vulnerability_curves.png")
fig7.savefig(FIG / "fig7_vulnerability_curves.pdf")
print("✓ Figure 7 saved")

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 8: K_d Sensitivity — Derivative Gain Trap at Molecular Damping
# ═══════════════════════════════════════════════════════════════════════
fig8, ax = plt.subplots(figsize=(7, 5))

kd_sens = data["kd_sensitivity"]
for label, style in [("healthy", {"color": C["baseline"], "linewidth": 2, "linestyle": "-"}),
                     ("molecular", {"color": C["molecular"], "linewidth": 2, "linestyle": "--"})]:
    kd_vals = kd_sens[label]["Kd"]
    ts_vals = kd_sens[label]["tau_star_ms"]
    ax.plot(kd_vals, ts_vals, label=f"b={kd_sens[label]['b']:.3f} ({label})", **style)

# Mark optimal K_d
for label, color in [("healthy", C["baseline"]), ("molecular", C["molecular"])]:
    kd_vals = kd_sens[label]["Kd"]
    ts_vals = kd_sens[label]["tau_star_ms"]
    best_idx = np.argmax(ts_vals)
    ax.plot(kd_vals[best_idx], ts_vals[best_idx], "o", color=color, markersize=8, zorder=5)
    ax.annotate(f"K*_d={kd_vals[best_idx]:.1f}\nτ*={ts_vals[best_idx]:.1f}ms",
                xy=(kd_vals[best_idx], ts_vals[best_idx]),
                xytext=(kd_vals[best_idx]+3, ts_vals[best_idx]-3),
                fontsize=8, arrowprops=dict(arrowstyle="->", color=color))

# Mark the molecular τ_eff
tau_eff = data["module_b_receptors"]["delay_decomposition"]["tau_eff_ms"]
ax.axhline(tau_eff, color=C["lbx1"], linestyle=":", linewidth=1.5, alpha=0.7)
ax.text(28, tau_eff + 1, f"τ_eff = {tau_eff:.1f} ms (AlphaFold)", fontsize=8, color=C["lbx1"])

ax.set_xlabel("Derivative Gain K_d")
ax.set_ylabel("Critical Delay τ* (ms)")
ax.set_title("Figure 8: The Derivative Gain Trap\n(Molecular vs Healthy Damping)", fontweight="bold")
ax.legend(loc="lower right", framealpha=0.9)
ax.grid(True, alpha=0.3)
ax.set_xlim(2, 30)

plt.tight_layout()
fig8.savefig(FIG / "fig8_kd_trap_molecular.png")
fig8.savefig(FIG / "fig8_kd_trap_molecular.pdf")
print("✓ Figure 8 saved")

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 9: Trajectory Comparison Across Genotypes
# ═══════════════════════════════════════════════════════════════════════
fig9, axes9 = plt.subplots(2, 3, figsize=(12, 6), sharex=True)
axes_flat = axes9.flatten()

for idx, (sname, color) in enumerate(scenario_colors.items()):
    if idx >= 6:
        break
    ax = axes_flat[idx]
    traj = data["trajectory_data"][sname]
    t = traj["t"]
    theta = traj["theta"]
    ax.plot(t, theta, color=color, linewidth=0.8)

    params = data["integrated_scenarios"][sname]["params"]
    tc = data["integrated_scenarios"][sname]["tau_star_ms"]
    is_stable = data["integrated_scenarios"][sname]["stable"]

    status = "STABLE" if is_stable else "UNSTABLE"
    status_color = C["stable"] if is_stable else C["unstable"]
    ax.set_title(f"{scenario_labels[sname]}", fontsize=9)

    # Info box
    info = f"τ={params['tau']*1000:.0f}ms, τ*={tc:.0f}ms\n{status}"
    ax.text(0.97, 0.97, info, transform=ax.transAxes, fontsize=7,
            va="top", ha="right", bbox=dict(boxstyle="round", facecolor=status_color, alpha=0.15))

    ax.set_ylabel("θ (degrees)" if idx % 3 == 0 else "")
    if idx >= 3:
        ax.set_xlabel("Time (s)")
    ax.grid(True, alpha=0.2)

# Hide unused axes
for idx in range(len(scenario_colors), 6):
    axes_flat[idx].set_visible(False)

fig9.suptitle("Figure 9: DDE Trajectories Under Molecular Parameterisation", fontweight="bold", y=1.02)
plt.tight_layout()
fig9.savefig(FIG / "fig9_trajectories.png")
fig9.savefig(FIG / "fig9_trajectories.pdf")
print("✓ Figure 9 saved")

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 10: Stability Margin Summary
# ═══════════════════════════════════════════════════════════════════════
fig10, ax = plt.subplots(figsize=(8, 4.5))

scenarios_ordered = ["Baseline (default params)", "Molecular-adjusted (AlphaFold)",
                     "LBX1 risk variant", "PAX1 risk variant",
                     "Combined risk (LBX1 + PAX1)", "FBN1 (Marfan-type)"]
labels = [scenario_labels.get(s, s.split("(")[0].strip()) for s in scenarios_ordered]
if "PAX1 risk variant" not in scenario_labels:
    labels[3] = "PAX1 variant"

margins = []
bar_colors = []
for s in scenarios_ordered:
    sc = data["integrated_scenarios"][s]
    margin = sc.get("stability_margin_ms", 0)
    if margin is None:
        margin = 0
    margins.append(margin)
    bar_colors.append(C["stable"] if margin > 0 else C["unstable"])

y_pos = np.arange(len(scenarios_ordered))
bars = ax.barh(y_pos, margins, color=bar_colors, edgecolor="black", linewidth=0.5, height=0.6)

# Zero line
ax.axvline(0, color="black", linewidth=1.5)

# Annotate values
for i, (bar, margin) in enumerate(zip(bars, margins)):
    x_pos = margin + (1 if margin >= 0 else -1)
    ha = "left" if margin >= 0 else "right"
    ax.text(x_pos, i, f"{margin:+.1f} ms", va="center", ha=ha, fontsize=9, fontweight="bold")

ax.set_yticks(y_pos)
ax.set_yticklabels(labels)
ax.set_xlabel("Stability Margin (τ* − τ) in ms")
ax.set_title("Figure 10: Stability Margins Under Molecular Parameterisation", fontweight="bold")
ax.grid(True, axis="x", alpha=0.3)
ax.invert_yaxis()

# Shade regions
ax.axvspan(-35, 0, alpha=0.05, color="red")
ax.axvspan(0, 10, alpha=0.05, color="green")
ax.text(-1, -0.5, "UNSTABLE", fontsize=8, color=C["unstable"], ha="right", fontweight="bold")
ax.text(1, -0.5, "STABLE", fontsize=8, color=C["stable"], ha="left", fontweight="bold")

plt.tight_layout()
fig10.savefig(FIG / "fig10_stability_margins.png")
fig10.savefig(FIG / "fig10_stability_margins.pdf")
print("✓ Figure 10 saved")

print("\n✓ All AlphaFold extension figures saved to figures_alphafold/")
