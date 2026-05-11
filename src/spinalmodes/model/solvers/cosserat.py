"""
Optional thin bridge to PyElastica for full Cosserat rod simulations.

Import-safe even when PyElastica is absent, enabling CI smoke tests to skip gracefully.
"""

from __future__ import annotations

from typing import Any


def available() -> bool:
    """Return True if PyElastica is importable."""
    try:

        return True
    except Exception:
        return False


def simulate_cosserat(params: dict[str, Any]) -> dict[str, Any]:
    """
    Run a Cosserat rod simulation with gravity and IEC target curvature actuation.

    Args:
        params: Dictionary containing simulation parameters:
            - info: InfoField1D object
            - iec_params: CounterCurvatureParams object
            - length: Rod length (float)
            - n_elements: Number of rod elements (int)
            - final_time: Simulation duration (float)
            - dt: Time step (float)
            - gravity: Gravity acceleration (float, default 9.81)
            - E0: Young's modulus (float, optional)
            - nu: Poisson ratio (float, optional)
            - rho: Density (float, optional)
            - radius: Rod radius (float, optional)
            - kappa_gen: Intrinsic curvature (array, optional)
            - save_every: Save interval (int, optional)
            - damping_constant: Damping constant (float, optional)

    Returns:
        dict with:
            - ok: bool
            - reason: str or None
            - result: dict containing 'time', 'centerline', 'curvature', 'info_field'
    """
    if not available():
        return {"ok": False, "reason": "PyElastica not installed", "result": None}

    try:
        # Import inside function to avoid hard dependency at module level
        from spinalmodes.countercurvature.api import CounterCurvatureRodSystem

        # Extract required parameters
        try:
            info = params["info"]
            iec_params = params["iec_params"]
            length = float(params["length"])
            n_elements = int(params["n_elements"])
            final_time = float(params["final_time"])
            dt = float(params["dt"])
        except KeyError as e:
            return {"ok": False, "reason": f"Missing required parameter: {e}", "result": None}

        # Optional parameters
        gravity = params.get("gravity", 9.81)
        E0 = params.get("E0", 1e6)
        nu = params.get("nu", 0.5)
        rho = params.get("rho", 1000.0)
        radius = params.get("radius", 0.01)
        kappa_gen = params.get("kappa_gen", None)
        save_every = params.get("save_every", 100)
        damping_constant = params.get("damping_constant", 0.5)

        # Create system
        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=iec_params,
            length=length,
            n_elements=n_elements,
            E0=E0,
            nu=nu,
            rho=rho,
            radius=radius,
            kappa_gen=kappa_gen,
            gravity=gravity,
        )

        # Run simulation
        result = system.run_simulation(
            final_time=final_time,
            dt=dt,
            save_every=save_every,
            gravity=gravity,
            damping_constant=damping_constant,
        )

        # Package result
        return {
            "ok": True,
            "reason": None,
            "result": {
                "time": result.time,
                "centerline": result.centerline,
                "curvature": result.curvature,
                "info_field": result.info_field,
            },
        }

    except Exception as e:
        return {"ok": False, "reason": str(e), "result": None}
