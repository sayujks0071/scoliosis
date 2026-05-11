import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Load data
df = pd.read_csv("outputs/thermodynamic_cost/phase_diagram_energy_deficit.csv")

# Pivot for heatmap
heatmap_data = df.pivot(index="L", columns="chi_kappa", values="R_deficit")

# Plot
plt.figure(figsize=(10, 8))
sns.heatmap(
    heatmap_data,
    cmap="inferno",
    vmin=0,
    vmax=2,
    cbar_kws={"label": "Energy Deficit Ratio ($R_{deficit}$)"},
)

# Invert Y axis so L increases upwards
plt.gca().invert_yaxis()

plt.title('Energy Deficit Phase Diagram: The "Danger Zone"', fontsize=16)
plt.ylabel("Spinal Length $L$ (Growth)", fontsize=14)
plt.xlabel(r"Coupling Strength $\chi_\kappa$", fontsize=14)

# Highlight Danger Zone
plt.text(
    0.5,
    0.9,
    "Danger Zone ($R > 1$)",
    transform=plt.gca().transAxes,
    color="white",
    ha="center",
    fontsize=12,
    fontweight="bold",
)

plt.tight_layout()
plt.savefig("research/figures/energy_phase_danger_zone.png", dpi=300)
print("Plot saved to research/figures/energy_phase_danger_zone.png")
