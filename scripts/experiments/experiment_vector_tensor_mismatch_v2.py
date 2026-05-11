import os
import numpy as np
import matplotlib.pyplot as plt

OUT_DIR = "outputs/sim/vector_tensor_mismatch"
os.makedirs(OUT_DIR, exist_ok=True)

# Spatial domain
s = np.linspace(0, 1, 500)

# Base alignment: normal spine is well aligned (alpha ~ 0.9)
# Scoliotic spine has a localized lateral mismatch (alpha drops)
alpha_normal = 0.9 * np.ones_like(s)

# Introduce a localized mismatch (e.g., a left-right asymmetry near the apex)
apex_idx = 250
mismatch_width = 50
alpha_scoliotic = 0.9 * np.ones_like(s)
alpha_scoliotic[apex_idx-mismatch_width:apex_idx+mismatch_width] -= 0.8 * np.exp(-((s[apex_idx-mismatch_width:apex_idx+mismatch_width] - s[apex_idx])/(0.05))**2)

# Stiffness calculation
E_parallel = 1.0  # normalized max stiffness
E_perpendicular = 0.2  # normalized min stiffness

E_eff_normal = E_parallel * alpha_normal**2 + E_perpendicular * (1 - alpha_normal**2)
E_eff_scoliotic = E_parallel * alpha_scoliotic**2 + E_perpendicular * (1 - alpha_scoliotic**2)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

ax1.plot(s, alpha_normal, label="Normal", color="blue")
ax1.plot(s, alpha_scoliotic, label="Scoliotic Mismatch", color="red", linestyle="--")
ax1.set_ylabel(r"Alignment Parameter $\alpha(s)$")
ax1.set_title("Vector-Tensor Mismatch in Scoliosis")
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.plot(s, E_eff_normal, label="Normal", color="blue")
ax2.plot(s, E_eff_scoliotic, label="Scoliotic (Lateral Drop)", color="red", linestyle="--")
ax2.set_xlabel("Normalized Spinal Axis $s$")
ax2.set_ylabel(r"Effective Stiffness $E_{eff}$")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "vector_tensor_mismatch_plot.png"))
print(f"Plot saved to {OUT_DIR}/vector_tensor_mismatch_plot.png")
