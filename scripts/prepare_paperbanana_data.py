import pandas as pd


def downsample_data():
    input_path = "outputs/thermodynamic_cost/phase_diagram_energy_deficit.csv"
    output_path = "outputs/thermodynamic_cost/phase_diagram_energy_deficit_for_plot.csv"

    # Read original data
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: {input_path} not found.")
        return

    # Filter columns
    df_filtered = df[['chi_kappa', 'L', 'R_deficit']].copy()

    # Define boundary region: 0.8 <= R_deficit <= 1.2
    boundary_mask = (df_filtered['R_deficit'] >= 0.8) & (df_filtered['R_deficit'] <= 1.2)

    # Sample 10 points from the boundary region
    df_boundary = df_filtered[boundary_mask]
    if len(df_boundary) > 10:
        df_boundary = df_boundary.sample(n=10, random_state=42)

    # Sample 8 points from the rest (to show the global trend)
    df_rest = df_filtered[~boundary_mask]
    if len(df_rest) > 8:
        df_rest = df_rest.sample(n=8, random_state=42)

    # Combine and shuffle
    df_final = pd.concat([df_boundary, df_rest]).sample(frac=1, random_state=42).reset_index(drop=True)

    # Save to new CSV
    df_final.to_csv(output_path, index=False)
    print(f"Saved downsampled data to {output_path} with {len(df_final)} rows.")

if __name__ == "__main__":
    downsample_data()
