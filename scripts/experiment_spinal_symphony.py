#!/usr/bin/env python3
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.io.wavfile as wav


def higuchi_fd(x, kmax):
    """Calculates the Higuchi Fractal Dimension of a time series x."""
    n_times = x.size
    lk = np.empty(kmax)
    x_reg = np.array(x)
    for k in range(1, kmax + 1):
        lm = np.empty((k,))
        for m in range(k):
            ll = 0
            n_max = int(np.floor((n_times - m - 1) / k))
            n_max = int(n_max)
            for j in range(1, n_max):
                ll += abs(x_reg[m + j * k] - x_reg[m + (j - 1) * k])
            ll /= k
            ll *= (n_times - 1) / (k * n_max)
            lm[m] = ll
        lk[k - 1] = np.mean(lm)

    ln_lk = np.log(lk)
    ln_k = np.log(1.0 / np.arange(1, kmax + 1))

    # Fit line
    slope, _ = np.polyfit(ln_k, ln_lk, 1)
    return slope

def sonify_series(time, frequency_data, amplitude_data, duration_sec=10.0, sample_rate=44100):
    """
    Generates an audio signal from time-series data.
    time: array of time points (e.g. simulation hours)
    frequency_data: array of values to map to frequency (e.g. curvature)
    amplitude_data: array of values to map to amplitude (e.g. torsion)
    """

    # Normalize data
    # Map curvature to 200-800Hz
    min_freq = 200
    max_freq = 800
    norm_freq = (frequency_data - np.min(frequency_data)) / (np.max(frequency_data) - np.min(frequency_data) + 1e-6)
    freqs = min_freq + norm_freq * (max_freq - min_freq)

    # Map torsion to 0.1-0.8 amplitude
    min_amp = 0.1
    max_amp = 0.8
    norm_amp = (amplitude_data - np.min(amplitude_data)) / (np.max(amplitude_data) - np.min(amplitude_data) + 1e-6)
    amps = min_amp + norm_amp * (max_amp - min_amp)

    # Generate samples
    n_samples = int(duration_sec * sample_rate)
    t_audio = np.linspace(0, duration_sec, n_samples)

    # Interpolate data to audio time
    # Normalize input time to 0-duration
    t_norm = (time - np.min(time)) / (np.max(time) - np.min(time)) * duration_sec

    freq_interp = np.interp(t_audio, t_norm, freqs)
    amp_interp = np.interp(t_audio, t_norm, amps)

    # Integrate frequency to get phase
    phase = 2 * np.pi * np.cumsum(freq_interp) / sample_rate

    # Generate signal
    signal = amp_interp * np.sin(phase)

    return t_audio, signal

def main():
    input_file = "outputs/spinal_jetlag/jetlag_cycles.csv"
    output_dir = "outputs/spinal_symphony"
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    df = pd.read_csv(input_file)

    # Process each condition
    conditions = df['condition'].unique()

    plt.figure(figsize=(15, 10))

    for i, condition in enumerate(conditions):
        subset = df[df['condition'] == condition]
        if subset.empty:
            continue

        time = subset['t_hours'].values
        cobb = subset['cobb_angle'].values
        torsion = subset['max_torsion'].values

        # Calculate Higuchi Fractal Dimension
        # HFD needs a longer series, but let's try with what we have
        # Or interpolate to get more points
        # Interpolate to 1000 points for HFD calculation
        if len(cobb) > 10:
            from scipy.interpolate import interp1d
            f = interp1d(time, cobb, kind='cubic')
            t_new = np.linspace(min(time), max(time), 1000)
            cobb_interp = f(t_new)
            hfd = higuchi_fd(cobb_interp, kmax=10)
        else:
            hfd = 0.0

        print(f"Condition: {condition}, HFD: {hfd:.4f}")

        # Sonify
        duration = 5.0 # 5 seconds per condition
        t_audio, signal = sonify_series(time, cobb, torsion, duration_sec=duration)

        # Save WAV
        wav_path = os.path.join(output_dir, f"{condition}.wav")
        # Normalize to 16-bit PCM
        signal_int16 = np.int16(signal / np.max(np.abs(signal)) * 32767)
        wav.write(wav_path, 44100, signal_int16)
        print(f"Saved audio to {wav_path}")

        # Plot Spectrogram
        plt.subplot(len(conditions), 1, i+1)
        plt.specgram(signal, Fs=44100, NFFT=1024, noverlap=512, cmap='inferno')
        plt.title(f"Spectrogram: {condition} (HFD={hfd:.2f})")
        plt.ylabel("Frequency (Hz)")
        if i == len(conditions) - 1:
            plt.xlabel("Time (s)")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "spinal_spectrograms.png"))
    print(f"Saved spectrograms to {os.path.join(output_dir, 'spinal_spectrograms.png')}")

if __name__ == "__main__":
    main()
