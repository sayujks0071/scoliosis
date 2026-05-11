#!/usr/bin/env python3
"""
Spine Sonification Experiment.

This script runs a short Cosserat rod simulation where the spine transitions
from straight to an S-shape (simulating scoliosis onset). It extracts the
curvature data over time and maps it to audio frequencies, creating a
sonification of the buckling instability.
"""

import os
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import scipy.io.wavfile as wav

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from spinalmodes.countercurvature.api import CounterCurvatureParams, InfoField1D
from spinalmodes.model.solvers.cosserat import available, simulate_cosserat


def setup_simulation():
    """Sets up the parameters for the buckling simulation."""
    length = 0.5
    n_elements = 40

    # 1. Setup Info Field (Gaussian bump to define the "Information Spine")
    s = np.linspace(0, length, n_elements + 1)
    I = 0.5 + 0.5 * np.exp(-0.5 * ((s - 0.5 * length) / (0.1 * length)) ** 2)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Initial Params (High growth to induce buckling)
    params = CounterCurvatureParams(
        chi_kappa=15.0,  # High coupling to induce S-shape
        chi_tau=0.0,
        chi_E=0.0,
        chi_M=0.0,
        scale_length=length,
    )

    # 3. Geometric Setup
    kappa_gen = np.zeros((3, n_elements + 1))
    kappa_gen[1, :] = 2.0  # Natural Kyphosis
    kappa_gen[0, :] = 0.1  # Small Lateral Defect to seed buckling

    sim_params = {
        "info": info,
        "iec_params": params,
        "length": length,
        "n_elements": n_elements,
        "final_time": 2.0,
        "dt": 1e-4,
        "gravity": 9.81,
        "kappa_gen": kappa_gen,
        "save_every": 200,  # Save every 0.02s
        "damping_constant": 5.0
    }

    return sim_params

def sonify_curvature(time_arr, kappa_arr, out_path, sample_rate=44100):
    """
    Converts a time-series of curvature profiles into an audio signal.

    Args:
        time_arr: 1D array of simulation times.
        kappa_arr: array of curvature (time, node) or (time, node, dim).
        out_path: Path to save the WAV file.
    """
    # handle both 2D (time, node) and 3D (time, node, dim)
    if len(kappa_arr.shape) == 2:
        n_time, n_nodes = kappa_arr.shape
        # Add a dummy dimension so we can treat it uniformly
        kappa_arr = np.expand_dims(kappa_arr, axis=-1)
    else:
        n_time, n_nodes, _ = kappa_arr.shape

    # We want the audio to last a few seconds, let's say 10 seconds total.
    audio_duration = 10.0
    total_samples = int(audio_duration * sample_rate)

    # Audio time axis
    t_audio = np.linspace(0, audio_duration, total_samples)

    # Map simulation time to audio time
    t_sim_norm = time_arr / time_arr[-1]
    t_audio_norm = t_audio / audio_duration

    # We will represent the spine as a sum of oscillators (one for each node).
    # The fundamental frequency will be mapped from the node's position along the spine.
    # The amplitude of each oscillator will be modulated by the local curvature magnitude.

    # Base frequencies for nodes (e.g., C major scale spread out)
    # Using a harmonic series or just a linear spread
    f_min = 100.0
    f_max = 800.0
    node_freqs = np.linspace(f_min, f_max, n_nodes)

    # We will calculate the total magnitude of curvature at each node
    # kappa is (time, node, dim=3). Magnitude is norm over dim=2.
    kappa_mag = np.linalg.norm(kappa_arr, axis=2)

    # Normalize curvature magnitude globally to [0, 1] for amplitude mapping
    max_k = np.max(kappa_mag)
    if max_k > 0:
        kappa_norm = kappa_mag / max_k
    else:
        kappa_norm = kappa_mag

    signal = np.zeros(total_samples)

    for i in range(n_nodes):
        # Interpolate the curvature amplitude for this node to the audio timescale
        amp_interp = np.interp(t_audio_norm, t_sim_norm, kappa_norm[:, i])

        # We can also slightly frequency-modulate based on lateral curvature (dim=0)
        # to add "dissonance" when it buckles laterally.
        lat_k = kappa_arr[:, i, 0]
        # Normalize lateral curvature
        max_lat = np.max(np.abs(lat_k)) if np.max(np.abs(lat_k)) > 0 else 1.0
        lat_norm = lat_k / max_lat
        lat_interp = np.interp(t_audio_norm, t_sim_norm, lat_norm)

        # Base frequency for this node
        f_base = node_freqs[i]

        # Modulated frequency: add up to 5% detuning based on lateral buckling
        f_inst = f_base * (1.0 + 0.05 * lat_interp)

        # Phase integration
        phase = 2.0 * np.pi * np.cumsum(f_inst) / sample_rate

        # Add to mix, weighting amplitude by amp_interp.
        # Add a baseline amplitude so straight spine makes a harmonious hum
        node_signal = np.sin(phase) * (0.1 + 0.9 * amp_interp)

        signal += node_signal

    # Normalize signal to prevent clipping
    max_amp = np.max(np.abs(signal))
    if max_amp > 0:
        signal = signal / max_amp

    # Fade in and fade out
    fade_len = int(0.1 * sample_rate)
    fade_in = np.linspace(0, 1, fade_len)
    fade_out = np.linspace(1, 0, fade_len)
    signal[:fade_len] *= fade_in
    signal[-fade_len:] *= fade_out

    # Save to WAV
    stereo_int16 = np.int16(signal * 32767)
    wav.write(out_path, sample_rate, stereo_int16)
    print(f"Saved audio to {out_path}")

