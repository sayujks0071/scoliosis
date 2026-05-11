#!/usr/bin/env python3
"""
AlphaFold-to-DDE Pipeline v2: Fixed critical_delay() using Phase 3's
validated analytical_hopf_boundary algorithm.

Modules A-C are unchanged (AlphaFold download, pLDDT extraction, parameter mapping).
The integrated analysis now uses the correct Hopf bifurcation solver.
"""

import numpy as np
import json, os, warnings
from pathlib import Path

warnings.filterwarnings("ignore")

OUT = Path("/sessions/gracious-relaxed-dirac/mnt/life/results")
FIG = Path("/sessions/gracious-relaxed-dirac/mnt/life/figures_alphafold")
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

# ─── Fixed Hopf boundary solver (from validated Phase 3) ──────────────
def analytical_hopf_boundary(Kp, Kd, b=1.0, I=0.8, mgL=73.575):
    """
    Correct Hopf bifurcation boundary for the DDE:
      I*θ̈ + b*θ̇ − mgL*θ + Kp*θ(t−τ) + Kd*θ̇(t−τ) = 0

    At Hopf: s = jω, so the char. eq. becomes:
      Real: −Iω² − mgL + Kp·cos(ωτ) + Kd·ω·sin(ωτ) = 0
      Imag: bω − Kp·sin(ωτ) + Kd·ω·cos(ωτ) = 0

    Modulus condition: Kp² + (Kd·ω)² = (bω)² + (Iω² + mgL)²
    Phase gives τ via arctan2.
    """
    omega = np.linspace(0.5, 60, 6000)

    # Vectorized computation of lhs and rhs
    lhs = Kp**2 + (Kd * omega)**2
    rhs = (b * omega)**2 + (I * omega**2 + mgL)**2
    max_val = np.maximum(lhs, rhs)
    max_val = np.maximum(max_val, 1e-12)

    # Check modulus condition vectorized, avoiding a slow 6000-iteration python loop
    mask = np.abs(lhs - rhs) / max_val < 0.002
    valid_omegas = omega[mask]

    best_tau = None
    best_residual = np.inf

    for w in valid_omegas:
        A = I * w**2 + mgL
        B = b * w
        denom = Kp**2 + (Kd * w)**2
        cos_wt = (A * Kp - B * Kd * w) / denom
        sin_wt = (A * Kd * w + B * Kp) / denom
        if abs(cos_wt) <= 1.01 and abs(sin_wt) <= 1.01:
            cos_wt = np.clip(cos_wt, -1, 1)
            sin_wt = np.clip(sin_wt, -1, 1)
            wt = np.arctan2(sin_wt, cos_wt)
            if wt < 0:
                wt += 2 * np.pi
            tau_c = wt / w
            if 0.001 < tau_c < 0.5:
                # Verify residual
                r_real = -I*w**2 - mgL + Kp*np.cos(w*tau_c) + Kd*w*np.sin(w*tau_c)
                r_imag = b*w - Kp*np.sin(w*tau_c) + Kd*w*np.cos(w*tau_c)
                residual = r_real**2 + r_imag**2
                if residual < best_residual:
                    best_residual = residual
                    best_tau = tau_c
    return best_tau if best_tau else 0.0


def simulate_dde(Kp, Kd, tau, duration=8.0, dt=0.002, b=1.0, I=0.8,
                 mgL=73.575, theta0=0.05, noise_std=0.0):
    """Minimal DDE simulator: I*θ̈ + b*θ̇ − mgL*θ + Kp*θ(t-τ) + Kd*θ̇(t-τ) = ξ"""
    delay_steps = max(1, int(tau / dt))
    N = int(duration / dt)
    theta = np.zeros(N)
    omega = np.zeros(N)
    theta[0] = theta0

    AMP_CAP = 50.0  # Radians cap to prevent overflow

    for i in range(1, N):
        j = max(0, i - delay_steps)
        accel = (-b * omega[i-1] + mgL * theta[i-1]
                 - Kp * theta[j] - Kd * omega[j]) / I
        if noise_std > 0:
            accel += np.random.normal(0, noise_std)
        omega[i] = omega[i-1] + accel * dt
        theta[i] = theta[i-1] + omega[i] * dt
        if abs(theta[i]) > AMP_CAP:
            theta[i:] = AMP_CAP * np.sign(theta[i])
            omega[i:] = 0
            break

    return np.linspace(0, duration, N), np.degrees(theta)


