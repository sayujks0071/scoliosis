"""
JAX-accelerated elastic rod solver for Bio-Gravitational validation.

Replaces PyElastica's time-stepping loop with GPU-compiled JAX kernels.
Designed for batched parameter sweeps (vmap over chi_M, seed).

Usage:
    from spinalmodes.countercurvature.jax_rod_solver import jax_run_simulation

    # Single simulation (GPU-compiled)
    result = jax_run_simulation(params, info_field, final_time, dt)

    # Batched over 30 chi_M values (single GPU kernel)
    chi_M_array = jnp.linspace(0.1, 50.0, 30)
    batched_fn = jax.vmap(jax_run_simulation, in_axes=(0, None, None, None))
    results = batched_fn(params_array, info_field, final_time, dt)
"""

import jax
import jax.numpy as jnp
from jax import jit, vmap
from jax.tree_util import tree_map
from functools import partial
from typing import NamedTuple
import numpy as np  # Only for initial setup, not in GPU kernels


class RodState(NamedTuple):
    """Rod configuration at a single timestep."""
    positions: jax.Array  # (n_nodes, 3) - centerline positions
    velocities: jax.Array  # (n_nodes, 3) - node velocities
    directors: jax.Array  # (n_elements, 3, 3) - material frame
    omega: jax.Array  # (n_elements, 3) - angular velocities


class RodParams(NamedTuple):
    """Physical parameters for the rod."""
    n_elements: int
    length: float
    radius: float
    E0: float  # Young's modulus
    rho: float  # Density
    gravity: float
    chi_M: float  # Active moment coupling

    # Information field (pre-computed on CPU, transferred to GPU)
    I_field: jax.Array  # (n_nodes,)
    grad_I: jax.Array  # (n_nodes,)

    # Derived quantities (computed once)
    A: float  # Cross-sectional area
    I_moment: float  # Second moment of area (I = pi*r^4/4)
    rest_lengths: jax.Array  # (n_elements,)
    rest_voronoi_lengths: jax.Array  # (n_nodes,)


def initialize_rod_params(
    length: float,
    n_elements: int,
    radius: float,
    E0: float,
    rho: float,
    gravity: float,
    chi_M: float,
    info_field_I: np.ndarray,
    info_field_grad: np.ndarray
) -> RodParams:
    """
    Initialize rod parameters (CPU-side, transfers to GPU).

    Args:
        length: Rod length (m)
        n_elements: Number of elements
        radius: Rod radius (m)
        E0: Young's modulus (Pa)
        rho: Density (kg/m^3)
        gravity: Gravitational acceleration (m/s^2)
        chi_M: Active moment coupling strength
        info_field_I: Information field I(s) evaluated at nodes
        info_field_grad: Gradient dI/ds at nodes

    Returns:
        RodParams with JAX arrays on GPU
    """
    n_nodes = n_elements + 1
    A = np.pi * radius**2
    I_moment = np.pi * radius**4 / 4.0

    # Rest lengths (uniform spacing)
    rest_lengths = jnp.full(n_elements, length / n_elements)

    # Voronoi lengths (for mass distribution)
    voronoi = np.zeros(n_nodes)
    voronoi[0] = rest_lengths[0] / 2.0
    voronoi[-1] = rest_lengths[-1] / 2.0
    voronoi[1:-1] = (rest_lengths[:-1] + rest_lengths[1:]) / 2.0
    rest_voronoi_lengths = jnp.array(voronoi)

    return RodParams(
        n_elements=n_elements,
        length=length,
        radius=radius,
        E0=E0,
        rho=rho,
        gravity=gravity,
        chi_M=chi_M,
        I_field=jnp.array(info_field_I),
        grad_I=jnp.array(info_field_grad),
        A=A,
        I_moment=I_moment,
        rest_lengths=rest_lengths,
        rest_voronoi_lengths=rest_voronoi_lengths
    )


def initialize_rod_state(n_elements: int, length: float) -> RodState:
    """
    Initialize rod state (horizontal cantilever).

    Args:
        n_elements: Number of elements
        length: Rod length

    Returns:
        RodState with initial configuration
    """
    n_nodes = n_elements + 1

    # Horizontal rod along X-axis
    positions = jnp.zeros((n_nodes, 3))
    positions = positions.at[:, 0].set(jnp.linspace(0, length, n_nodes))

    # Zero initial velocities
    velocities = jnp.zeros((n_nodes, 3))

    # Identity directors (no initial rotation)
    directors = jnp.tile(jnp.eye(3), (n_elements, 1, 1))

    # Zero angular velocities
    omega = jnp.zeros((n_elements, 3))

    return RodState(
        positions=positions,
        velocities=velocities,
        directors=directors,
        omega=omega
    )