def plot_spectrogram(audio_path, out_path):
    """Plots the spectrogram of the generated audio."""
    sample_rate, data = wav.read(audio_path)
    # If stereo, use one channel
    if len(data.shape) > 1:
        data = data[:, 0]

    plt.figure(figsize=(10, 6))
    plt.specgram(data, Fs=sample_rate, NFFT=1024, noverlap=512, cmap='inferno')
    plt.title("Spectrogram of Spinal Buckling")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.colorbar(label='Intensity')
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"Saved spectrogram to {out_path}")

def run_experiment():
    if not available():
        print("Error: PyElastica not available. Cannot run simulation.")
        return

    print("Setting up simulation...")
    sim_params = setup_simulation()

    print("Running Cosserat simulation (this may take a minute)...")
    res = simulate_cosserat(sim_params)

    if not res["ok"]:
        print(f"Simulation failed: {res['reason']}")
        return

    data = res["result"]
    time_arr = data["time"]
    kappa_arr = data["curvature"]

    # kappa_arr shape from PyElastica wrapper is usually (time, nodes, dim)
    # Let's verify shape. If it's (time, dim, nodes), we transpose it.
    if len(kappa_arr.shape) == 3 and kappa_arr.shape[1] == 3:
        # It's (time, dim, nodes), transpose to (time, nodes, dim)
        kappa_arr = np.transpose(kappa_arr, (0, 2, 1))

    print(f"Simulation complete. Time steps: {len(time_arr)}, Nodes: {kappa_arr.shape[1]}")

    # Create output directory
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join("outputs", "sim", f"{today}_spine_sonification")
    os.makedirs(out_dir, exist_ok=True)

    audio_path = os.path.join(out_dir, "spinal_buckling.wav")
    spec_path = os.path.join(out_dir, "spectrogram.png")

    print("Sonifying curvature data...")
    sonify_curvature(time_arr, kappa_arr, audio_path)

    print("Generating spectrogram...")
    plot_spectrogram(audio_path, spec_path)

    # Generate a brief report
    report_path = os.path.join(out_dir, "report.md")
    with open(report_path, "w") as f:
        f.write("# Spine Sonification: Hearing the Instability\n\n")
        f.write("This experiment maps the dynamic curvature of a buckling Cosserat rod to audio signals.\n\n")
        f.write("## Methodology\n")
        f.write("A spine is modeled using PyElastica with a high Information-Elasticity Coupling (chi_kappa=15.0). ")
        f.write("As it buckles under gravity, the resulting S-shape curvature is extracted over time. ")
        f.write("Each node along the spine is assigned a base frequency. The amplitude of that frequency is modulated ")
        f.write("by the local curvature magnitude, and the frequency itself is slightly detuned based on the lateral curvature.\n\n")
        f.write("## Results\n")
        f.write("The generated audio begins as a harmonious chord (representing the straight, kyphotic spine) and ")
        f.write("transitions into a dissonant, complex soundscape as the lateral buckling instability (scoliosis) takes hold.\n\n")
        f.write("## Files\n")
        f.write("- Audio: `spinal_buckling.wav`\n")
        f.write("- Spectrogram: `spectrogram.png`\n")
    print(f"Saved report to {report_path}")

if __name__ == "__main__":
    run_experiment()