# ─── AlphaFold structure parser ────────────────────────────────────────
def download_alphafold_pdb(uniprot_id, cache_dir="/sessions/gracious-relaxed-dirac/af_cache"):
    os.makedirs(cache_dir, exist_ok=True)
    path = f"{cache_dir}/{uniprot_id}.pdb"
    if os.path.exists(path):
        return path
    import requests
    url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        for ver in ["v6", "v3"]:
            for frag in ["", "-3"]:
                url2 = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}{frag}-F1-model_{ver}.pdb"
                r = requests.get(url2, timeout=30)
                if r.status_code == 200:
                    break
            if r.status_code == 200:
                break
    if r.status_code != 200:
        return None
    with open(path, "w") as f:
        f.write(r.text)
    return path


def parse_pdb_plddt(pdb_path):
    plddts = {}
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                resnum = int(line[22:26].strip())
                bfactor = float(line[60:66].strip())
                plddts[resnum] = bfactor
    return plddts


def flexibility_index(plddts, domain_start=None, domain_end=None):
    residues = sorted(plddts.keys())
    if domain_start and domain_end:
        residues = [r for r in residues if domain_start <= r <= domain_end]
    if not residues:
        return 0.5
    scores = [plddts[r] for r in residues]
    return 1.0 - np.mean(scores) / 100.0


def disorder_fraction(plddts, threshold=50.0, domain_start=None, domain_end=None):
    residues = sorted(plddts.keys())
    if domain_start and domain_end:
        residues = [r for r in residues if domain_start <= r <= domain_end]
    if not residues:
        return 0.0
    return sum(1 for r in residues if plddts[r] < threshold) / len(residues)


# ═══════════════════════════════════════════════════════════════════════
# MODULE A: STRUCTURAL PROTEINS → STIFFNESS
# ═══════════════════════════════════════════════════════════════════════
print("=" * 70)
print("MODULE A: Structural Proteins → Passive Stiffness Parameters")
print("=" * 70)

structural_proteins = {
    "COL1A1": {"uniprot": "P02452", "role": "bone_matrix",
               "triple_helix": (170, 1200),
               "description": "Type I collagen α1 – vertebral bone matrix"},
    "COL2A1": {"uniprot": "P02458", "role": "disc_cartilage",
               "triple_helix": (200, 1200),
               "description": "Type II collagen α1 – disc/cartilage matrix"},
}

structural_results = {}
for name, info in structural_proteins.items():
    pdb_path = download_alphafold_pdb(info["uniprot"])
    if not pdb_path:
        print(f"  {name}: AlphaFold structure not available")
        continue
    plddts = parse_pdb_plddt(pdb_path)
    n_res = len(plddts)
    ds, de = info["triple_helix"]
    de = min(de, max(plddts.keys()))
    flex = flexibility_index(plddts, ds, de)
    dis_frac = disorder_fraction(plddts, 50, ds, de)
    overall_flex = flexibility_index(plddts)
    mean_plddt = np.mean([plddts[r] for r in plddts])

    structural_results[name] = {
        "n_residues": n_res,
        "mean_plddt": round(float(mean_plddt), 1),
        "domain": f"triple-helix ({ds}-{de})",
        "domain_flexibility": round(float(flex), 4),
        "disorder_fraction": round(float(dis_frac), 4),
        "overall_flexibility": round(float(overall_flex), 4),
    }
    print(f"\n  {name} ({info['description']})")
    print(f"    Residues: {n_res}, Mean pLDDT: {mean_plddt:.1f}")
    print(f"    Domain [{ds}-{de}]: flexibility={flex:.4f}, disorder={dis_frac:.1%}")

col1_flex = structural_results.get("COL1A1", {}).get("domain_flexibility", 0.15)
col2_flex = structural_results.get("COL2A1", {}).get("domain_flexibility", 0.15)
combined_flex = 0.4 * col1_flex + 0.6 * col2_flex
b_molecular = 1.0 * (1.0 - 0.5 * combined_flex)

print(f"\n  → Combined collagen flexibility: {combined_flex:.4f}")
print(f"    Molecular-adjusted damping: b = {b_molecular:.3f} (baseline: 1.000)")