def compute_curvature(positions: jax.Array, rest_lengths: jax.Array, n_elements: int) -> jax.Array:
    """
    Compute discrete curvature kappa(s).

    Args:
        positions: (n_nodes, 3) centerline positions
        rest_lengths: (n_elements,) rest edge lengths
        n_elements: Number of elements (static)

    Returns:
        curvature: (n_elements,) curvature magnitude
    """
    # Tangent vectors
    edges = positions[1:] - positions[:-1]  # (n_elements, 3)
    tangents = edges / jnp.linalg.norm(edges, axis=1, keepdims=True)

    # Discrete curvature: kappa_i = |t_{i+1} - t_i| / L_i
    # For n_elements, we have n_elements tangents, n_elements-1 curvatures at internal nodes
    # Pad boundaries with zero curvature
    if n_elements == 1:
        return jnp.zeros(1)

    delta_tangent = tangents[1:] - tangents[:-1]  # (n_elements-1, 3)
    kappa_internal = jnp.linalg.norm(delta_tangent, axis=1) / rest_lengths[:-1]

    # Pad to n_elements length (zero curvature at boundaries)
    kappa = jnp.concatenate([
        jnp.array([0.0]),
        kappa_internal,
        jnp.array([0.0])
    ])[:n_elements]  # Trim to n_elements

    return kappa


def compute_bending_forces(
    positions: jax.Array,
    params: RodParams,
    n_elements: int
) -> jax.Array:
    """
    Compute elastic bending forces.

    Simplified: F_bend ∝ -E*I * kappa * (normal direction)

    Args:
        positions: (n_nodes, 3)
        params: RodParams

    Returns:
        forces: (n_nodes, 3) bending forces
    """
    n_nodes = n_elements + 1

    # Compute curvature
    kappa = compute_curvature(positions, params.rest_lengths, n_elements)

    # Simplified bending force: -E*I*kappa in Z-direction (resisting deflection)
    # This is a coarse approximation; full PyElastica uses discrete elastic rods theory
    forces = jnp.zeros((n_nodes, 3))

    # Apply bending restoring force proportional to curvature
    # Force at node i: sum of contributions from adjacent elements
    bend_stiffness = params.E0 * params.I_moment

    for i in range(1, n_nodes - 1):
        # Average curvature at node i
        kappa_avg = (kappa[i-1] + kappa[i]) / 2.0
        # Force direction: towards straight configuration (heuristic)
        # In Z-direction (vertical), opposing deflection
        forces = forces.at[i, 2].add(bend_stiffness * kappa_avg / params.length**2)

    return forces


def compute_active_moments(
    positions: jax.Array,
    params: RodParams
) -> jax.Array:
    """
    Compute active moments from IEC coupling (chi_M * grad_I).

    Args:
        positions: (n_nodes, 3)
        params: RodParams with chi_M, grad_I

    Returns:
        forces: (n_nodes, 3) equivalent forces from active moments
    """
    # M_active = chi_M * grad_I at each node
    # Convert moment to equivalent force: F ~ M / L (lever arm approximation)
    moment_magnitude = params.chi_M * params.grad_I  # (n_nodes,)

    # Apply as force in Z-direction (countering gravity sag)
    forces = jnp.zeros((positions.shape[0], 3))
    forces = forces.at[:, 2].set(moment_magnitude / params.length)

    return forces


def compute_gravitational_forces(params: RodParams, n_elements: int) -> jax.Array:
    """
    Compute gravitational forces.

    Args:
        params: RodParams

    Returns:
        forces: (n_nodes, 3) gravity forces (-Z direction)
    """
    n_nodes = n_elements + 1

    # Mass per node (distributed via Voronoi lengths)
    mass_per_node = params.rho * params.A * params.rest_voronoi_lengths

    # Gravity force: -m*g*Z
    forces = jnp.zeros((n_nodes, 3))
    forces = forces.at[:, 2].set(-mass_per_node * params.gravity)

    return forces


