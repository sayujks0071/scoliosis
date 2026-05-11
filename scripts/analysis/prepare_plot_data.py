import pandas as pd

# Load data
df = pd.read_csv("outputs/thermodynamic_cost/phase_diagram_energy_deficit.csv")

# Select relevant columns
df_plot = df[["chi_kappa", "L", "R_deficit"]]

# Round to reduce size
df_plot = df_plot.round(4)

# Save to a new file
df_plot.to_csv("outputs/thermodynamic_cost/phase_diagram_energy_deficit_small.csv", index=False)
print("Saved simplified CSV.")