structural_results["parameter_mapping"] = {
    "combined_flexibility": round(float(combined_flex), 4),
    "b_baseline": 1.0,
    "b_molecular": round(float(b_molecular), 3),
    "mapping": "b = b0 × (1 - 0.5 × flex_combined)"
}

# ═══════════════════════════════════════════════════════════════════════
# MODULE B: RECEPTOR PROTEINS → DELAY (τ)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("MODULE B: Receptor Proteins → Sensorimotor Delay (τ)")
print("=" * 70)

receptor_proteins = {
    "PIEZO2": {"uniprot": "Q9H5I5", "role": "mechanoreceptor",
               "gate_domain": (1, 400),
               "description": "Mechanosensitive ion channel – proprioceptive transduction"},
    "GPR126": {"uniprot": "Q86SQ4", "role": "adhesion_gpcr",
               "signaling_domain": (800, 1221),
               "description": "Adhesion GPCR G6 – cartilage/disc signaling"},
    "MTNR1B": {"uniprot": "P49286", "role": "melatonin_receptor",
               "binding_domain": (30, 300),
               "description": "Melatonin receptor 1B – circadian/growth regulation"},
}

receptor_results = {}
for name, info in receptor_proteins.items():
    pdb_path = download_alphafold_pdb(info["uniprot"])
    if not pdb_path:
        continue
    plddts = parse_pdb_plddt(pdb_path)
    n_res = len(plddts)
    domain_key = [k for k in info.keys() if k.endswith("_domain")][0]
    ds, de = info[domain_key]
    de = min(de, max(plddts.keys()))
    func_flex = flexibility_index(plddts, ds, de)
    func_disorder = disorder_fraction(plddts, 50, ds, de)
    overall_flex = flexibility_index(plddts)
    mean_plddt = np.mean([plddts[r] for r in plddts])

    receptor_results[name] = {
        "n_residues": n_res,
        "mean_plddt": round(float(mean_plddt), 1),
        "functional_domain": f"{ds}-{de}",
        "domain_flexibility": round(float(func_flex), 4),
        "domain_disorder": round(float(func_disorder), 4),
        "overall_flexibility": round(float(overall_flex), 4),
    }
    print(f"\n  {name} ({info['description']})")
    print(f"    Residues: {n_res}, Mean pLDDT: {mean_plddt:.1f}")
    print(f"    Functional domain [{ds}-{de}]: flex={func_flex:.4f}")

piezo2_flex = receptor_results.get("PIEZO2", {}).get("domain_flexibility", 0.3)
gpr126_flex = receptor_results.get("GPR126", {}).get("domain_flexibility", 0.3)
mtnr1b_flex = receptor_results.get("MTNR1B", {}).get("domain_flexibility", 0.3)

tau_proprio = 0.025 * (1 + 2.0 * piezo2_flex)
tau_tissue = 0.030 * (1 + 1.5 * gpr126_flex)
tau_growth = 0.015 * (1 + 1.0 * mtnr1b_flex)
tau_molecular = tau_proprio + tau_tissue + tau_growth

print(f"\n  → Delay decomposition:")
print(f"    τ_proprioceptive (PIEZO2): {tau_proprio*1000:.1f} ms")
print(f"    τ_tissue_remodel (GPR126): {tau_tissue*1000:.1f} ms")
print(f"    τ_growth_timing (MTNR1B):  {tau_growth*1000:.1f} ms")
print(f"    τ_eff (molecular sum):     {tau_molecular*1000:.1f} ms")

receptor_results["delay_decomposition"] = {
    "tau_proprioceptive_ms": round(tau_proprio * 1000, 1),
    "tau_tissue_remodel_ms": round(tau_tissue * 1000, 1),
    "tau_growth_timing_ms": round(tau_growth * 1000, 1),
    "tau_eff_ms": round(tau_molecular * 1000, 1),
    "mapping": "τ_i = τ_base_i × (1 + α_i × flex_i)"
}

# ═══════════════════════════════════════════════════════════════════════
# MODULE C: AIS-RISK VARIANTS → PATIENT-SPECIFIC PARAMETERS
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("MODULE C: AIS-Risk Variants → Patient-Specific DDE Parameters")
print("=" * 70)

ais_genes = {
    "LBX1": {"uniprot": "Q9UPV0", "role": "neuronal_determination",
             "functional_domain": (1, 300), "dde_target": "Kd",
             "description": "Ladybird homeobox 1 – somatosensory relay neuron fate"},
    "PAX1": {"uniprot": "P15863", "role": "vertebral_development",
             "functional_domain": (20, 150), "dde_target": "mgL",
             "description": "Paired box 1 – vertebral column patterning"},
}

