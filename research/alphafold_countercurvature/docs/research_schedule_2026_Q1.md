# Research Schedule: Gravity as an Optimization Process (2026 Q1)

**Date:** 2026-10-27
**PI:** Jules (Principal Investigator, Theoretical Biology)
**Context:** Gradient Descent Optimization Framework
**Status:** ACTIVE

---

## Summary

This research schedule operationalizes the hypothesis that spinal alignment is a "Gradient Descent" optimization process where the organism minimizes the **Total Potential Energy** ($U_{CC}$) against the gravitational field. The schedule is designed to test the stability boundary defined by the **Bio-Gravitational Number** ($\mathcal{B}_g$) and the failure modes associated with "**Spinal Jetlag**" (circadian desynchronization of the learning rate).

**Core Framework:**
*   **Cost Function ($U_{CC}$):** Total Potential Energy (Gravity + Elasticity - Information).
*   **Gradient:** Mechanosensory error (PIEZO2) between current shape and genetic reference metric.
*   **Optimizer:** Differential Growth (Slow) and Muscle Tone (Fast).
*   **Learning Rate Scheduler:** Circadian Clock (BMAL1) modulates tissue sensitivity ($\alpha$).
*   **Failure Mode:** Scoliosis as a "Local Minimum" or "Exploding Gradient".

---

## Phase 1: Computational Proof-of-Concept (Weeks 1-4)

**Objective:** Establish the baseline simulation environment in `src/spinalmodes/countercurvature/pyelastica_bridge.py`, explicitly defining the cost function and demonstrating optimization failure (Scoliosis).

| Week | Focus | Task | Hypothesis |
| :--- | :--- | :--- | :--- |
| **1** | The Cost Function ($U_{CC}$) | Implement a utility in `pyelastica_bridge.py` to calculate the components of $U_{CC}$: Gravitational Potential ($E_g$) vs. Elastic Strain Energy ($E_{el}$) vs. Information Work. | Minimizing $U_{CC}$ leads to a stable, straight spine in 1g. The system naturally finds the global minimum. |
| **2** | The Gradient (Error Signal) | Implement an iterative "Gradient Descent" loop. Update `rod.rest_kappa` in `CounterCurvatureRodSystem` based on the error between current curvature and genetic target. | Local mechanosensory feedback (Gradient) is sufficient to correct global posture errors without a central controller. |
| **3** | The Bio-Gravitational Number ($\mathcal{B}_g$) | Perform a parameter sweep of the `CounterCurvatureParams` in `pyelastica_bridge.py`. Calculate $\mathcal{B}_g = \chi_M \langle |\nabla I| \rangle / (\rho A g L^2)$ for simulation values. | There exists a critical $\mathcal{B}_g < 1$ where the optimizer fails to converge, leading to buckling (Local Minimum). |
| **4** | Optimization Failure (Exploding Gradient) | Simulate "Exploding Gradient" by increasing the feedback gain (learning rate) or introducing delay/noise in the `ActiveMuscleTorques` update loop. | High sensory noise or delays cause the optimization step size to exceed the stability limit, resulting in oscillatory divergence (Scoliosis). |

---

## Phase 2: The "Spinal Jetlag" Simulation (Weeks 5-8)

**Objective:** Integrate the Circadian Clock as a time-dependent "Learning Rate Scheduler" to test the "Spinal Jetlag" hypothesis. What happens if the clock desynchronizes from the gravity vector?

