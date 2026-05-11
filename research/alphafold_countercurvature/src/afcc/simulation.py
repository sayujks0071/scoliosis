"""
Simulation module for running PyElastica simulations driven by protein metrics.

This module integrates the `spinalmodes` simulation engine with the `afcc` analysis pipeline.
It maps structural metrics (calculated from PDB files) to mechanical parameters for a Cosserat rod simulation.

Key Mappings:
- Anisotropy Index -> Stiffness Anisotropy (Vector Strength): Higher anisotropy implies stronger directional cues.
- Curvature Summary -> Chi_Kappa (Intrinsic Curvature Drive): Higher curvature implies stronger active bending.
- Torsion Summary -> Chi_Tau (Intrinsic Torsion Drive): Higher torsion implies stronger twist coupling.
- PAE Domain Blockiness -> Chi_E (Stiffness Modulation): Higher blockiness implies segmented stiffness.

This allows us to predict the "mechanical phenotype" of a protein assembly or tissue based on its structural components.
"""

import time
import tracemalloc
from typing import Any, Dict

import numpy as np

# Try to import spinalmodes components
try:
    from spinalmodes.countercurvature.coupling import CounterCurvatureParams
    from spinalmodes.countercurvature.info_fields import InfoField1D
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        CounterCurvatureRodSystem,
    )
except ImportError:
    # If spinalmodes is not installed as a package, we might need sys.path hack or fail
    # For now, we assume it is available as per environment setup.
    CounterCurvatureRodSystem = None
    PYELASTICA_AVAILABLE = False
    CounterCurvatureParams = None
    InfoField1D = None

def simulate_protein_mechanics(
    metrics: Dict[str, Any],
    length: float = 1.0,
    n_elements: int = 50,
    duration: float = 2.0,
    dt: float = 1e-4,
    gravity: float = 9.81,
    boundary_condition: str = "fixed",
    scale_factor_kappa: float = 5.0,
    scale_factor_tau: float = 5.0,
    scale_factor_E: float = 0.5,
    show_progress: bool = True,
) -> Dict[str, Any]:
    """
    Run a mechanical simulation based on protein metrics.

    This function bridges the gap between protein structure (AlphaFold) and tissue mechanics (PyElastica).
    It maps structural metrics to parameters of the Biological Counter-Curvature theory:

    - **Anisotropy Index** -> **Stiffness Anisotropy**: Represents the "Vector" cue strength (e.g., Fibrillin alignment).
    - **Curvature Summary** -> **Chi_Kappa**: Represents the "Scalar" active drive (e.g., Piezo2 gain).
    - **Torsion Summary** -> **Chi_Tau**: Represents twist coupling (e.g., Planar Cell Polarity defects).
    - **PAE Blockiness** -> **Chi_E**: Represents stiffness modulation (e.g., segmentation).

    Args:
        metrics: Dictionary of protein metrics (from afcc.metrics.MetricsAnalyzer).
        length: Length of the rod (m).
        n_elements: Number of elements in the rod.
        duration: Simulation duration (s).
        dt: Time step (s).
        gravity: Gravitational acceleration (m/s^2).
        boundary_condition: "fixed" or "pinned".
        scale_factor_kappa: Scaling factor for curvature summary -> chi_kappa.
        scale_factor_tau: Scaling factor for torsion summary -> chi_tau.
        scale_factor_E: Scaling factor for PAE blockiness -> chi_E.
        show_progress: Whether to show the PyElastica progress bar.

    Returns:
        Dictionary containing simulation results (max curvature, max torsion, scoliosis index)
        and performance metrics (runtime, memory).
    """
    if not PYELASTICA_AVAILABLE or CounterCurvatureRodSystem is None:
        return {
            "error": "PyElastica or spinalmodes not available.",
            "pyelastica_available": False
        }

    # 1. Extract and Map Metrics
    # Anisotropy Index (1.0 = Isotropic, >1.0 = Anisotropic)
    # Map directly to stiffness_anisotropy (Vector Strength)
    anisotropy = metrics.get('anisotropy_index', 1.0)
    if np.isnan(anisotropy):
        anisotropy = 1.0

    # Curvature Summary (Mean curvature of backbone)
    # Map to chi_kappa (Intrinsic curvature drive)
    curv_summary = metrics.get('curvature_summary', 0.0)
    if np.isnan(curv_summary):
        curv_summary = 0.0
    chi_kappa = curv_summary * scale_factor_kappa

    # Torsion Summary (Mean torsion of backbone)
    # Map to chi_tau (Intrinsic torsion drive)
    tor_summary = metrics.get('torsion_summary', 0.0)
    if np.isnan(tor_summary):
        tor_summary = 0.0
    chi_tau = tor_summary * scale_factor_tau

    # PAE Blockiness (Degree of domain segmentation)
    # Map to chi_E (Stiffness modulation)
    blockiness = metrics.get('PAE_domain_blockiness_score', 0.0)
    if np.isnan(blockiness):
        blockiness = 0.0
    chi_E = blockiness * scale_factor_E

    # 4. Run Simulation with Profiling
    tracemalloc.start()
    t0 = time.time()

    try:
        # 2. Setup Information Field
        # For a minimal experiment, we use a generic Gaussian info field
        # representing a localized signal (e.g. morphogen gradient)
        if n_elements < 2:
            raise ValueError("n_elements must be at least 2")

        s = np.linspace(0, length, n_elements + 1)
        # Center bump
        info_center = 0.5 * length
        info_width = 0.1 * length
        I = 0.5 + 0.5 * np.exp(-0.5 * ((s - info_center) / info_width)**2)
        dIds = np.gradient(I, s)
        info = InfoField1D(s=s, I=I, dIds=dIds)

        # 3. Setup Parameters
        params = CounterCurvatureParams(
            chi_kappa=chi_kappa,
            chi_tau=chi_tau,
            chi_E=chi_E,
            chi_M=0.0, # Active moments not mapped yet
            scale_length=length
        )

        # Create System
        # We use a constant intrinsic curvature base (Kyphosis/Lordosis)
        # to see deviations from it
        kappa_gen = np.zeros((3, n_elements + 1))
        kappa_gen[0, :] = 2.0 # Constant sagittal curvature

        rod_system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=length,
            n_elements=n_elements,
            E0=1e6, # 1 MPa
            radius=0.01,
            kappa_gen=kappa_gen,
            gravity=gravity,
            stiffness_anisotropy=anisotropy
        )

        result = rod_system.run_simulation(
            final_time=duration,
            dt=dt,
            save_every=max(1, int(duration/dt/10)), # Save ~10 frames, ensure >= 1
            boundary_condition=boundary_condition,
            progress_bar=show_progress
        )

        sim_metrics = result.compute_final_metrics()

        success = True
        error_msg = ""

    except Exception as e:
        success = False
        error_msg = str(e)
        sim_metrics = {}

    t1 = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    runtime = t1 - t0
    peak_mb = peak / (1024 * 1024)

    # 5. Compile Result
    output = {
        "input_anisotropy": anisotropy,
        "input_curvature": curv_summary,
        "input_torsion": tor_summary,
        "input_blockiness": blockiness,
        "mapped_stiffness_anisotropy": anisotropy,
        "mapped_chi_kappa": chi_kappa,
        "mapped_chi_tau": chi_tau,
        "mapped_chi_E": chi_E,
        "runtime_sec": runtime,
        "peak_memory_mb": peak_mb,
        "success": success,
        "error": error_msg,
    }

    # Merge sim metrics
    output.update(sim_metrics)

    return output