variant_results = {}
for name, info in ais_genes.items():
    pdb_path = download_alphafold_pdb(info["uniprot"])
    if not pdb_path:
        continue
    plddts = parse_pdb_plddt(pdb_path)
    n_res = len(plddts)
    ds, de = info["functional_domain"]
    de = min(de, max(plddts.keys()))
    func_flex = flexibility_index(plddts, ds, de)
    func_disorder = disorder_fraction(plddts, 70, ds, de)
    mean_plddt = np.mean([plddts[r] for r in plddts])
    variant_perturbation = 0.2 * (1 + func_flex)

    variant_results[name] = {
        "n_residues": n_res,
        "mean_plddt": round(float(mean_plddt), 1),
        "functional_domain": f"{ds}-{de}",
        "domain_flexibility": round(float(func_flex), 4),
        "domain_disorder_70": round(float(func_disorder), 4),
        "variant_perturbation": round(float(variant_perturbation), 4),
        "dde_target": info["dde_target"],
    }
    print(f"\n  {name} ({info['description']})")
    print(f"    Residues: {n_res}, Mean pLDDT: {mean_plddt:.1f}")
    print(f"    Functional domain [{ds}-{de}]: flex={func_flex:.4f}")
    print(f"    Variant perturbation: {variant_perturbation:.1%}, target: {info['dde_target']}")

# ═══════════════════════════════════════════════════════════════════════
# INTEGRATED SIMULATION (with corrected Hopf boundary)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("INTEGRATED ANALYSIS: Molecular-Parameterised DDE Stability")
print("(Using corrected analytical_hopf_boundary)")
print("=" * 70)

lbx1_perturb = variant_results.get("LBX1", {}).get("variant_perturbation", 0.2)
pax1_perturb = variant_results.get("PAX1", {}).get("variant_perturbation", 0.15)

scenarios = {
    "Baseline (default params)": {
        "Kp": 120, "Kd": 10, "tau": 0.070, "b": 1.0, "mgL": 73.575
    },
    "Molecular-adjusted (AlphaFold)": {
        "Kp": 120, "Kd": 10, "tau": tau_molecular,
        "b": b_molecular, "mgL": 73.575
    },
    "LBX1 risk variant": {
        "Kp": 120,
        "Kd": 10 * (1 + lbx1_perturb),
        "tau": tau_molecular * 1.1,
        "b": b_molecular, "mgL": 73.575
    },
    "PAX1 risk variant": {
        "Kp": 120, "Kd": 10,
        "tau": tau_molecular,
        "b": b_molecular,
        "mgL": 73.575 * (1 + pax1_perturb)
    },
    "Combined risk (LBX1 + PAX1)": {
        "Kp": 120,
        "Kd": 10 * (1 + lbx1_perturb),
        "tau": tau_molecular * 1.15,
        "b": b_molecular * 0.9,
        "mgL": 73.575 * (1 + pax1_perturb)
    },
    "FBN1 (Marfan-type)": {
        "Kp": 120, "Kd": 10,
        "tau": tau_molecular * 1.05,
        "b": b_molecular * 0.7,
        "mgL": 73.575 * 1.15
    },
}

# Verify the Hopf solver on the baseline first
baseline_tc = analytical_hopf_boundary(120, 10, 1.0, 0.8, 73.575)
print(f"\n  Validation: Baseline τ* = {baseline_tc*1000:.1f} ms (expected ~80-92ms from Phase 3)")

sim_results = {}
print(f"\n  {'Scenario':<35} {'Kd':>5} {'τ(ms)':>6} {'b':>5} {'mgL':>7} {'τ*(ms)':>7} {'Margin':>7} {'Status':>10}")
print("  " + "-" * 92)

