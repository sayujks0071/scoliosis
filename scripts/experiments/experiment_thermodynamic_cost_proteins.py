#!/usr/bin/env python3
"""
Thermodynamic Cost of Countercurvature: Protein Structural Analysis
====================================================================

Maps the three terms of the free energy dissipation functional (Eq. dissipation)
to specific molecular players using pre-computed AlphaFold structural metrics.

  F_dot = integral[ eta_p |dkappa/dt|^2 + eta_a (kappa - kappa_passive)^2 + Gamma_m(s) ] ds

  eta_p  : Proprioceptive feedback cost (sensing + neural processing)
  eta_a  : Active moment maintenance (tonic muscle contraction)
  Gamma_m: Basal tissue maintenance (matrix turnover, hormonal, circadian)

Uses pre-computed AFCC metrics from outputs/afcc/ (AlphaFold structures already
fetched and analyzed by the AFCC pipeline).

Author: Dr. Sayuj Krishnan S
Date: 2026-02-07
"""

import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("outputs/thermodynamic_cost")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Directories containing pre-computed AFCC metrics
METRICS_DIRS = [
    Path("outputs/afcc"),
    Path("research/alphafold_countercurvature/outputs/afcc"),
]

@dataclass
class ProteinTarget:
    gene: str
    uniprot: str
    term: str           # "eta_p", "eta_a", "Gamma_m"
    role: str
    prediction: str
    scaling: str        # How cost scales with spinal length L

# ---------------------------------------------------------------------------
# The Three Terms: Protein Targets
# ---------------------------------------------------------------------------