def compute_total_forces(
    state: RodState,
    params: RodParams,
    n_elements: int
) -> jax.Array:
    """
    Compute total forces on all nodes.

    Args:
        state: Current RodState
        params: RodParams

    Returns:
        forces: (n_nodes, 3) total forces
    """
    # Bending (elastic restoring)
    F_bend = compute_bending_forces(state.positions, params, n_elements)

    # Active moments (IEC coupling)
    F_active = compute_active_moments(state.positions, params)

    # Gravity
    F_grav = compute_gravitational_forces(params, n_elements)

    # Damping (velocity-dependent)
    damping_coeff = 0.1 * params.rho * params.A  # Heuristic
    F_damp = -damping_coeff * state.velocities

    # Total force
    forces = F_bend + F_active + F_grav + F_damp

    # Boundary condition: fix base node (node 0)
    forces = forces.at[0, :].set(0.0)

    return forces


def explicit_euler_step(
    state: RodState,
    params: RodParams,
    n_elements: int,
    dt: float
) -> RodState:
    """
    Single explicit Euler time step.

    Args:
        state: Current RodState
        params: RodParams
        dt: Time step

    Returns:
        new_state: Updated RodState
    """
    # Compute forces
    forces = compute_total_forces(state, params, n_elements)

    # Mass per node
    mass_per_node = params.rho * params.A * params.rest_voronoi_lengths

    # Acceleration: a = F / m
    accel = forces / mass_per_node[:, None]

    # Update velocities: v_{n+1} = v_n + a * dt
    new_velocities = state.velocities + accel * dt

    # Update positions: x_{n+1} = x_n + v_{n+1} * dt
    new_positions = state.positions + new_velocities * dt

    # Fix base node (boundary condition)
    new_positions = new_positions.at[0, :].set(state.positions[0, :])
    new_velocities = new_velocities.at[0, :].set(0.0)

    # Directors and omega unchanged in this simplified model
    # (Full PyElastica updates rotational DOFs; we focus on translational)

    return RodState(
        positions=new_positions,
        velocities=new_velocities,
        directors=state.directors,
        omega=state.omega
    )


@partial(jit, static_argnums=(1, 2, 3, 4))
def run_simulation_jit(
    params: RodParams,
    n_elements: int,
    n_steps: int,
    save_every: int,
    dt: float
) -> tuple[jax.Array, jax.Array]:
    """
    JIT-compiled simulation loop.

    Args:
        params: RodParams
        n_elements: Number of elements (static)
        n_steps: Number of time steps (static)
        save_every: Save interval (static)
        dt: Time step (static)

    Returns:
        positions_history: (n_saves, n_nodes, 3)
        curvature_history: (n_saves, n_elements)
    """
    n_saves = n_steps // save_every + 1
    n_nodes = n_elements + 1

    # Preallocate output arrays
    positions_history = jnp.zeros((n_saves, n_nodes, 3))
    curvature_history = jnp.zeros((n_saves, n_elements))

    # Initial state
    initial_state = initialize_rod_state(n_elements, params.length)
    state = initial_state
    positions_history = positions_history.at[0].set(state.positions)
    curvature_history = curvature_history.at[0].set(
        compute_curvature(state.positions, params.rest_lengths, n_elements)
    )

    # Time-stepping loop with lax.fori_loop (GPU-friendly)
    def body_fn(step, carry):
        state, pos_hist, curv_hist = carry

        # Euler step
        new_state = explicit_euler_step(state, params, n_elements, dt)

        # Save if needed
        save_idx = (step + 1) // save_every
        should_save = (step + 1) % save_every == 0

        pos_hist = jax.lax.cond(
            should_save,
            lambda: pos_hist.at[save_idx].set(new_state.positions),
            lambda: pos_hist
        )

        curv = compute_curvature(new_state.positions, params.rest_lengths, n_elements)
        curv_hist = jax.lax.cond(
            should_save,
            lambda: curv_hist.at[save_idx].set(curv),
            lambda: curv_hist
        )

        return (new_state, pos_hist, curv_hist)

    # Note: lax.fori_loop requires static n_steps, but we can use lax.scan for dynamic
    # For simplicity, using fori_loop with static n_steps
    carry = (state, positions_history, curvature_history)
    _, positions_history, curvature_history = jax.lax.fori_loop(
        0, n_steps, body_fn, carry
    )

    return positions_history, curvature_history