for name, params in scenarios.items():
    tc = analytical_hopf_boundary(params["Kp"], params["Kd"], params["b"], 0.8, params["mgL"])
    is_stable = params["tau"] < tc if tc > 0 else False
    margin_ms = (tc - params["tau"]) * 1000 if tc > 0 else float('-inf')

    # Simulate trajectory
    t, theta = simulate_dde(params["Kp"], params["Kd"], params["tau"],
                            duration=10.0, dt=0.002, b=params["b"], mgL=params["mgL"])
    max_amp = float(np.max(np.abs(theta)))

    sim_results[name] = {
        "params": {k: round(float(v), 4) for k, v in params.items()},
        "tau_star_ms": round(float(tc * 1000), 1) if tc else 0,
        "stable": bool(is_stable),
        "stability_margin_ms": round(float(margin_ms), 1) if tc else None,
        "max_amplitude_deg": round(max_amp, 2),
        "t": t.tolist()[::50],
        "theta": theta.tolist()[::50],
    }

    stability = "✓ STABLE" if is_stable else "✗ UNSTABLE"
    print(f"  {name:<35} {params['Kd']:>5.1f} {params['tau']*1000:>6.1f} {params['b']:>5.3f} "
          f"{params['mgL']:>7.3f} {tc*1000:>7.1f} {margin_ms:>+7.1f} {stability:>10}")

# ─── Growth-spurt vulnerability analysis ─────────────────────────────
print("\n  → Growth-Spurt Vulnerability (τ sweep 40-140ms):")
tau_sweep = np.linspace(0.040, 0.140, 50)
vulnerability = {}

for sname in ["Baseline (default params)", "Molecular-adjusted (AlphaFold)",
              "LBX1 risk variant", "Combined risk (LBX1 + PAX1)", "FBN1 (Marfan-type)"]:
    p = scenarios[sname]
    tc = analytical_hopf_boundary(p["Kp"], p["Kd"], p["b"], 0.8, p["mgL"])
    amps = []
    for tau_val in tau_sweep:
        _, theta = simulate_dde(p["Kp"], p["Kd"], tau_val, 10.0, 0.002, p["b"], mgL=p["mgL"])
        amps.append(float(np.max(np.abs(theta))))
    vulnerability[sname] = {
        "tau_ms": [round(t*1000, 1) for t in tau_sweep],
        "max_amp_deg": [round(a, 2) for a in amps],
        "tau_star_ms": round(tc * 1000, 1) if tc else 0,
    }
    # 10° threshold
    threshold_tau = next((tau_sweep[i]*1000 for i, a in enumerate(amps) if a > 10), None)
    tc_str = f"{tc*1000:.1f}ms" if tc else "N/A"
    if threshold_tau:
        print(f"    {sname:<35} τ*={tc_str}  10°-threshold: {threshold_tau:.1f}ms")
    else:
        print(f"    {sname:<35} τ*={tc_str}  10°-threshold: >140ms")

# ─── K_d sensitivity at molecular τ ──────────────────────────────────
print("\n  → Derivative Gain Trap at molecular delay:")
kd_sweep = np.linspace(2, 30, 30)
kd_sensitivity = {}

for b_val, label in [(1.0, "healthy"), (b_molecular, "molecular")]:
    tau_stars = []
    for kd in kd_sweep:
        tc = analytical_hopf_boundary(120, kd, b_val, 0.8, 73.575)
        tau_stars.append(round(tc * 1000, 1) if tc else 0)
    kd_sensitivity[label] = {
        "Kd": [round(float(k), 1) for k in kd_sweep],
        "tau_star_ms": tau_stars,
        "b": b_val,
    }
    # Find optimal Kd
    best_idx = np.argmax(tau_stars)
    print(f"    b={b_val:.3f} ({label}): optimal Kd={kd_sweep[best_idx]:.1f}, max τ*={tau_stars[best_idx]:.1f}ms")

# ═══════════════════════════════════════════════════════════════════════
# SAVE CORRECTED RESULTS
# ═══════════════════════════════════════════════════════════════════════
all_results = {
    "module_a_structural": structural_results,
    "module_b_receptors": receptor_results,
    "module_c_variants": variant_results,
    "integrated_scenarios": {k: {kk: vv for kk, vv in v.items() if kk not in ('t', 'theta')}
                            for k, v in sim_results.items()},
    "vulnerability_analysis": vulnerability,
    "kd_sensitivity": kd_sensitivity,
    "trajectory_data": {k: {"t": v["t"], "theta": v["theta"]} for k, v in sim_results.items()},
}

with open(OUT / "alphafold_molecular_results.json", "w") as f:
    json.dump(all_results, f, indent=2)

print(f"\n✓ Corrected results saved to {OUT / 'alphafold_molecular_results.json'}")
print("✓ Pipeline v2 complete.")
