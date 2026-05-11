#!/usr/bin/env python3
"""
Generate publication-ready figures for:
"The Derivative Gain Gap: A Control-Theoretic Mechanism for Adolescent Idiopathic Scoliosis"
Target journal: Spine Deformity

Figures:
  1. Kd-tau Stability Map (Heatmap) with Hopf bifurcation boundary
  2. Growth-Phase Trajectory overlaid on stability map
  3. Sex-Specific Vulnerability Windows
  4. Brace Mechanism Reinterpretation
  5. Model Overview Schematic (block diagram)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import patheffects
import os

# ============================================================
# Output directory
# ============================================================
OUT_DIR = "/Users/mac/life/life/outputs/spine_deformity_figures"
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================
# Publication style
# ============================================================
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "lines.linewidth": 1.2,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# ============================================================
# Physical parameters (from phase3_kd_trap.py)
# ============================================================
I = 0.8          # moment of inertia (kg m^2)
b = 1.0          # damping (Nm s/rad)
m = 25.0         # mass (kg)
g = 9.81         # gravity (m/s^2)
L = 0.30         # CoM height (m)
mgl = m * g * L  # gravitational torque = 73.575
Kp = 120.0       # proportional gain (Nm/rad)


# ============================================================
# DDE simulator (matches phase3_kd_trap.py)
# ============================================================
def simulate_dde(tau_eff, duration=20.0, dt=0.0005, theta0=0.05,
                 Kp_val=None, Kd_val=None):
    """Delayed differential equation simulation of inverted pendulum spine model."""
    if Kp_val is None:
        Kp_val = Kp
    if Kd_val is None:
        Kd_val = 8.0

    N = int(duration / dt)
    ds = max(int(tau_eff / dt), 1) if tau_eff > 0 else 0

    th = np.zeros(N + ds)
    dth = np.zeros(N + ds)
    th[:ds + 1] = theta0

    AMP_CAP = 50.0

    for i in range(ds, ds + N - 1):
        th_d = th[i - ds] if ds > 0 else th[i]
        dth_d = dth[i - ds] if ds > 0 else dth[i]

        ddth = (mgl * th[i] - b * dth[i] - Kp_val * th_d - Kd_val * dth_d) / I

        dth[i + 1] = dth[i] + ddth * dt
        th[i + 1] = th[i] + dth[i + 1] * dt

        if abs(th[i + 1]) > AMP_CAP:
            th[i + 1:] = AMP_CAP * np.sign(th[i + 1])
            dth[i + 1:] = 0
            break

    t = np.arange(N) * dt
    return t, th[ds:ds + N]


def max_amplitude(tau, Kd_val, Kp_val=120.0, duration=20.0):
    """Run a simulation and return the max |theta| in the last 50% of the signal."""
    t, th = simulate_dde(tau, duration=duration, Kp_val=Kp_val, Kd_val=Kd_val)
    half = len(th) // 2
    return np.max(np.abs(th[half:]))


# ============================================================
# FIGURE 1: Kd-tau Stability Map
# ============================================================
print("Generating Figure 1: Kd-tau Stability Map...")

Kd_range = np.linspace(0.5, 25, 80)
tau_range = np.linspace(0.001, 0.200, 80)  # 1-200 ms

amp_map = np.zeros((len(tau_range), len(Kd_range)))

for j, kd in enumerate(Kd_range):
    for i, tau in enumerate(tau_range):
        amp_map[i, j] = max_amplitude(tau, kd)
    if (j + 1) % 20 == 0:
        print(f"  Kd sweep {j+1}/{len(Kd_range)}")

# Clip for visualization
amp_map_vis = np.clip(amp_map, 0, 2.0)

# Find Hopf boundary: contour where amplitude crosses a threshold
hopf_threshold = 0.15  # rad ~ 8.6 degrees -- onset of sustained oscillation

# Find the optimal Kd (maximum tau* for stability)
optimal_kd_idx = None
optimal_tau_idx = None
max_stable_tau = 0
for j, kd in enumerate(Kd_range):
    for i in range(len(tau_range) - 1, -1, -1):
        if amp_map[i, j] < hopf_threshold:
            if tau_range[i] > max_stable_tau:
                max_stable_tau = tau_range[i]
                optimal_kd_idx = j
                optimal_tau_idx = i
            break

fig, ax = plt.subplots(figsize=(3.5, 3.0))

# Use tau in ms for display
tau_ms = tau_range * 1000

im = ax.pcolormesh(Kd_range, tau_ms, amp_map_vis,
                    cmap="magma_r", shading="auto", vmin=0, vmax=1.5)
cb = fig.colorbar(im, ax=ax, label="Max amplitude (rad)", shrink=0.85, pad=0.02)
cb.ax.tick_params(labelsize=7)

# Hopf bifurcation contour
cs = ax.contour(Kd_range, tau_ms, amp_map, levels=[hopf_threshold],
                colors="white", linewidths=1.5, linestyles="-")
ax.clabel(cs, fmt={hopf_threshold: "Hopf boundary"}, fontsize=7,
          colors="white", inline_spacing=2)

# Mark optimal Kd
if optimal_kd_idx is not None:
    ax.plot(Kd_range[optimal_kd_idx], tau_ms[optimal_tau_idx], "o",
            color="cyan", markersize=6, markeredgecolor="white", markeredgewidth=0.8,
            zorder=5)
    ax.annotate(f"Optimal $K_d$={Kd_range[optimal_kd_idx]:.1f}",
                xy=(Kd_range[optimal_kd_idx], tau_ms[optimal_tau_idx]),
                xytext=(Kd_range[optimal_kd_idx] + 3, tau_ms[optimal_tau_idx] + 15),
                fontsize=7, color="white",
                arrowprops=dict(arrowstyle="->", color="white", lw=0.8))

# Shade the derivative gain trap region (high Kd, low tau*)
ax.annotate("Derivative\ngain trap",
            xy=(22, 40), fontsize=7, color="white", ha="center",
            fontstyle="italic",
            path_effects=[patheffects.withStroke(linewidth=2, foreground="black")])

ax.set_xlabel("Derivative gain $K_d$ (Nm$\\cdot$s/rad)")
ax.set_ylabel("Neural delay $\\tau$ (ms)")
ax.set_title("Fig. 1: $K_d$--$\\tau$ Stability Map", fontweight="bold", fontsize=9)

fig.savefig(os.path.join(OUT_DIR, "fig1_stability_map.png"))
fig.savefig(os.path.join(OUT_DIR, "fig1_stability_map.pdf"))
plt.close(fig)
print("  Saved fig1_stability_map.png/pdf")


# ============================================================
# FIGURE 2: Growth-Phase Trajectory
# ============================================================
print("Generating Figure 2: Growth-Phase Trajectory...")

# CDC growth velocity data (approximate)
ages = np.linspace(8, 18, 200)

def growth_velocity_female(age):
    """Female PHV at ~11.5y, ~8 cm/yr peak."""
    return 4.0 + 4.0 * np.exp(-0.5 * ((age - 11.5) / 1.0) ** 2)

def growth_velocity_male(age):
    """Male PHV at ~13.5y, ~9 cm/yr peak."""
    return 4.0 + 5.0 * np.exp(-0.5 * ((age - 13.5) / 1.2) ** 2)

# Model: During rapid growth, proprioceptive recalibration lags
# -> effective Kd degrades proportional to growth velocity
# -> effective tau increases proportional to growth velocity

Kd_baseline = 12.0  # healthy baseline
tau_baseline_ms = 45.0  # healthy baseline neural delay (ms)

def kd_during_growth(age, gv_func):
    """Kd degrades when growth velocity is high.
    From parameter exploration: Kd=7 at tau=60ms is stable, Kd=7 at tau=70ms is unstable.
    So at PHV, Kd dropping from 12 to ~7 with tau rising to ~70ms crosses the boundary.
    """
    gv = gv_func(age)
    gv_norm = (gv - 4.0) / 5.0  # normalize: 0 at baseline, ~1 at peak
    gv_norm = np.clip(gv_norm, 0, 1)
    return Kd_baseline * (1 - 0.42 * gv_norm)  # up to 42% degradation at PHV -> Kd~7

def tau_during_growth(age, gv_func):
    """Effective delay increases during rapid growth (longer limbs, recalibrating)."""
    gv = gv_func(age)
    gv_norm = (gv - 4.0) / 5.0
    gv_norm = np.clip(gv_norm, 0, 1)
    return tau_baseline_ms + 30 * gv_norm  # up to +30 ms at PHV -> ~75ms

kd_female = np.array([kd_during_growth(a, growth_velocity_female) for a in ages])
tau_female = np.array([tau_during_growth(a, growth_velocity_female) for a in ages])
kd_male = np.array([kd_during_growth(a, growth_velocity_male) for a in ages])
tau_male = np.array([tau_during_growth(a, growth_velocity_male) for a in ages])

fig, ax = plt.subplots(figsize=(3.5, 3.0))

# Background stability map (reuse data)
im = ax.pcolormesh(Kd_range, tau_ms, amp_map_vis,
                    cmap="magma_r", shading="auto", vmin=0, vmax=1.5, alpha=0.7)
cb = fig.colorbar(im, ax=ax, label="Max amplitude (rad)", shrink=0.85, pad=0.02)
cb.ax.tick_params(labelsize=7)

# Hopf boundary
ax.contour(Kd_range, tau_ms, amp_map, levels=[hopf_threshold],
           colors="white", linewidths=1.2, linestyles="--")

# Female trajectory
ax.plot(kd_female, tau_female, "-", color="#FF6B6B", lw=2.0, label="Female", zorder=10)
# Mark PHV point
phv_f_idx = np.argmin(np.abs(ages - 11.5))
ax.plot(kd_female[phv_f_idx], tau_female[phv_f_idx], "o", color="#FF6B6B",
        markersize=7, markeredgecolor="white", markeredgewidth=1, zorder=11)
ax.annotate("PHV\n11.5y", xy=(kd_female[phv_f_idx], tau_female[phv_f_idx]),
            xytext=(kd_female[phv_f_idx] - 3.5, tau_female[phv_f_idx] + 12),
            fontsize=6.5, color="#FF6B6B", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#FF6B6B", lw=0.8),
            path_effects=[patheffects.withStroke(linewidth=1.5, foreground="black")])

# Direction arrows along female trajectory
for frac in [0.15, 0.55, 0.85]:
    idx = int(frac * len(ages))
    dx = kd_female[min(idx+1, len(ages)-1)] - kd_female[max(idx-1, 0)]
    dy = tau_female[min(idx+1, len(ages)-1)] - tau_female[max(idx-1, 0)]
    ax.annotate("", xy=(kd_female[idx] + dx*2, tau_female[idx] + dy*2),
                xytext=(kd_female[idx], tau_female[idx]),
                arrowprops=dict(arrowstyle="->", color="#FF6B6B", lw=1.0))

# Male trajectory
ax.plot(kd_male, tau_male, "-", color="#4DABF7", lw=2.0, label="Male", zorder=10)
phv_m_idx = np.argmin(np.abs(ages - 13.5))
ax.plot(kd_male[phv_m_idx], tau_male[phv_m_idx], "o", color="#4DABF7",
        markersize=7, markeredgecolor="white", markeredgewidth=1, zorder=11)
ax.annotate("PHV\n13.5y", xy=(kd_male[phv_m_idx], tau_male[phv_m_idx]),
            xytext=(kd_male[phv_m_idx] + 2.5, tau_male[phv_m_idx] + 12),
            fontsize=6.5, color="#4DABF7", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#4DABF7", lw=0.8),
            path_effects=[patheffects.withStroke(linewidth=1.5, foreground="black")])

# Start/end labels
ax.annotate("8y", xy=(kd_female[0], tau_female[0]), fontsize=6, color="white",
            xytext=(-5, 5), textcoords="offset points",
            path_effects=[patheffects.withStroke(linewidth=1.5, foreground="black")])
ax.annotate("18y", xy=(kd_female[-1], tau_female[-1]), fontsize=6, color="white",
            xytext=(-5, -10), textcoords="offset points",
            path_effects=[patheffects.withStroke(linewidth=1.5, foreground="black")])

ax.legend(loc="upper left", framealpha=0.7, edgecolor="none", fontsize=7,
          facecolor="black", labelcolor="white")

ax.set_xlabel("Effective $K_d$ (Nm$\\cdot$s/rad)")
ax.set_ylabel("Effective neural delay $\\tau$ (ms)")
ax.set_title("Fig. 2: Growth-Phase Trajectory", fontweight="bold", fontsize=9)
ax.set_xlim(Kd_range[0], Kd_range[-1])
ax.set_ylim(tau_ms[0], tau_ms[-1])

fig.savefig(os.path.join(OUT_DIR, "fig2_growth_trajectory.png"))
fig.savefig(os.path.join(OUT_DIR, "fig2_growth_trajectory.pdf"))
plt.close(fig)
print("  Saved fig2_growth_trajectory.png/pdf")


# ============================================================
# FIGURE 3: Sex-Specific Vulnerability Windows
# ============================================================
print("Generating Figure 3: Sex-Specific Vulnerability Windows...")

# Compute stability margin = tau*(Kd_eff) - tau_eff
# tau* is the critical delay at the current Kd: the max tau before instability
def find_tau_crit(Kd_val, Kp_val=120.0, threshold=0.15, tau_max=0.25, n_steps=100):
    """Find critical delay by binary search."""
    lo, hi = 0.001, tau_max
    for _ in range(n_steps):
        mid = (lo + hi) / 2
        amp = max_amplitude(mid, Kd_val, Kp_val)
        if amp < threshold:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

# Precompute tau* for a range of Kd values (cache for speed)
print("  Computing tau* lookup table...")
kd_lookup = np.linspace(3, 20, 60)
tau_crit_lookup = np.array([find_tau_crit(kd, n_steps=30) for kd in kd_lookup])

def tau_star_interp(kd):
    """Interpolate tau* from lookup table."""
    return np.interp(kd, kd_lookup, tau_crit_lookup)

# Stability margin for each sex
margin_female_ms = np.array([
    tau_star_interp(kd_during_growth(a, growth_velocity_female)) * 1000
    - tau_during_growth(a, growth_velocity_female)
    for a in ages
])
margin_male_ms = np.array([
    tau_star_interp(kd_during_growth(a, growth_velocity_male)) * 1000
    - tau_during_growth(a, growth_velocity_male)
    for a in ages
])

fig, ax = plt.subplots(figsize=(3.5, 2.8))

ax.plot(ages, margin_female_ms, "-", color="#E64980", lw=2.0, label="Female")
ax.plot(ages, margin_male_ms, "-", color="#339AF0", lw=2.0, label="Male")

# Shade unstable region (below zero)
ax.fill_between(ages, -50, 0, alpha=0.12, color="red", label="Unstable region")
ax.axhline(0, color="black", lw=0.8, ls="--", alpha=0.6)

# Shade female vulnerable window
f_unstable = ages[margin_female_ms < 0]
if len(f_unstable) > 0:
    ax.axvspan(f_unstable[0], f_unstable[-1], alpha=0.08, color="#E64980")

# Shade male vulnerable window
m_unstable = ages[margin_male_ms < 0]
if len(m_unstable) > 0:
    ax.axvspan(m_unstable[0], m_unstable[-1], alpha=0.08, color="#339AF0")

# Clinical AIS onset windows (from literature)
# Female: typically 10-13y, Male: typically 12-15y
ax.annotate("", xy=(10, -42), xytext=(13, -42),
            arrowprops=dict(arrowstyle="<->", color="#E64980", lw=1.5))
ax.text(11.5, -46, "Clinical AIS\nonset (F)", fontsize=6, color="#E64980",
        ha="center", va="top")

ax.annotate("", xy=(12, -35), xytext=(15, -35),
            arrowprops=dict(arrowstyle="<->", color="#339AF0", lw=1.5))
ax.text(13.5, -39, "Clinical AIS\nonset (M)", fontsize=6, color="#339AF0",
        ha="center", va="top")

# Mark PHV
ax.axvline(11.5, color="#E64980", lw=0.6, ls=":", alpha=0.7)
ax.axvline(13.5, color="#339AF0", lw=0.6, ls=":", alpha=0.7)
ax.text(11.5, ax.get_ylim()[1] * 0.9, "PHV(F)", fontsize=6, color="#E64980",
        ha="center", rotation=90, va="top")
ax.text(13.5, ax.get_ylim()[1] * 0.9, "PHV(M)", fontsize=6, color="#339AF0",
        ha="center", rotation=90, va="top")

ax.set_xlabel("Age (years)")
ax.set_ylabel("Stability margin: $\\tau^* - \\tau_{eff}$ (ms)")
ax.set_title("Fig. 3: Sex-Specific Vulnerability Windows", fontweight="bold", fontsize=9)
ax.set_xlim(8, 18)
ax.legend(loc="upper right", framealpha=0.9, edgecolor="none", fontsize=7)

fig.savefig(os.path.join(OUT_DIR, "fig3_vulnerability_windows.png"))
fig.savefig(os.path.join(OUT_DIR, "fig3_vulnerability_windows.pdf"))
plt.close(fig)
print("  Saved fig3_vulnerability_windows.png/pdf")


# ============================================================
# FIGURE 4: Brace Mechanism Reinterpretation
# ============================================================
print("Generating Figure 4: Brace Mechanism Reinterpretation...")

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), gridspec_kw={"wspace": 0.35})

# Panel A: Stability margin comparison
ax = axes[0]

# Conditions
conditions = ["Pre-PHV\n(age 9)", "PHV\n(no brace)", "PHV\n(with brace)"]

# Pre-PHV: high Kd, low tau -> comfortably stable
kd_pre = 11.5   # near baseline
tau_pre = 48.0   # near baseline (ms)
margin_pre = tau_star_interp(kd_pre) * 1000 - tau_pre

# PHV no brace: degraded Kd, higher tau -> just past Hopf boundary
# From param exploration: Kd=7, tau=70ms is unstable
kd_phv = 7.0
tau_phv = 70.0   # ms
margin_phv = tau_star_interp(kd_phv) * 1000 - tau_phv

# PHV with brace: brace augments effective Kd by ~40% via haptic feedback
# Kd=10, tau=70ms is stable from param exploration
kd_brace = 10.0
tau_brace = 68.0  # slight reduction from mechanical stiffening
margin_brace = tau_star_interp(kd_brace) * 1000 - tau_brace

margins = [margin_pre, margin_phv, margin_brace]
colors = ["#51CF66", "#FF6B6B", "#4DABF7"]

bars = ax.bar(conditions, margins, color=colors, edgecolor="black", linewidth=0.6, width=0.6)
ax.axhline(0, color="black", lw=0.8, ls="--")
ax.fill_between([-0.5, 2.5], [-50, -50], [0, 0], alpha=0.06, color="red")
ax.text(2.3, -3, "UNSTABLE", fontsize=6, color="red", alpha=0.5, ha="right")

for bar, val in zip(bars, margins):
    y_pos = val + 1 if val > 0 else val - 4
    ax.text(bar.get_x() + bar.get_width() / 2, y_pos,
            f"{val:.0f} ms", ha="center", va="bottom" if val > 0 else "top",
            fontsize=7, fontweight="bold")

ax.set_ylabel("Stability margin (ms)")
ax.set_title("A. Stability margin", fontweight="bold", fontsize=9)
ax.set_ylim(min(margins) - 15, max(margins) + 15)

# Panel B: Time series comparison
ax = axes[1]

# Simulate at PHV conditions
tau_phv_s = tau_phv / 1000
tau_brace_s = tau_brace / 1000

t1, th1 = simulate_dde(tau_phv_s, duration=10.0, Kd_val=kd_phv, Kp_val=Kp)
t2, th2 = simulate_dde(tau_brace_s, duration=10.0, Kd_val=kd_brace, Kp_val=Kp)

# Clip for visualization (unstable case runs away; show the growth before saturation)
th1_deg = np.degrees(th1)
th2_deg = np.degrees(th2)
y_lim = 30  # degrees -- show up to 30 deg for clarity

ax.plot(t1, np.clip(th1_deg, -y_lim, y_lim), "-", color="#FF6B6B", lw=1.2,
        label="No brace", alpha=0.9)
ax.plot(t2, np.clip(th2_deg, -y_lim, y_lim), "-", color="#4DABF7", lw=1.2,
        label="With brace", alpha=0.9)
ax.axhline(0, color="gray", lw=0.5, ls="-", alpha=0.3)

# Clinical threshold
ax.axhline(10, color="orange", lw=0.7, ls="--", alpha=0.6)
ax.axhline(-10, color="orange", lw=0.7, ls="--", alpha=0.6)
ax.text(0.3, 12, "Cobb 10$^\\circ$", fontsize=6, color="orange", ha="left", va="bottom")

# Mark where no-brace exceeds clinical threshold
idx_exceed = np.where(np.abs(th1_deg) > 10)[0]
if len(idx_exceed) > 0:
    t_exceed = t1[idx_exceed[0]]
    ax.axvline(t_exceed, color="#FF6B6B", lw=0.5, ls=":", alpha=0.5)

ax.set_xlabel("Time (s)")
ax.set_ylabel("Spinal angle (degrees)")
ax.set_title("B. Simulated oscillation at PHV", fontweight="bold", fontsize=9)
ax.legend(loc="upper right", framealpha=0.9, edgecolor="none", fontsize=7)
ax.set_xlim(0, 10)
ax.set_ylim(-y_lim, y_lim)

fig.suptitle("Fig. 4: Brace as Haptic $K_d$ Augmentation", fontweight="bold",
             fontsize=10, y=1.02)

fig.savefig(os.path.join(OUT_DIR, "fig4_brace_mechanism.png"))
fig.savefig(os.path.join(OUT_DIR, "fig4_brace_mechanism.pdf"))
plt.close(fig)
print("  Saved fig4_brace_mechanism.png/pdf")


# ============================================================
# FIGURE 5: Model Overview Schematic (Block Diagram)
# ============================================================
print("Generating Figure 5: Model Overview Schematic...")

fig, ax = plt.subplots(figsize=(7.0, 3.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5)
ax.axis("off")

# Block style
box_kw = dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="black", linewidth=1.2)
growth_kw = dict(boxstyle="round,pad=0.2", facecolor="#FFF3BF", edgecolor="#F59F00",
                 linewidth=0.8)

# Blocks: positions (center_x, center_y)
blocks = {
    "ref":       (0.8, 2.5, "$\\theta_{ref}=0$\n(Upright)"),
    "sum":       (2.0, 2.5, "$\\Sigma$"),
    "brain":     (3.5, 2.5, "Brain\n(PID Controller)\n$K_p, K_d$"),
    "delay":     (5.2, 2.5, "Neural\nDelay $\\tau$"),
    "muscle":    (6.8, 2.5, "Muscles\n(Actuator)"),
    "spine":     (8.5, 2.5, "Spine\n(Inverted\nPendulum)"),
    "sensor":    (6.8, 0.8, "Proprioceptors\n(Sensors)"),
}

# Draw blocks
for key, (cx, cy, label) in blocks.items():
    if key == "sum":
        circle = plt.Circle((cx, cy), 0.25, facecolor="white", edgecolor="black", lw=1.2)
        ax.add_patch(circle)
        ax.text(cx, cy, label, ha="center", va="center", fontsize=9, fontweight="bold")
    else:
        w, h = (1.3, 0.8) if key != "ref" else (1.0, 0.6)
        if key in ["brain", "spine"]:
            w = 1.5
            h = 1.0
        rect = FancyBboxPatch((cx - w/2, cy - h/2), w, h, **box_kw)
        ax.add_patch(rect)
        ax.text(cx, cy, label, ha="center", va="center", fontsize=7,
                linespacing=1.2)

# Arrows: forward path
arrow_kw = dict(arrowstyle="-|>", color="black", lw=1.5, mutation_scale=12)

# ref -> sum
ax.annotate("", xy=(1.75, 2.5), xytext=(1.3, 2.5), arrowprops=arrow_kw)
# sum -> brain
ax.annotate("", xy=(2.75, 2.5), xytext=(2.25, 2.5), arrowprops=arrow_kw)
ax.text(2.5, 2.7, "$e(t)$", fontsize=7, ha="center", va="bottom", color="gray")
# brain -> delay
ax.annotate("", xy=(4.55, 2.5), xytext=(4.25, 2.5), arrowprops=arrow_kw)
ax.text(4.4, 2.7, "$u(t)$", fontsize=7, ha="center", va="bottom", color="gray")
# delay -> muscle
ax.annotate("", xy=(6.15, 2.5), xytext=(5.85, 2.5), arrowprops=arrow_kw)
ax.text(6.0, 2.7, "$u(t-\\tau)$", fontsize=7, ha="center", va="bottom", color="gray")
# muscle -> spine
ax.annotate("", xy=(7.75, 2.5), xytext=(7.45, 2.5), arrowprops=arrow_kw)
ax.text(7.6, 2.7, "Torque", fontsize=7, ha="center", va="bottom", color="gray")

# Output from spine
ax.annotate("", xy=(9.5, 2.5), xytext=(9.25, 2.5), arrowprops=arrow_kw)
ax.text(9.6, 2.5, "$\\theta(t)$", fontsize=8, ha="left", va="center")

# Feedback path: spine -> sensor -> sum
# spine down to sensor level
ax.annotate("", xy=(8.5, 1.2), xytext=(8.5, 2.0),
            arrowprops=dict(arrowstyle="-", color="black", lw=1.2))
ax.annotate("", xy=(7.45, 0.8), xytext=(8.5, 0.8),
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2, mutation_scale=10))
# sensor to sum (going left and up)
ax.annotate("", xy=(2.0, 0.8), xytext=(6.15, 0.8),
            arrowprops=dict(arrowstyle="-", color="black", lw=1.2))
ax.annotate("", xy=(2.0, 2.25), xytext=(2.0, 0.8),
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2, mutation_scale=10))

# Negative sign at sum
ax.text(1.75, 2.15, "$-$", fontsize=9, ha="center", va="center", fontweight="bold")

# Growth effects (yellow annotations)
# Growth affects Kd
growth_y = 4.2
ax.text(5.0, growth_y, "GROWTH EFFECTS", fontsize=8, fontweight="bold",
        ha="center", color="#E67700",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF3BF", edgecolor="#F59F00"))

# Arrow: growth -> brain (Kd degradation)
ax.annotate("$K_d$ degradation\n(recalibration lag)",
            xy=(3.5, 3.0), xytext=(3.5, 3.9),
            fontsize=6.5, color="#E67700", ha="center",
            arrowprops=dict(arrowstyle="-|>", color="#F59F00", lw=1.0))

# Arrow: growth -> delay (tau increase)
ax.annotate("$\\tau$ increase\n(longer limbs)",
            xy=(5.2, 3.0), xytext=(5.2, 3.9),
            fontsize=6.5, color="#E67700", ha="center",
            arrowprops=dict(arrowstyle="-|>", color="#F59F00", lw=1.0))

# Arrow: growth -> spine (mgl increase)
ax.annotate("$mgL$ increase\n(taller CoM)",
            xy=(8.5, 3.0), xytext=(8.0, 3.9),
            fontsize=6.5, color="#E67700", ha="center",
            arrowprops=dict(arrowstyle="-|>", color="#F59F00", lw=1.0))

# Brace annotation
ax.annotate("Brace: augments $K_d$\n(haptic feedback)",
            xy=(3.5, 2.0), xytext=(1.5, 1.2),
            fontsize=6.5, color="#1971C2", ha="center", fontstyle="italic",
            arrowprops=dict(arrowstyle="-|>", color="#1971C2", lw=0.8, ls="--"),
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#D0EBFF", edgecolor="#1971C2",
                      linewidth=0.6))

# Gravity label
ax.text(9.0, 1.5, "Gravity\n$mgL\\sin\\theta$", fontsize=6.5, ha="center",
        color="#868E96", fontstyle="italic")
ax.annotate("", xy=(8.5, 2.0), xytext=(9.0, 1.7),
            arrowprops=dict(arrowstyle="-|>", color="#868E96", lw=0.8, ls=":"))

ax.set_title("Fig. 5: Delayed PID Control Model of Spinal Balance",
             fontweight="bold", fontsize=10, pad=15)

fig.savefig(os.path.join(OUT_DIR, "fig5_model_schematic.png"))
fig.savefig(os.path.join(OUT_DIR, "fig5_model_schematic.pdf"))
plt.close(fig)
print("  Saved fig5_model_schematic.png/pdf")


# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("ALL 5 FIGURES GENERATED SUCCESSFULLY")
print("=" * 60)
print(f"Output directory: {OUT_DIR}")
for fname in sorted(os.listdir(OUT_DIR)):
    fpath = os.path.join(OUT_DIR, fname)
    size_kb = os.path.getsize(fpath) / 1024
    print(f"  {fname:45s} {size_kb:7.1f} KB")