def jax_run_simulation(
    chi_M: float,
    length: float,
    n_elements: int,
    radius: float,
    E0: float,
    rho: float,
    gravity: float,
    info_field_I: np.ndarray,
    info_field_grad: np.ndarray,
    final_time: float,
    dt: float,
    save_every: int = 5000,
    seed: int = 0
) -> dict:
    """
    Run single JAX-accelerated rod simulation.

    Args:
        chi_M: Active moment coupling
        length: Rod length (m)
        n_elements: Number of elements
        radius: Rod radius (m)
        E0: Young's modulus (Pa)
        rho: Density (kg/m^3)
        gravity: Gravitational acceleration (m/s^2)
        info_field_I: Information field I(s) at nodes
        info_field_grad: Gradient dI/ds at nodes
        final_time: Simulation end time (s)
        dt: Time step (s)
        save_every: Save interval (steps)
        seed: Random seed (for initial perturbations, unused in deterministic version)

    Returns:
        result: Dict with 'positions', 'curvature', 'z_tip', 'runtime'
    """
    import time
    start = time.time()

    # Initialize parameters
    params = initialize_rod_params(
        length, n_elements, radius, E0, rho, gravity, chi_M,
        info_field_I, info_field_grad
    )

    # Run simulation (initial_state created inside JIT now)
    n_steps = int(final_time / dt)
    positions, curvature = run_simulation_jit(params, n_elements, n_steps, save_every, dt)

    # Block until GPU finishes (JAX is async)
    positions = jnp.asarray(positions).block_until_ready()
    curvature = jnp.asarray(curvature).block_until_ready()

    runtime = time.time() - start

    # Extract final z_tip
    z_tip = float(positions[-1, -1, 2])

    return {
        'positions': np.array(positions),
        'curvature': np.array(curvature),
        'z_tip': z_tip,
        'runtime': runtime
    }


# ============================================================================
# Batched version using vmap (GPU parallelization over chi_M)
# ============================================================================

def jax_run_simulation_batched(
    chi_M_array: np.ndarray,
    length: float,
    n_elements: int,
    radius: float,
    E0: float,
    rho: float,
    gravity: float,
    info_field_I: np.ndarray,
    info_field_grad: np.ndarray,
    final_time: float,
    dt: float,
    save_every: int = 5000
) -> list[dict]:
    """
    Run batched simulations over chi_M array (GPU-parallel).

    Uses jax.vmap to vectorize over chi_M → single GPU kernel launch.

    Args:
        chi_M_array: (n_chi_M,) array of chi_M values to sweep
        (other args same as jax_run_simulation)

    Returns:
        results: List of dicts, one per chi_M value
    """
    import time
    start = time.time()

    # Create batched params (vmap over chi_M dimension)
    n_chi_M = len(chi_M_array)

    # Broadcast scalar params to batch dimension
    params_list = [
        initialize_rod_params(
            length, n_elements, radius, E0, rho, gravity, chi_M,
            info_field_I, info_field_grad
        )
        for chi_M in chi_M_array
    ]

    # Stack into batched RodParams (each field gets batch dimension)
    # Note: JAX vmap requires pytrees, RodParams is a NamedTuple (pytree-compatible)
    batched_params = tree_map(lambda *args: jnp.stack(args), *params_list)

    # Vmap over batch dimension (axis 0 of params)
    batched_run = vmap(
        lambda p: run_simulation_jit(p, n_elements, int(final_time / dt), save_every, dt),
        in_axes=0  # Vmap over first axis of params
    )

    # Run all simulations in parallel on GPU
    positions_batch, curvature_batch = batched_run(batched_params)

    # Block until done
    positions_batch = positions_batch.block_until_ready()
    curvature_batch = curvature_batch.block_until_ready()

    runtime = time.time() - start

    # Unpack results
    results = []
    for i in range(n_chi_M):
        z_tip = float(positions_batch[i, -1, -1, 2])
        results.append({
            'positions': np.array(positions_batch[i]),
            'curvature': np.array(curvature_batch[i]),
            'z_tip': z_tip,
            'chi_M': float(chi_M_array[i]),
            'runtime_per_sim': runtime / n_chi_M
        })

    print(f"Batched run: {n_chi_M} sims in {runtime:.2f}s ({runtime/n_chi_M:.3f}s each)")

    return results
