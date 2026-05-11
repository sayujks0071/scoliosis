import pandas as pd

# Load data
df = pd.read_csv("outputs/thermodynamic_cost/phase_diagram_energy_deficit.csv")

# Select relevant columns
df = df[["chi_kappa", "L", "R_deficit"]]

# Get unique values
chis = sorted(df.chi_kappa.unique())
Ls = sorted(df.L.unique())

# Subsample: Take every 2nd value
chis_small = chis[::2]
Ls_small = Ls[::2]

# Filter
df_small = df[df.chi_kappa.isin(chis_small) & df.L.isin(Ls_small)].copy()

# Round
df_small = df_small.round(4)

# Save
df_small.to_csv("outputs/thermodynamic_cost/phase_diagram_energy_deficit_tiny.csv", index=False)
print(f"Saved tiny CSV with {len(df_small)} rows.")
