import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

# Ensure output directory exists
os.makedirs('outputs/figures', exist_ok=True)

def main():
    # Load data
    df = pd.read_csv('data/species_parameters.csv')

    # Constants
    g = 9.81

    # Calculate Bg = EI / (M * g * L^2)
    df['Weight_N'] = df['Mass_kg'] * g
    df['Bg'] = df['EI_Nm2'] / (df['Weight_N'] * df['Length_m']**2)

    # Filter out Giraffe and Dolphin as per memory
    filtered_df = df[~df['Species'].isin(['Giraffe', 'Dolphin'])].copy()

    # Log-log regression
    x = np.log10(filtered_df['Mass_kg'])
    y = np.log10(filtered_df['Bg'])

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    print(f"Log-log regression: exponent (slope) = {slope:.3f}, R^2 = {r_value**2:.3f}, p = {p_value:.3e}")

    # Bootstrap resampling
    n_iterations = 10000
    n_size = len(filtered_df)
    boot_slopes = []

    # Set seed for reproducibility
    np.random.seed(42)

    for _ in range(n_iterations):
        indices = np.random.choice(range(n_size), size=n_size, replace=True)
        x_boot = x.iloc[indices]
        y_boot = y.iloc[indices]

        # Only compute regression if we have at least 2 distinct points
        if len(np.unique(x_boot)) > 1:
            m, _, _, _, _ = stats.linregress(x_boot, y_boot)
            boot_slopes.append(m)

    boot_slopes = np.array(boot_slopes)
    ci_lower = np.percentile(boot_slopes, 2.5)
    ci_upper = np.percentile(boot_slopes, 97.5)

    print(f"Bootstrap 95% CI for exponent: [{ci_lower:.3f}, {ci_upper:.3f}]")

    # The rest of the original script (Ke calculation, plotting)
    human_adult = df[df['Species'] == 'Human_Adult'].iloc[0]
    supply_ref = human_adult['Mass_kg']**0.75
    demand_ref = human_adult['Length_m']**4

    df['Supply_Index'] = df['Mass_kg']**0.75 / supply_ref
    df['Demand_Index'] = df['Length_m']**4 / demand_ref
    df['Ke'] = df['Supply_Index'] / df['Demand_Index']

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {'Quadruped': 'blue', 'Biped': 'red', 'Facultative_Biped': 'orange', 'Aquatic': 'cyan'}
    markers = {'Quadruped': 'o', 'Biped': '^', 'Facultative_Biped': 's', 'Aquatic': 'D'}

    for i, row in df.iterrows():
        posture = row['Posture']
        color = colors.get(posture, 'gray')
        marker = markers.get(posture, 'o')

        ax.scatter(row['Mass_kg'], row['Bg'], c=color, marker=marker, s=150,
                   label=posture if posture not in ax.get_legend_handles_labels()[1] else "")
        ax.annotate(row['Species'], (row['Mass_kg'], row['Bg']), xytext=(5, 5), textcoords='offset points', fontsize=9)

    # Plot regression line
    x_line = np.linspace(df['Mass_kg'].min(), df['Mass_kg'].max(), 100)
    y_line = (10**intercept) * (x_line**slope)
    ax.plot(x_line, y_line, 'k--', label=f'Fit: Bg ~ M^{slope:.3f}')

    ax.axhline(y=0.1, color='r', linestyle='--', label='Critical Stability Threshold')
    ax.fill_between(df['Mass_kg'], 0, 0.1, color='red', alpha=0.1, label='Unstable / Metabolic Buckling Zone')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Body Mass (kg)')
    ax.set_ylabel('Bio-Gravitational Number (Bg)')
    ax.set_title('Cross-Species Scaling: The Allometric Trap')
    ax.grid(True, which="both", ls="-", alpha=0.2)
    ax.legend()

    plt.tight_layout()
    plt.savefig('outputs/figures/cross_species_scaling.png')
    print("Figure saved to outputs/figures/cross_species_scaling.png")

if __name__ == "__main__":
    main()
