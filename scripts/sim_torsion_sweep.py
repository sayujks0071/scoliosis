import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from spinalmodes.countercurvature.pyelastica_bridge import run_protein_simulation
except ImportError as e:
    print(f"Error importing simulation module: {e}")
    sys.exit(1)

def run_sweep():
    # Setup parameters
    torsion_values = np.linspace(0.0, 2.0, 21)
    results = []

    out_dir = Path("outputs/sim/2026-03-11")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Torsion Drive Sweep (N={len(torsion_values)})...")

    for i, t in enumerate(torsion_values):
        print(f"[{i+1}/{len(torsion_values)}] Simulating Torsion Drive = {t:.2f}...")
        res = run_protein_simulation(
            anisotropy=3.0,
            active_curvature=12.0,
            torsion_drive=float(t),
            initial_lateral_defect=0.05,
            duration=2.0,
            n_elements=50,
            dt=1e-4,
            show_progress=False
        )
        if res.get("success"):
            cobb = res.get("cobb_angle", 0.0)
            s_lat = res.get("S_lat", 0.0)
            print(f"  -> Cobb: {cobb:.2f} deg, S_lat: {s_lat:.4f}")
            results.append({
                "torsion_drive": t,
                "cobb_angle": cobb,
                "s_lat": s_lat,
                "max_curvature": res.get("max_curvature", 0.0),
                "max_torsion": res.get("max_torsion", 0.0)
            })
        else:
            print(f"  -> Failed: {res.get('error')}")

    # Save Results
    df = pd.DataFrame(results)
    df.to_csv(out_dir / "results.csv", index=False)
    print(f"Saved results to {out_dir / 'results.csv'}")

    # Save Params
    pd.DataFrame([{
        "t_min": torsion_values[0],
        "t_max": torsion_values[-1],
        "steps": len(torsion_values),
        "anisotropy": 3.0,
        "active_curvature": 12.0,
        "initial_lateral_defect": 0.05,
        "duration": 2.0,
        "n_elements": 50,
        "dt": 1e-4
    }]).to_csv(out_dir / "params.csv", index=False)
    print(f"Saved params to {out_dir / 'params.csv'}")

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['torsion_drive'], df['cobb_angle'], 'o-', linewidth=2, color='blue')
    plt.xlabel('Torsion Drive')
    plt.ylabel('Cobb Angle (degrees)')
    plt.title('Effect of Torsion Drive on Cobb Angle\n(Anisotropy=3.0, Active Growth=12.0)')
    plt.grid(True, alpha=0.3)

    plot_path = out_dir / "plot_torsion_cobb.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path}")

if __name__ == "__main__":
    run_sweep()
