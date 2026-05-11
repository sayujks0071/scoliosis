import os

import pandas as pd

# Create directory if not exists
os.makedirs("research/figures", exist_ok=True)

# Read data
df = pd.read_csv("outputs/parameter_map_results.csv")

# Filter for fixed boundary condition
df_fixed = df[df["boundary_condition"] == "fixed"].copy()

# Save to research/figures
df_fixed.to_csv("research/figures/stability_phase_data.csv", index=False)

print(f"Saved {len(df_fixed)} rows to research/figures/stability_phase_data.csv")