TARGETS: List[ProteinTarget] = [
    # ===== eta_p: Proprioceptive feedback dissipation =====
    ProteinTarget(
        gene="PIEZO2", uniprot="Q9H5I5", term="eta_p",
        role="Vector mechanosensor for proprioception; detects alignment error",
        prediction="High anisotropy (extended) = high metabolic cost to maintain orientation; "
                   "channel density must scale with L during growth spurt",
        scaling="L (sensor density per unit length)"
    ),
    ProteinTarget(
        gene="EGR3", uniprot="Q06889", term="eta_p",
        role="Transcription factor maintaining muscle spindle innervation",
        prediction="Extended structure despite being a TF; high disorder = energetically "
                   "costly to fold; EGR3 expression must scale with L for spindle density",
        scaling="L (innervation per segment)"
    ),
    ProteinTarget(
        gene="RUNX3", uniprot="Q13761", term="eta_p",
        role="Master regulator of proprioceptive neuron development",
        prediction="Intermediate anisotropy, high disorder (56%); its expression level sets "
                   "the proprioceptive gain; insufficient scaling during growth = reduced correction",
        scaling="L (proprioceptive neuron count)"
    ),
    ProteinTarget(
        gene="NTRK3", uniprot="Q16288", term="eta_p",
        role="TrkC receptor; proprioceptive neuron survival signal",
        prediction="Intermediate anisotropy, 9 hinge candidates = conformationally expensive; "
                   "NT-3/TrkC signaling cost scales with spinal length",
        scaling="L (afferent neuron count)"
    ),
    ProteinTarget(
        gene="PIEZO1", uniprot="Q92508", term="eta_p",
        role="Scalar mechanosensor; detects membrane tension (buckling threshold)",
        prediction="Extended (3.9 aniso), massive (2521 res); scalar complement to PIEZO2; "
                   "sets the stiffness floor below which buckling occurs",
        scaling="L^2 (membrane area)"
    ),

    # ===== eta_a: Active moment maintenance =====
    ProteinTarget(
        gene="DMD", uniprot="P11532", term="eta_a",
        role="Dystrophin; cytoskeleton-ECM linker in paraspinal muscle",
        prediction="Essential for maintenance of muscle tone against gravity; loss leads to collapse; "
                   "connects contractile force to the load-bearing ECM.",
        scaling="L^3 (muscle volume)"
    ),
    ProteinTarget(
        gene="MYLK", uniprot="Q15746", term="eta_a",
        role="Myosin light chain kinase; tonic contraction regulator",
        prediction="Regulator of myosin contractility; sets the gain of the active moment; "
                   "failure leads to inability to sustain postural tone.",
        scaling="L^2 (contractile force)"
    ),
    ProteinTarget(
        gene="LBX1", uniprot="P52954", term="eta_a",
        role="Paraspinal muscle specification TF; top GWAS hit for AIS",
        prediction="Intermediate anisotropy, high disorder (61%); blocky structure sensitive "
                   "to nuclear stiffness; during energy deficit, LBX1 program fails first",
        scaling="L^2 (muscle cross-section x length)"
    ),
    ProteinTarget(
        gene="FLNA", uniprot="P21333", term="eta_a",
        role="Filamin A; cytoskeletal mechanosensor and crosslinker",
        prediction="Tension-gated signal integrator; unfolding domains expose cryptic sites; "
                   "maintenance cost proportional to cytoskeletal volume",
        scaling="L^3 (muscle volume)"
    ),
    ProteinTarget(
        gene="VIM", uniprot="P08670", term="eta_a",
        role="Vimentin; gravitational strain gauge in cells",
        prediction="Intermediate filament; collapses in microgravity triggering ROS cascade; "
                   "the 'first domino' in energy deficit — its failure triggers metabolic switch",
        scaling="L^3 (cell volume)"
    ),
    ProteinTarget(
        gene="LMNA", uniprot="P02545", term="eta_a",
        role="Lamin A/C; nuclear mechanostat scaling with tissue stiffness",
        prediction="Highest anisotropy (4.75) among TFs; nuclear stiffness must scale with "
                   "gravitational load during growth; failure = Scalar Senescence",
        scaling="L^2 (load-bearing cross-section)"
    ),
    ProteinTarget(
        gene="CAV1", uniprot="Q03135", term="eta_a",
        role="Caveolin-1; membrane curvature sensor and mechanotransducer",
        prediction="Membrane-embedded sensor; cost of maintaining caveolar pits scales with "
                   "membrane area; connects to YAP/TAZ nuclear translocation",
        scaling="L^2 (membrane area)"
    ),

    # ===== Gamma_m: Basal tissue maintenance =====
    ProteinTarget(
        gene="COL1A1", uniprot="P02452", term="Gamma_m",
        role="Type I collagen; primary structural protein of vertebral bone/disc",
        prediction="Triple helix (high anisotropy expected); collagen turnover is the largest "
                   "single component of Gamma_m; cost scales with tissue volume",
        scaling="L^3 (bone/disc volume)"
    ),
    ProteinTarget(
        gene="COMP", uniprot="P49747", term="Gamma_m",
        role="Cartilage oligomeric matrix protein; disc ECM maintenance",
        prediction="ECM scaffold protein; turnover rate determines matrix maintenance cost; "
                   "disc height increases during growth requiring more COMP",
        scaling="L (disc height x number)"
    ),
    ProteinTarget(
        gene="SIRT1", uniprot="Q96EB6", term="Gamma_m",
        role="Sirtuin 1; NAD+-dependent metabolic sensor (energy gauge)",
        prediction="Compact enzyme; acts as the 'fuel gauge' detecting energy deficit; "
                   "low NAD+/NADH during rapid growth triggers metabolic switch to adipogenesis",
        scaling="constant (sensor, not structural)"
    ),
    ProteinTarget(
        gene="SOX9", uniprot="P48436", term="Gamma_m",
        role="Master chondrogenic TF; growth plate cartilage specification",
        prediction="SOX9 drives growth plate proliferation; its activity rate determines dL/dt; "
                   "higher SOX9 = faster growth = steeper metabolic demand curve",
        scaling="L (growth plate activity)"
    ),
    ProteinTarget(
        gene="SHH", uniprot="Q15465", term="Gamma_m",
        role="Sonic Hedgehog; morphogen gradient for vertebral patterning",
        prediction="Compact signaling molecule; maintains the information field I(s) itself; "
                   "gradient maintenance cost scales with rod length",
        scaling="L (gradient length)"
    ),
    ProteinTarget(
        gene="CDKN1A", uniprot="P38936", term="Gamma_m",
        role="p21; cell cycle inhibitor activated by mechanical unloading",
        prediction="Small, compact; upregulated in microgravity to halt proliferation; "
                   "its activation = signal that energy supply is insufficient for growth",
        scaling="threshold (binary switch)"
    ),
    ProteinTarget(
        gene="PPARGC1A", uniprot="Q9UBK2", term="Gamma_m",
        role="Mitochondrial biogenesis master regulator; determines energy SUPPLY capacity",
        prediction="Energy supply bottleneck during growth spurt contributes to AIS; failure to scale "
                   "mitochondrial biogenesis with L^3 leads to metabolic burnout.",
        scaling="L (mitochondrial volume)"
    ),
    ProteinTarget(
        gene="IGF1R", uniprot="P08069", term="Gamma_m",
        role="Insulin-like growth factor 1 receptor; mediates growth plate signaling",
        prediction="Signaling receptor for growth spurt rate; rapid growth linked to curve progression; "
                   "receptor density determines sensitivity to systemic growth signals.",
        scaling="L (receptor density)"
    ),
    ProteinTarget(
        gene="GHR", uniprot="P10912", term="Gamma_m",
        role="Growth hormone receptor; master regulator of adolescent growth spurt rate",
        prediction="Regulates the rate of spinal elongation; rapid growth is a risk factor for AIS; "
                   "dictates the pace of demand increase.",
        scaling="L (growth signal)"
    ),
    ProteinTarget(
        gene="ARNTL", uniprot="O00327", term="Gamma_m",
        role="BMAL1; circadian clock TF in intervertebral disc regulating metabolism",
        prediction="Circadian rhythm disruption linked to disc degeneration and scoliosis; essential "
                   "for temporal coordination of repair mechanisms.",
        scaling="L (circadian entrainment)"
    ),
]