| Week | Focus | Task | Hypothesis |
| :--- | :--- | :--- | :--- |
| **5** | The Learning Rate Scheduler | Implement a time-dependent scalar for `ActiveMuscleTorques`: $\alpha(t) = \alpha_{base} (1 + A \cos(\omega t + \phi))$. | Synchronizing the "Learning Rate" (sensitivity) with the "Batch Load" (daily gravity cycle) minimizes energy expenditure. |
| **6** | Desynchronization (The Jetlag) | Run simulations where the clock phase $\phi$ is shifted relative to the gravity load cycle. Simulate "Shift Work" conditions. | A phase mismatch ($\Delta \phi \neq 0$) causes the optimizer to update shape based on "stale" gradients, increasing the steady-state error (Cobb angle). |
| **7** | Vector-Scalar Mismatch | Simulate **Microgravity**: Set gravity vector $\mathbf{g}=0$ but maintain high Scalar "swelling pressure" (via `beta_H` in `formalism_01.md`). | Loss of the vector component ($\mathbf{g}$) while maintaining scalar pressure leads to "Directionless Growth" and loss of curvature definition. |
| **8** | The Stabilizer (Torsional Coupling) | Revisit `stiffness_anisotropy` in `CounterCurvatureRodSystem`. Test if high Torsional Coupling (`chi_tau`) dampens the circadian oscillations. | Structural coupling (Torsion) acts as a passive damper that stabilizes the aggressive active optimization of the circadian clock. |

---

## Phase 3: Experimental Validation Design (Weeks 9-12)

**Objective:** Outline specific wet-lab experiments to validate the computational predictions, translating `pyelastica` results into biological protocols.

| Week | Focus | Task | Hypothesis |
| :--- | :--- | :--- | :--- |
| **9** | Species Comparative Analysis | Calculate $\mathcal{B}_g$ for: Human (AIS), Mouse, Zebrafish, and Whale using literature data (Muscle PCSA vs Bone Length). | Species with $\mathcal{B}_g \approx 1$ (Humans) are uniquely susceptible to "Optimization Failure" compared to high $\mathcal{B}_g$ species (Mice). |
| **10** | Experimental Design: "Test T_Clock" | Design the "Desynchronization Drift" protocol: Raise zebrafish in arhythmic (strobe) vs. rhythmic (12:12) light. Measure spinal straightness. | Disruption of the central clock (Learning Rate Scheduler) leads to higher variance in spinal alignment (higher Loss). |
| **11** | Experimental Design: "Test U" | Design the "Loading Rescue" protocol: Apply cyclic mechanical stretch to organoids at specific circadian phases (PER2::LUC bioluminescence). | Mechanical loading is only anabolic (corrective) if applied during the "sensitive" phase of the local clock. |
| **12** | Synthesis & Manuscript | Integrate Phase 1/2 simulation data and Phase 3 experimental designs into `manuscript/sections/theory.tex`. Finalize `formalism_01.md`. | The "Gravity as Optimization" framework successfully unifies mechanical buckling and biological growth theories. |

---

## Risk Assessment

### 1. Theoretical Bottlenecks
*   **Non-Convex Cost Function:** The Total Potential Energy landscape ($U_{CC}$) might be non-convex, meaning "Gradient Descent" could get stuck in local minima (deformities) even with a perfect optimizer.
    *   *Mitigation:* Use `pyelastica` to map the full energy landscape and identify "Basins of Attraction" for healthy vs. scoliotic spines.
*   **Definition of Information Energy:** The term $-U_{info}$ in the cost function is abstract.
    *   *Mitigation:* Operationalize it strictly as the deviation from `kappa_rest` in the code, avoiding information-theoretic ambiguity.

### 2. Computational Risks
*   **Timescale Separation:** Simulating circadian days ($10^5$ seconds) with mechanical timesteps ($10^{-4}$ seconds) is computationally prohibitive.
    *   *Mitigation:* Use "Time-Homogenization" or a dual-scale approach in `pyelastica_bridge.py`, assuming mechanical equilibrium is reached instantly relative to growth.

### 3. Experimental Risks
*   **Measuring $\mathcal{B}_g$ In Vivo:** Estimating "Information Gradient" strength in living tissue is difficult.
    *   *Mitigation:* Use proxies like Muscle/Bone cross-sectional area ratios and `ActiveMuscleTorques` generated in simulations as a baseline.
