import numpy as np
import pandas as pd
import scipy.stats as stats
import os

os.makedirs('outputs/figures', exist_ok=True)

def calc_bic(y, y_pred, k):
    n = len(y)
    rss = np.sum((y - y_pred)**2)
    # BIC = n * ln(RSS/n) + k * ln(n)
    return n * np.log(rss / n) + k * np.log(n)

def main():
    # Load data
    df = pd.read_csv('data/species_parameters.csv')
    g = 9.81
    df['Weight_N'] = df['Mass_kg'] * g
    df['Bg'] = df['EI_Nm2'] / (df['Weight_N'] * df['Length_m']**2)
    filtered_df = df[~df['Species'].isin(['Giraffe', 'Dolphin'])].copy()

    log_M = np.log10(filtered_df['Mass_kg'].values)
    log_Bg = np.log10(filtered_df['Bg'].values)

    # Model 1: Allometric Scaling (Bg ~ Mass^slope) -> log_Bg = a + b*log_M
    slope, intercept, _, _, _ = stats.linregress(log_M, log_Bg)
    y_pred_allometric = intercept + slope * log_M
    # Parameters: intercept, slope, variance (k=3)
    bic_allometric = calc_bic(log_Bg, y_pred_allometric, k=3)

    # Model 2: Constant (Bg ~ constant) -> log_Bg = a
    mean_log_Bg = np.mean(log_Bg)
    y_pred_constant = np.full_like(log_Bg, mean_log_Bg)
    # Parameters: mean, variance (k=2)
    bic_constant = calc_bic(log_Bg, y_pred_constant, k=2)

    delta_bic = bic_constant - bic_allometric
    # Bayes Factor approximation: BF = exp(Delta BIC / 2)
    bf = np.exp(delta_bic / 2)

    print(f"Allometric Model BIC: {bic_allometric:.2f}")
    print(f"Constant Model BIC: {bic_constant:.2f}")
    print(f"Delta BIC: {delta_bic:.2f}")
    print(f"Approximate Bayes Factor (Allometric over Constant): {bf:.2e}")

    results_df = pd.DataFrame({
        'Model': ['Allometric (Bg ~ M^slope)', 'Constant (Bg ~ const)'],
        'BIC': [bic_allometric, bic_constant],
        'Delta_BIC': [0, delta_bic],
        'Bayes_Factor': [1, 1/bf]
    })
    results_df.to_csv('outputs/figures/bayesian_model_comparison.csv', index=False)
    print("Results saved to outputs/figures/bayesian_model_comparison.csv")

if __name__ == "__main__":
    main()