# ---------------------------------------------------------------------------
# Load pre-computed metrics
# ---------------------------------------------------------------------------

def load_all_metrics() -> Dict[str, Dict[str, Any]]:
    """Load all pre-computed AFCC metrics, preferring latest date."""
    all_proteins = {}

    for metrics_dir in METRICS_DIRS:
        if not metrics_dir.exists():
            continue
        # Sort by date (directory name) to get latest last (will overwrite)
        for metrics_file in sorted(metrics_dir.glob("*/metrics.csv")):
            with open(metrics_file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    gene = row.get("gene_symbol", "")
                    if gene:
                        all_proteins[gene] = row
                        all_proteins[gene]["_source_file"] = str(metrics_file)

    return all_proteins


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(targets: List[ProteinTarget], metrics: Dict) -> str:
    """Generate evidence note mapping proteins to dissipation terms."""

    terms = {
        "eta_p": ("Proprioceptive Feedback Cost (η_p)",
                  "The cost of **sensing curvature error**. These proteins maintain "
                  "the proprioceptive circuit that detects deviations from the "
                  "information-prescribed shape. During the growth spurt, sensing "
                  "density (sensors per unit length) must scale with L."),
        "eta_a": ("Active Moment Maintenance (η_a)",
                  "The cost of **tonic muscle contraction and cytoskeletal tension** "
                  "that holds the spine against gravity. This is the largest ATP "
                  "consumer — the molecular machines converting chemical energy into "
                  "the mechanical moment opposing gravitational sag. Scales as L² to L³."),
        "Gamma_m": ("Basal Tissue Maintenance (Γ_m)",
                    "The cost of **maintaining the information field itself**: ECM "
                    "turnover, morphogen gradients, metabolic homeostasis, and the "
                    "growth machinery. This term determines the **supply side** of "
                    "the energy balance and the **rate** of the growth spurt."),
    }

    lines = []
    lines.append("# Thermodynamic Cost of Countercurvature: Molecular Mapping via AlphaFold")
    lines.append("")
    lines.append(f"**Date:** {time.strftime('%Y-%m-%d')}")
    lines.append("**Source:** Pre-computed AFCC metrics (AlphaFold Countercurvature pipeline)")
    lines.append("**Framework:** Free energy dissipation functional (manuscript Eq. 7)")
    lines.append("")
    lines.append("```")
    lines.append("Ḟ = ∫₀ᴸ [ ηₚ|∂κ/∂t|² + ηₐ(κ - κ_passive)² + Γₘ(s) ] ds")
    lines.append("```")
    lines.append("")
    lines.append("## Key Insight")
    lines.append("")
    lines.append("Einstein describes gravity as curvature of spacetime. Life forms grow")
    lines.append("*against* this curvature — a paradox paid for in ATP. The same atoms")
    lines.append("that sit passively in rock are reorganized in living tissue to resist")
    lines.append("gravitational geodesics. The thermodynamic cost of this resistance is")
    lines.append("not abstract: it is paid at the molecular level by specific proteins")
    lines.append("whose AlphaFold-predicted structures reveal how they bear this cost.")
    lines.append("")
    lines.append("The spine's S-curve is a **standing wave** requiring continuous energy")
    lines.append("input. During the adolescent growth spurt, the metabolic demand")
    lines.append("(P_counter ~ L^{2-3}) increases 65-113% while the supply system lags,")
    lines.append("creating the **Energy Deficit Window** that seeds AIS.")
    lines.append("")

    for term_key, (term_name, term_desc) in terms.items():
        term_targets = [t for t in targets if t.term == term_key]
        lines.append("---")
        lines.append(f"## {term_name}")
        lines.append("")
        lines.append(term_desc)
        lines.append("")

        lines.append("| Gene | UniProt | Anisotropy | Morphology | Rg (Å) | pLDDT | Res | Hinges | L-Scaling | Role |")
        lines.append("| :--- | :--- | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |")

        for t in term_targets:
            m = metrics.get(t.gene)
            if m:
                aniso = float(m.get("anisotropy_index", 0))
                morph = m.get("morphology", "?")
                rg = float(m.get("radius_of_gyration", 0))
                plddt = float(m.get("plddt_mean", 0))
                nres = int(m.get("n_residues", 0))
                hinges = int(m.get("hinge_candidates", 0))

                lines.append(
                    f"| **{t.gene}** | {t.uniprot} | {aniso:.2f} | "
                    f"{morph} | {rg:.1f} | {plddt:.1f} | {nres} | "
                    f"{hinges} | {t.scaling} | {t.role} |"
                )
            else:
                lines.append(
                    f"| **{t.gene}** | {t.uniprot} | — | — | — | — | — | — | "
                    f"{t.scaling} | {t.role} *(no AFCC data)* |"
                )
        lines.append("")

        # Compute term-level statistics
        available = [metrics[t.gene] for t in term_targets if t.gene in metrics]
        if available:
            anisos = [float(m.get("anisotropy_index", 0)) for m in available]
            rgs = [float(m.get("radius_of_gyration", 0)) for m in available]
            plddts = [float(m.get("plddt_mean", 0)) for m in available]
            total_res = sum(int(m.get("n_residues", 0)) for m in available)
            total_hinges = sum(int(m.get("hinge_candidates", 0)) for m in available)

            lines.append(f"**Structural summary:** Mean anisotropy = **{np.mean(anisos):.2f}**, "
                        f"Rg range = {min(rgs):.0f}–{max(rgs):.0f} Å, "
                        f"Mean pLDDT = {np.mean(plddts):.1f}, "
                        f"Total residues = {total_res}, "
                        f"Total hinges = {total_hinges}")
            lines.append("")

        # Per-protein predictions
        lines.append("### Thermodynamic Predictions")
        lines.append("")
        for t in term_targets:
            lines.append(f"- **{t.gene}** ({t.scaling}): {t.prediction}")
        lines.append("")

    # =========================================================================
    # Synthesis
    # =========================================================================
    lines.append("---")
    lines.append("## Synthesis: The Energy Deficit Window — A Molecular View")
    lines.append("")

    # Compute cross-term statistics
    eta_p_targets = [t for t in targets if t.term == "eta_p" and t.gene in metrics]
    eta_a_targets = [t for t in targets if t.term == "eta_a" and t.gene in metrics]
    gamma_targets = [t for t in targets if t.term == "Gamma_m" and t.gene in metrics]

    if eta_p_targets:
        eta_p_aniso = np.mean([float(metrics[t.gene]["anisotropy_index"]) for t in eta_p_targets])
    else:
        eta_p_aniso = 0
    if eta_a_targets:
        eta_a_aniso = np.mean([float(metrics[t.gene]["anisotropy_index"]) for t in eta_a_targets])
    else:
        eta_a_aniso = 0
    if gamma_targets:
        gamma_aniso = np.mean([float(metrics[t.gene]["anisotropy_index"]) for t in gamma_targets])
    else:
        gamma_aniso = 0

    lines.append("### Structural Signatures Across Terms")
    lines.append("")
    lines.append("| Term | Mean Anisotropy | Structural Signature | Scaling |")
    lines.append("| :--- | ---: | :--- | :--- |")
    lines.append(f"| **η_p** (Sensing) | {eta_p_aniso:.2f} | "
                f"Extended sensors (PIEZO1/2) + disordered TFs (EGR3, RUNX3) | L to L² |")
    lines.append(f"| **η_a** (Actuation) | {eta_a_aniso:.2f} | "
                f"Fibrous scaffolds (LMNA) + crosslinkers (FLNA) + strain gauges (VIM) | L² to L³ |")
    lines.append(f"| **Γ_m** (Maintenance) | {gamma_aniso:.2f} | "
                f"Compact enzymes (SIRT1) + ECM (COL1A1) + morphogens (SHH) | L to L³ |")
    lines.append("")

    lines.append("### The Molecular Logic of the Energy Deficit Window")
    lines.append("")
    lines.append("The AlphaFold structural data reveal a clear hierarchy of vulnerability:")
    lines.append("")
    lines.append("1. **High-anisotropy demand proteins** (PIEZO2: 4.44, LMNA: 4.75, PIEZO1: 3.90)")
    lines.append("   are structurally the most expensive to maintain. Their extended")
    lines.append("   conformations require continuous cytoskeletal tension for proper")
    lines.append("   orientation. These are the first to lose fidelity when energy is scarce.")
    lines.append("")
    lines.append("2. **Disordered sensing TFs** (EGR3: 64% disordered, RUNX3: 56% disordered)")
    lines.append("   require constant chaperone activity and have high turnover rates.")
    lines.append("   Their expression levels must track spinal length but their")
    lines.append("   transcription depends on the same energy pool being depleted.")
    lines.append("")
    lines.append("3. **Compact supply-side proteins** (SIRT1, CDKN1A, SOX9) are structurally")
    lines.append("   cheap but functionally rate-limiting. SIRT1 detects the energy deficit;")
    lines.append("   SOX9 drives the growth rate; CDKN1A halts proliferation when energy fails.")
    lines.append("   These are the **sensors and switches** of the Energy Deficit Window.")
    lines.append("")
    lines.append("4. **The critical mismatch**: During peak height velocity (~8 cm/yr),")
    lines.append("   the demand proteins (PIEZO2, LMNA, FLNA) require ~65-113% more")
    lines.append("   energy, but the supply sensor (SIRT1) detects declining NAD+/NADH")
    lines.append("   *after* the deficit has already begun. This lag — between structural")
    lines.append("   demand and metabolic sensing — is the molecular basis of the")
    lines.append("   Energy Deficit Window.")
    lines.append("")
    lines.append("### Testable Prediction")
    lines.append("")
    lines.append("Paraspinal muscle biopsies from AIS patients at peak growth velocity")
    lines.append("will show:")
    lines.append("- **Reduced** PIEZO2 membrane density and LMNA nuclear aspect ratio")
    lines.append("  (demand-side failure)")
    lines.append("- **Reduced** PPARGC1A/PGC-1α and elevated SIRT1 (supply-side stress)")
    lines.append("- **Elevated** CDKN1A/p21 (growth arrest signal)")
    lines.append("- **Asymmetric** LBX1 expression (concave < convex)")
    lines.append("")
    lines.append("compared to height-matched non-scoliotic controls.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("  THERMODYNAMIC COST OF COUNTERCURVATURE: AlphaFold Analysis")
    print("  Using pre-computed AFCC metrics")
    print("=" * 70)

    # Load cached metrics
    metrics = load_all_metrics()
    print(f"\n  Loaded metrics for {len(metrics)} proteins")

    # Check coverage
    found = []
    missing = []
    for t in TARGETS:
        if t.gene in metrics:
            found.append(t)
        else:
            missing.append(t)
            print(f"  ⚠ Missing: {t.gene} ({t.uniprot})")

    print(f"  Matched: {len(found)}/{len(TARGETS)} targets")
    print()

    # Generate evidence note
    report = generate_report(TARGETS, metrics)
    note_path = Path("notes/evidence") / f"{time.strftime('%Y-%m-%d')}__thermodynamic_cost_proteins.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    with open(note_path, "w") as f:
        f.write(report)
    print(f"  ✅ Evidence note: {note_path}")

    # Save CSV
    csv_path = OUTPUT_DIR / "thermodynamic_cost_proteins.csv"
    rows = []
    for t in TARGETS:
        m = metrics.get(t.gene, {})
        rows.append({
            "gene": t.gene,
            "uniprot": t.uniprot,
            "term": t.term,
            "role": t.role,
            "scaling": t.scaling,
            "anisotropy": m.get("anisotropy_index", ""),
            "morphology": m.get("morphology", ""),
            "rg": m.get("radius_of_gyration", ""),
            "plddt_mean": m.get("plddt_mean", ""),
            "n_residues": m.get("n_residues", ""),
            "hinge_candidates": m.get("hinge_candidates", ""),
            "disorder_fraction": m.get("disorder_fraction_proxy", ""),
            "PAE_blockiness": m.get("PAE_domain_blockiness_score", ""),
            "status": "matched" if t.gene in metrics else "missing",
        })

    if rows:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"  ✅ CSV: {csv_path}")

    # Print summary
    print(f"\n{'='*70}")
    print("  SUMMARY BY DISSIPATION TERM")
    print(f"{'='*70}")

    for term, label in [("eta_p", "η_p (Sensing)"), ("eta_a", "η_a (Actuation)"), ("Gamma_m", "Γ_m (Maintenance)")]:
        term_targets = [t for t in TARGETS if t.term == term and t.gene in metrics]
        if not term_targets:
            continue

        anisos = [float(metrics[t.gene]["anisotropy_index"]) for t in term_targets]
        rgs = [float(metrics[t.gene]["radius_of_gyration"]) for t in term_targets]

        print(f"\n  {label}: {len(term_targets)} proteins, "
              f"mean aniso={np.mean(anisos):.2f}, Rg range={min(rgs):.0f}–{max(rgs):.0f} Å")

        for t in term_targets:
            m = metrics[t.gene]
            a = float(m.get("anisotropy_index", 0))
            rg = float(m.get("radius_of_gyration", 0))
            plddt = float(m.get("plddt_mean", 0))
            nres = int(m.get("n_residues", 0))
            hinges = int(m.get("hinge_candidates", 0))
            morph = m.get("morphology", "?")
            disorder = float(m.get("disorder_fraction_proxy", 0))

            print(f"    {t.gene:10s}  aniso={a:5.2f}  Rg={rg:6.1f}  "
                  f"pLDDT={plddt:5.1f}  res={nres:4d}  "
                  f"hinges={hinges}  disorder={disorder:.0%}  [{morph}]  "
                  f"scales:{t.scaling}")


if __name__ == "__main__":
    main()
