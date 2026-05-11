import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.spinalmodes.countercurvature.pyelastica_bridge import run_protein_simulation

def main():
    # Setup output directory
    out_dir = Path("outputs/sim/2026-03-09")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Parameter sweep configuration
    anisotropy = 2.0
    torsion_drive = 0.5
    active_curvatures = np.linspace(5.0, 25.0, 15)

    # Store results
    results = []

    print(f"Running parameter sweep over active_curvature with anisotropy={anisotropy}, torsion_drive={torsion_drive}")

    for ac in active_curvatures:
        print(f"  Running active_curvature={ac:.2f}...")
        res = run_protein_simulation(
            anisotropy=anisotropy,
            active_curvature=ac,
            torsion_drive=torsion_drive,
            duration=2.0,
            show_progress=False
        )
        res["active_curvature"] = ac
        results.append(res)

    df = pd.DataFrame(results)

    # Save results and params
    df.to_csv(out_dir / "results.csv", index=False)

    params_df = pd.DataFrame({
        "parameter": ["anisotropy", "torsion_drive", "duration", "n_elements"],
        "value": [anisotropy, torsion_drive, 2.0, 50]
    })
    params_df.to_csv(out_dir / "params.csv", index=False)

    # Plotting
    plt.figure(figsize=(10, 6))

    # Plot Cobb Angle vs Active Curvature
    plt.plot(df["active_curvature"], df["cobb_angle"], 'bo-', linewidth=2, label="Cobb Angle (deg)")
    plt.xlabel("Active Curvature")
    plt.ylabel("Cobb Angle (deg)")
    plt.title(f"Scoliosis Emergence vs Active Curvature\n(Anisotropy={anisotropy}, Torsion Drive={torsion_drive})")
    plt.grid(True)

    # Highlight critical threshold if exists
    max_cobb = df["cobb_angle"].max()
    if max_cobb > 10:
        critical_idx = df["cobb_angle"] > 10
        if critical_idx.any():
            crit_ac = df.loc[critical_idx, "active_curvature"].iloc[0]
            plt.axvline(x=crit_ac, color='r', linestyle='--', label=f"Critical Threshold (~{crit_ac:.1f})")

    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "plot_active_curvature.png")
    plt.close()

    print(f"Sweep complete. Results saved to {out_dir}")

if __name__ == "__main__":
    main()