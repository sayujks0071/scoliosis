#!/usr/bin/env python3
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import requests
import scipy.io.wavfile as wav

# Add afcc to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../research/alphafold_countercurvature/src')))
try:
    from afcc.metrics import MetricsAnalyzer
    from afcc.structure import StructureParser
except ImportError:
    # Fallback
    sys.path.append(os.path.abspath('research/alphafold_countercurvature/src'))
    from afcc.metrics import MetricsAnalyzer
    from afcc.structure import StructureParser

TEMP_DIR = "temp/afdb"
OUTPUT_DIR = "outputs/protein_sonification"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_pdb(uniprot_id):
    pdb_path = os.path.join(TEMP_DIR, f"{uniprot_id}.pdb")
    if os.path.exists(pdb_path):
        return pdb_path

    print(f"Fetching {uniprot_id}...")
    api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
    try:
        resp = requests.get(api_url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data: return None
        pdb_url = data[0]['pdbUrl']
        pdb_resp = requests.get(pdb_url)
        with open(pdb_path, 'wb') as f:
            f.write(pdb_resp.content)
        return pdb_path
    except Exception as e:
        print(e)
        return None

def sonify_protein(uniprot_id, symbol):
    pdb_path = fetch_pdb(uniprot_id)
    if not pdb_path:
        print(f"Failed to fetch {symbol}")
        return

    parser = StructureParser()
    analyzer = MetricsAnalyzer()

    coords, plddt, resnames = parser.fast_parse_pdb_arrays(Path(pdb_path))

    # Calculate metrics
    kappa = analyzer.calculate_curvature(coords)
    tau = analyzer.calculate_torsion(coords)

    # Clean NaNs
    kappa = np.nan_to_num(kappa, nan=0.0)
    tau = np.nan_to_num(tau, nan=0.0)

    # Generate Audio
    sample_rate = 44100
    duration_per_res = 0.05 # 50ms
    n_res = len(coords)
    total_samples = int(n_res * duration_per_res * sample_rate)

    t = np.linspace(0, n_res * duration_per_res, total_samples)

    # Interpolate metrics to audio time
    t_res = np.linspace(0, n_res * duration_per_res, n_res)

    # Map Curvature to Pitch (200 - 800 Hz)
    # Clamp curvature to reasonable range (0 - 1.0)
    k_clamp = np.clip(kappa, 0, 1.0)
    freqs = 200 + k_clamp * 600
    freq_interp = np.interp(t, t_res, freqs)

    # Map pLDDT to Amplitude (0.0 - 1.0)
    amp_vals = plddt / 100.0
    amp_interp = np.interp(t, t_res, amp_vals)

    # Map Torsion to Pan (-1 to 1)
    # Torsion is in radians (-pi to pi)
    pan_vals = np.clip(tau / np.pi, -1.0, 1.0)
    pan_interp = np.interp(t, t_res, pan_vals)

    # Generate Phase
    phase = 2 * np.pi * np.cumsum(freq_interp) / sample_rate

    # Generate Stereo Signal
    raw_signal = np.sin(phase)

    # Apply Envelope (Click removal between residues?)
    # No, continuous is better for "melody"

    left = raw_signal * amp_interp * (1 - pan_interp) * 0.5
    right = raw_signal * amp_interp * (1 + pan_interp) * 0.5

    stereo_signal = np.vstack((left, right)).T

    # Save WAV
    wav_path = os.path.join(OUTPUT_DIR, f"{symbol}_{uniprot_id}.wav")
    stereo_int16 = np.int16(stereo_signal * 32767)
    wav.write(wav_path, sample_rate, stereo_int16)
    print(f"Saved {wav_path}")

    # Plot Spectrogram
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(kappa, label='Curvature')
    plt.plot(plddt/100, label='Confidence', alpha=0.5)
    plt.title(f"Protein Melody Score: {symbol}")
    plt.legend()
    plt.xlim(0, n_res)

    plt.subplot(2, 1, 2)
    plt.specgram(left + right, Fs=sample_rate, NFFT=1024, noverlap=512, cmap='inferno')
    plt.ylabel("Frequency (Hz)")
    plt.xlabel("Time (s)")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"{symbol}_spectrogram.png"))
    plt.close()

if __name__ == "__main__":
    # Test with PIEZO2 (Strut) and LBX1 (Signaling)
    proteins = [
        ("PIEZO2", "Q9H5I5"),
        ("LBX1", "P52954")
    ]

    for sym, uid in proteins:
        sonify_protein(uid, sym)
