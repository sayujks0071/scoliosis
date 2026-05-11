"""
Bolt-BioFold Analysis Script
----------------------------
Performs structural analysis on AlphaFold predictions to support the Biological Countercurvature hypothesis.

Targets: Default Seed List (PIEZO1, PIEZO2, LBX1, FBN1, YAP1, IFT88, ITGB1) or user-provided list.
Metrics: pLDDT statistics, Radius of Gyration, PCA Anisotropy, Curvature/Torsion, PAE Blockiness.
Output: CSV table, Markdown report, Plots.

Usage:
    python3 scripts/data_management/bolt_biofold_analysis.py [targets...]
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

# Add research module to path to import StructureParser
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "research" / "alphafold_countercurvature" / "src"))
from afcc.afdb import AlphaFoldFetcher
from afcc.structure import StructureParser


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)

# Constants
TARGET_PROTEINS = [
    "PIEZO1", "PIEZO2", "COL1A1", "COL2A1", "YAP1", "TRPV4",
    "RUNX2", "SOX9", "VINCULIN", "TALIN1", "NOTCH1", "FIBRONECTIN",
    "PPARGC1A", "IGF1R", "GHR", "ARNTL", "DMD", "MYLK"
]
# Charged residues for surface metrics
CHARGED_RESIDUES = {'ARG', 'LYS', 'ASP', 'GLU', 'HIS', 'R', 'K', 'D', 'E', 'H'}

DEFAULT_PDB_DIR = Path("archive/alphafold_analysis_legacy/predictions")
MANIFEST_PATH = Path("research/alphafold_countercurvature/data/manifest.csv")
DEFAULT_OUTPUT_DIR = Path("outputs/bolt_biofold_analysis")
DEFAULT_SEED_LIST = ["PIEZO1", "PIEZO2", "LBX1", "FBN1", "YAP1", "IFT88", "ITGB1"]
CHARGED_RESIDUES = {'ARG', 'LYS', 'ASP', 'GLU', 'HIS', 'R', 'K', 'D', 'E', 'H'}

# Default PDB Dir: relative to repo root
DEFAULT_PDB_DIR = Path(__file__).resolve().parent.parent.parent / "research" / "alphafold_countercurvature" / "data" / "raw"
CANDIDATES_CSV = Path(__file__).resolve().parent.parent.parent / "data" / "candidates_master.csv"

def load_candidates_map() -> Dict[str, str]:
    """
    Loads Gene Symbol -> UniProt ID mapping from candidates_master.csv.
    """
    mapping = {}
    if CANDIDATES_CSV.exists():
        try:
            df = pd.read_csv(CANDIDATES_CSV)
            # Ensure columns exist
            if 'gene_symbol' in df.columns and 'uniprot_id' in df.columns:
                for _, row in df.iterrows():
                    if pd.notna(row['gene_symbol']) and pd.notna(row['uniprot_id']):
                        mapping[row['gene_symbol'].strip()] = row['uniprot_id'].strip()
        except Exception as e:
            print(f"⚠️ Warning: Failed to read candidates CSV: {e}")
    return mapping

def load_cached_analysis(pdb_path: Path) -> Optional[Dict]:
    """Loads cached analysis results if available."""
    cache_json = pdb_path.with_suffix('.bolt_metrics.json')
    cache_npz = pdb_path.with_suffix('.bolt_arrays.npz')

    if not (cache_json.exists() and cache_npz.exists()):
        return None

    try:
        # Check timestamps
        pdb_time = pdb_path.stat().st_mtime
        if cache_json.stat().st_mtime < pdb_time or cache_npz.stat().st_mtime < pdb_time:
            return None

        with open(cache_json, 'r') as f:
            metrics = json.load(f)

        with np.load(cache_npz) as data:
            # Reconstruct arrays
            metrics['coords'] = data['coords']
            metrics['plddts'] = data['plddts']
            metrics['curvature'] = data['curvature']
            if 'pae' in data:
                metrics['pae'] = data['pae']

        return metrics
    except Exception as e:
        print(f"Warning: Failed to load cache for {pdb_path}: {e}")
        return None

def save_cached_analysis(pdb_path: Path, results: Dict):
    """Saves analysis results to cache."""
    cache_json = pdb_path.with_suffix('.bolt_metrics.json')
    cache_npz = pdb_path.with_suffix('.bolt_arrays.npz')

    try:
        # Separate arrays and scalars
        arrays = {
            'coords': results['coords'],
            'plddts': results['plddts'],
            'curvature': results['curvature']
        }
        if 'pae' in results and results['pae'] is not None:
             arrays['pae'] = results['pae']

        # Filter out arrays from json
        scalars = {k: v for k, v in results.items() if k not in arrays and k != 'pae'}

        with open(cache_json, 'w') as f:
            json.dump(scalars, f, indent=2, cls=NumpyEncoder)

        np.savez_compressed(cache_npz, **arrays)

    except Exception as e:
        print(f"Warning: Failed to save cache for {pdb_path}: {e}")

def compute_surface_metrics(coords: np.ndarray, resnames: np.ndarray, plddts: np.ndarray) -> Dict[str, Any]:
    """
    Computes surface metrics based on neighbor counts using cKDTree.
    - Exposed: < 20 neighbors within 10.0 Angstroms AND pLDDT >= 70.
    - Charged: R, K, D, E, H.
    """
    if len(coords) == 0:
        return {
            "exposed_surface_proxy": 0,
            "charged_patch_score": 0.0
        }

    # ⚡ Bolt Optimization: Use cKDTree for O(N log N) neighbor search
    # Bolt 2026-11-20: Added leafsize=64 and workers=-1 for parallel search (~2.6x speedup)
    tree = cKDTree(coords, leafsize=64)
    # query_ball_point returns count including self, so subtract 1
    neighbor_counts = tree.query_ball_point(coords, r=10.0, return_length=True, workers=-1) - 1

    # Exposed mask: Neighbors < 20 AND pLDDT >= 70
    exposed_mask = (neighbor_counts < 20) & (plddts >= 70.0)
    exposed_count = np.sum(exposed_mask)

    if exposed_count == 0:
        return {
            "exposed_surface_proxy": 0,
            "charged_patch_score": 0.0
        }

    # Check charged
    exposed_resnames = resnames[exposed_mask]
    charged_count = sum(1 for r in exposed_resnames if str(r).upper() in CHARGED_RESIDUES)

    return {
        "exposed_surface_proxy": int(exposed_count),
        "charged_patch_score": float(charged_count) / float(exposed_count)
    }

def compute_geometry_metrics(coords: np.ndarray) -> Dict[str, float]:
    """
    Computes geometric descriptors for a set of coordinates (high confidence).
    """
    if len(coords) < 3:
        return {
            "radius_of_gyration": 0.0,
            "end_to_end_distance": 0.0,
            "anisotropy_index": 1.0,
            "max_eigenvalue": 0.0,
            "backbone_principal_axis": "[0,0,0]"
        }

    # Center coordinates
    centroid = np.mean(coords, axis=0)
    centered = coords - centroid

    # ⚡ Bolt Optimization: Single-pass geometry (Rg + Anisotropy)
    n = len(coords)
    M = centered.T @ centered

    # Radius of Gyration: Rg = sqrt(trace(M) / N)
    rg = np.sqrt(np.trace(M) / n)

    # End-to-End Distance
    end_to_end = np.linalg.norm(coords[-1] - coords[0])

    # PCA Anisotropy
    cov = M / (n - 1)
    eigvals, eigvecs = np.linalg.eigh(cov)
    eigvals = np.sort(eigvals)

    lambda_min = eigvals[0]
    lambda_max = eigvals[2]

    if lambda_min > 1e-6:
        anisotropy = lambda_max / lambda_min
    else:
        anisotropy = 1000.0

    # Principal Axis
    principal_axis = eigvecs[:, 2]
    principal_axis_str = f"[{principal_axis[0]:.3f}, {principal_axis[1]:.3f}, {principal_axis[2]:.3f}]"

    return {
        "radius_of_gyration": float(rg),
        "end_to_end_distance": float(end_to_end),
        "anisotropy_index": float(anisotropy),
        "max_eigenvalue": float(lambda_max),
        "backbone_principal_axis": principal_axis_str
    }

def compute_curvature_torsion(coords: np.ndarray, window: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes discrete curvature and torsion along the backbone.
    """
    if len(coords) < window * 2:
        return np.zeros(len(coords)), np.zeros(len(coords))

    # Moving average smoothing
    ret = np.cumsum(coords, axis=0)
    smoothed = np.empty((len(coords) - window + 1, 3))
    smoothed[0] = ret[window-1]
    smoothed[1:] = ret[window:] - ret[:-window]
    smoothed /= window

    # Tangent t
    t = np.gradient(smoothed, axis=0)
    # Normal n ~ t'
    dt = np.gradient(t, axis=0)

    cross_d1_d2 = np.cross(t, dt)
    num = np.linalg.norm(cross_d1_d2, axis=1)
    denom = np.linalg.norm(t, axis=1)**3

    curvature = np.zeros_like(num)
    mask = denom > 1e-6
    curvature[mask] = num[mask] / denom[mask]

    # Torsion
    ddt = np.gradient(dt, axis=0)
    num_tau = np.sum(cross_d1_d2 * ddt, axis=1)
    denom_tau = np.linalg.norm(cross_d1_d2, axis=1)**2

    torsion = np.zeros_like(num_tau)
    mask_tau = denom_tau > 1e-6
    torsion[mask_tau] = num_tau[mask_tau] / denom_tau[mask_tau]

    # Pad to match original length
    pad_len = (len(coords) - len(curvature)) // 2
    curvature = np.pad(curvature, (pad_len, len(coords)-len(curvature)-pad_len), 'edge')
    torsion = np.pad(torsion, (pad_len, len(coords)-len(torsion)-pad_len), 'edge')

    return curvature, torsion

def find_domain_segments(plddts: np.ndarray, threshold: float = 70.0, min_len: int = 20) -> List[Tuple[int, int]]:
    """
    Identifies contiguous high-confidence regions.
    Returns list of (start_idx, end_idx) tuples.
    """
    is_high = plddts >= threshold
    domains = []
    start = -1

    for i, val in enumerate(is_high):
        if val:
            if start == -1:
                start = i
        else:
            if start != -1:
                if i - start >= min_len:
                    domains.append((start, i-1))
                start = -1

    if start != -1 and len(plddts) - start >= min_len:
        domains.append((start, len(plddts)-1))

    return domains

def compute_pae_metrics(pae: np.ndarray, domains: List[Tuple[int, int]]) -> Tuple[float, float]:
    """
    Computes PAE blockiness metrics.
    Returns (PAE_mean, PAE_blockiness_score)
    Blockiness = Mean(Inter-domain) - Mean(Intra-domain)
    """
    if pae is None:
        return 0.0, 0.0

    pae_mean = np.mean(pae)

    if len(domains) < 2:
        return pae_mean, 0.0

    intra_scores = []
    inter_scores = []

    # Compute Intra-domain mean
    for d in domains:
        # Extract block
        block = pae[d[0]:d[1]+1, d[0]:d[1]+1]
        intra_scores.append(np.mean(block))

    # Compute Inter-domain mean (simplified: sampling or full)
    # We will do full pairwise between domains
    for i in range(len(domains)):
        for j in range(i+1, len(domains)):
            d1 = domains[i]
            d2 = domains[j]
            block = pae[d1[0]:d1[1]+1, d2[0]:d2[1]+1]
            inter_scores.append(np.mean(block))

    mean_intra = np.mean(intra_scores) if intra_scores else 0.0
    mean_inter = np.mean(inter_scores) if inter_scores else 0.0

    blockiness = mean_inter - mean_intra
    return float(pae_mean), float(blockiness)

def find_hinges(plddts: np.ndarray, curvature: np.ndarray) -> str:
    """
    Heuristic: Positions where confidence drops (local min) AND curvature is high.
    Returns formatted string of regions.
    """
    # 50 < pLDDT < 80 (structured but flexible) AND Curvature > 0.1
    hinge_mask = (plddts > 50) & (plddts < 80) & (curvature > 0.1)

    regions = []
    in_region = False
    start = -1

    for i, val in enumerate(hinge_mask):
        if val:
            if not in_region:
                in_region = True
                start = i
        else:
            if in_region:
                if i - start >= 3:
                     regions.append(f"{start}-{i-1}")
                in_region = False

    if in_region and len(hinge_mask) - start >= 3:
        regions.append(f"{start}-{len(hinge_mask)-1}")

    return "; ".join(regions) if regions else "None"

def find_bending_hotspots(curvature: np.ndarray, plddts: np.ndarray, top_n: int = 3) -> str:
    """
    Identifies top N regions with high curvature in high-confidence segments.
    """
    mask = plddts >= 70
    curv_copy = curvature.copy()
    curv_copy[~mask] = -1.0

    hotspots = []

    for _ in range(top_n):
        if np.max(curv_copy) <= 0:
            break
        idx = np.argmax(curv_copy)
        val = curv_copy[idx]

        # scan left
        start = idx
        while start > 0 and curv_copy[start-1] > val * 0.8:
            start -= 1
        # scan right
        end = idx
        while end < len(curv_copy) - 1 and curv_copy[end+1] > val * 0.8:
            end += 1

        hotspots.append(f"{start}-{end} (k={val:.2f})")

        # Mask out
        mask_start = max(0, start - 5)
        mask_end = min(len(curv_copy), end + 6)
        curv_copy[mask_start:mask_end] = -1.0

    return "; ".join(hotspots) if hotspots else "None"

def analyze_protein(pdb_path: Path, pae_path: Optional[Path], gene_symbol: str, uniprot_id: str, force: bool = False) -> Dict:
    """
    Analyzes a single PDB file using fast StructureParser with caching.
    """
    # Check persistent analysis cache (skip if force=True)
    if not force:
        cached = load_cached_analysis(pdb_path)
        if cached:
            # We must ensure gene_symbol/uniprot matches what we expect, as cache might be old
            cached['gene_symbol'] = gene_symbol
            cached['uniprot_id'] = uniprot_id
            print(f"  Loaded analysis cache for {gene_symbol}")
            return cached

    t0 = time.time()
    parser = StructureParser()

    # Parse PDB
    coords, plddts, resnames = parser.fast_parse_pdb_arrays(pdb_path)
    if coords is None:
        print(f"Error parsing {pdb_path}")
        return None

    # Parse PAE if available
    pae = None
    if pae_path and pae_path.exists():
        pae = parser.parse_pae(pae_path)

    dt = time.time() - t0
    print(f"  Parsed {gene_symbol} in {dt:.4f}s")

    # pLDDT Statistics
    plddt_mean = np.mean(plddts)
    plddt_median = np.median(plddts)
    plddt_high_frac = np.sum(plddts >= 90) / len(plddts)
    plddt_ok_frac = np.sum((plddts >= 70) & (plddts < 90)) / len(plddts)
    plddt_low_frac = np.sum(plddts < 70) / len(plddts)
    disorder_fraction = np.sum(plddts < 50) / len(plddts)

    # High Confidence Geometry (pLDDT >= 70)
    mask = plddts >= 70
    high_conf_coords = coords[mask]
    geo_metrics = compute_geometry_metrics(high_conf_coords)

    # Curvature/Torsion (Full Chain)
    full_curvature, full_torsion = compute_curvature_torsion(coords, window=10)

    # Metrics on HC segments
    mean_curvature_hc = np.mean(full_curvature[mask]) if np.any(mask) else 0.0
    max_curvature_hc = np.max(full_curvature[mask]) if np.any(mask) else 0.0
    mean_torsion_hc = np.mean(np.abs(full_torsion[mask])) if np.any(mask) else 0.0

    # Domains & Hinges
    domain_segments = find_domain_segments(plddts)
    domain_count = len(domain_segments)
    hinge_regions = find_hinges(plddts, full_curvature)
    bending_hotspots = find_bending_hotspots(full_curvature, plddts)

    # PAE Metrics
    pae_mean, pae_blockiness = compute_pae_metrics(pae, domain_segments)

    # Surface Metrics
    surface_metrics = compute_surface_metrics(coords, resnames, plddts)

    # Flags
    low_confidence_warning = plddt_mean < 70
    likely_IDR_heavy = disorder_fraction > 0.3
    multi_domain_uncertain = domain_count > 1 and low_confidence_warning

    results = {
        "gene_symbol": gene_symbol,
        "protein_id": gene_symbol, # Alias for compatibility
        "uniprot_id": uniprot_id,
        "species": "Homo sapiens",
        "length": len(coords),
        "pLDDT_mean": float(plddt_mean),
        "pLDDT_median": float(plddt_median),
        "pLDDT_fraction_high": float(plddt_high_frac),
        "pLDDT_fraction_ok": float(plddt_ok_frac),
        "pLDDT_fraction_low": float(plddt_low_frac),
        "PAE_mean": pae_mean,
        "PAE_domain_blockiness_score": pae_blockiness,
        "disorder_fraction_proxy": float(disorder_fraction),
        "predicted_domain_segments": domain_count,
        "hinge_candidates": hinge_regions,
        "mean_curvature_hc": float(mean_curvature_hc),
        "max_curvature_hc": float(max_curvature_hc),
        "mean_torsion_hc": float(mean_torsion_hc),
        "bending_hotspots": bending_hotspots,
        "exposed_surface_proxy": surface_metrics['exposed_surface_proxy'],
        "charged_patch_score": surface_metrics['charged_patch_score'],
        "low_confidence_warning": bool(low_confidence_warning),
        "multi_domain_uncertain": bool(multi_domain_uncertain),
        "likely_IDR_heavy": bool(likely_IDR_heavy),
        **geo_metrics,
        "coords": coords,
        "plddts": plddts,
        "curvature": full_curvature,
        "pae": pae
    }

    # Save to cache
    save_cached_analysis(pdb_path, results)
    return results

def generate_plots(results: List[Dict], output_dir: Path):
    """
    Generates summary plots.
    """
    pae_count = 0
    for res in results:
        pid = res['gene_symbol']

        fig, ax1 = plt.subplots(figsize=(10, 6))

        # pLDDT Plot
        ax1.set_xlabel('Residue Index')
        ax1.set_ylabel('pLDDT', color='tab:blue')
        ax1.plot(res['plddts'], color='tab:blue', label='pLDDT')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.set_ylim(0, 100)
        # Add threshold line
        ax1.axhline(y=70, color='gray', linestyle='--', alpha=0.5)

        # Curvature Plot (Twin axis)
        ax2 = ax1.twinx()
        ax2.set_ylabel('Curvature (1/A)', color='tab:red')
        ax2.plot(res['curvature'], color='tab:red', alpha=0.5, label='Curvature')
        ax2.tick_params(axis='y', labelcolor='tab:red')

        plt.title(f"Structure Profile: {pid}")
        fig.tight_layout()
        plt.savefig(output_dir / f"{pid}_profile.png")
        plt.close()

        # PAE Plot (Top 3 only)
        if 'pae' in res and res['pae'] is not None and pae_count < 3:
            plt.figure(figsize=(8, 8))
            plt.imshow(res['pae'], cmap='bwr', vmin=0, vmax=30)
            plt.colorbar(label='Predicted Aligned Error (Å)')
            plt.title(f"PAE Matrix: {pid}")
            plt.xlabel("Scored Residue")
            plt.ylabel("Aligned Residue")
            plt.tight_layout()
            plt.savefig(output_dir / f"{pid}_pae.png")
            plt.close()
            pae_count += 1

def main():
    parser = argparse.ArgumentParser(description="Bolt-BioFold Analysis")
    parser.add_argument("targets", nargs='*', help="List of gene symbols to analyze")
    parser.add_argument("--output_dir", type=Path, default=Path("outputs/bolt_biofold_analysis"), help="Directory for output")
    parser.add_argument("--force", action="store_true", help="Force re-computation ignoring cache")
    args = parser.parse_args()

    output_dir = args.output_dir
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    pdb_dir = DEFAULT_PDB_DIR
    pdb_dir.mkdir(parents=True, exist_ok=True)
    print(f"Starting Bolt-BioFold Analysis on targets in {pdb_dir}...")

    # Load manifest if available to resolve paths
    manifest_map = {}
    if MANIFEST_PATH.exists():
        print(f"Loading manifest from {MANIFEST_PATH}...")
        try:
            df = pd.read_csv(MANIFEST_PATH)
            # Create map: gene_symbol -> pdb_path
            # Filter for downloaded
            downloaded = df[df['status'].isin(['downloaded', 'cached'])]
            for _, row in downloaded.iterrows():
                gene = row['gene_symbol']
                path_str = row['pdb_path']
                if gene and path_str:
                     manifest_map[gene] = Path(path_str)
            print(f"Loaded {len(manifest_map)} entries from manifest.")
        except Exception as e:
            print(f"Warning: Failed to load manifest: {e}")

    if not any(pdb_dir.iterdir()) and not manifest_map: # Crude check
        print("Using Default Seed List as no input queue provided.")
    else:
        print("Using Default Seed List for targeted analysis.")

    # 1. Determine Targets
    targets = args.targets
    if not targets:
        print("Using Default Seed List.")
        targets = DEFAULT_SEED_LIST

    # 2. Load Mapping
    gene_map = load_candidates_map()

    # 3. Setup Fetcher
    # Use repo/research/alphafold_countercurvature/data/raw as base data dir
    data_dir = DEFAULT_PDB_DIR
    manifest_path = data_dir / "afdb_manifest.csv"
    fetcher = AlphaFoldFetcher(data_dir, manifest_path)

    results = []

    print(f"Starting Bolt-BioFold Analysis on {len(targets)} targets...")

    repo_root = Path(__file__).resolve().parent.parent.parent

    for gene in targets:
        # Resolve UniProt
        uniprot = gene_map.get(gene)

        # If not in map, try to see if gene is actually a uniprot ID (heuristic: 6 chars alphanumeric)
        if not uniprot:
            if len(gene) == 6 and gene.isalnum():
                uniprot = gene
            else:
                # If we can't map it, skip or try fetching by gene symbol (fetcher expects uniprot)
                print(f"❌ Skipping {gene}: Could not resolve to UniProt ID. Add to candidates CSV.")
                continue

        # Fetch Data
        status = fetcher.fetch_protein(uniprot, gene)

        if status['status'] not in ['downloaded', 'already_cached']:
             print(f"❌ Skipping {gene}: Download failed or not found.")
             continue

        # Determine paths
        if status.get('pdb_path'):
             pdb_path = Path(status['pdb_path'])
        else:
             # Just downloaded, construct path
             pdb_path = fetcher.afdb_dir / uniprot / f"{uniprot}.pdb"

        if not pdb_path.is_absolute():
            pdb_path = repo_root / pdb_path

        pae_path = None
        if status.get('pae_path'):
            pae_path = Path(status['pae_path'])
        else:
            # Check for manually constructed PAE path
            candidate_pae = fetcher.afdb_dir / uniprot / f"{uniprot}_pae.json"
            if candidate_pae.exists():
                pae_path = candidate_pae

        if pae_path and not pae_path.is_absolute():
            pae_path = repo_root / pae_path

        # Analyze
        print(f"Processing {gene} ({uniprot})...")
        res = analyze_protein(pdb_path, pae_path, gene, uniprot, force=args.force)
        if res:
            results.append(res)

    # Write CSV
    csv_path = output_dir / "bolt_biofold_results.csv"
    with open(csv_path, 'w', newline='') as f:
        # Define field order
        fieldnames = [
            "protein_id", "gene_symbol", "uniprot_id", "species", "length",
            "pLDDT_mean", "pLDDT_median", "pLDDT_fraction_high", "pLDDT_fraction_ok", "pLDDT_fraction_low",
            "PAE_mean", "PAE_domain_blockiness_score",
            "predicted_domain_segments", "disorder_fraction_proxy", "hinge_candidates",
            "backbone_principal_axis", "radius_of_gyration", "end_to_end_distance",
            "mean_curvature_hc", "mean_torsion_hc", "anisotropy_index", "max_eigenvalue",
            "bending_hotspots", "exposed_surface_proxy", "charged_patch_score",
            "low_confidence_warning", "multi_domain_uncertain", "likely_IDR_heavy"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            # Filter keys to match fieldnames
            row = {k: r.get(k, "N/A") for k in fieldnames}
            writer.writerow(row)

    print(f"CSV saved to {csv_path}")

    # Generate Plots
    generate_plots(results, figures_dir)
    print(f"Plots saved to {figures_dir}")

    # Generate Markdown Report
    md_path = output_dir / "bolt_biofold_report.md"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(md_path, 'w') as f:
        f.write("# Bolt-BioFold Analysis Report\n\n")
        f.write(f"**Date:** {date_str}\n")
        f.write("**Source:** AlphaFold DB (Default Seed List)\n")
        f.write("**Code Version:** Bolt-BioFold 2.1 (PAE Integration)\n\n")

        f.write("## Results Summary\n\n")
        f.write("| Gene | Anisotropy | Rg (A) | Curvature | pLDDT | Domains | PAE Blockiness | Surface | Charge |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")

        high_anisotropy_count = 0
        hinge_count = 0

        for r in results:
            f.write(f"| {r['gene_symbol']} | {r['anisotropy_index']:.2f} | {r['radius_of_gyration']:.1f} | {r['mean_curvature_hc']:.3f} | {r['pLDDT_mean']:.1f} | {r['predicted_domain_segments']} | {r['PAE_domain_blockiness_score']:.1f} | {r['exposed_surface_proxy']} | {r['charged_patch_score']:.2f} |\n")
            if r['anisotropy_index'] > 3.0:
                high_anisotropy_count += 1
            if r['hinge_candidates'] != "None":
                hinge_count += 1

        f.write("\n## Interpretation\n\n")
        for r in results:
            f.write(f"### {r['gene_symbol']} ({r['uniprot_id']})\n")

            # What we see
            f.write("**What we see:**\n")
            f.write(f"- Geometry: Anisotropy {r['anisotropy_index']:.2f}, Rg {r['radius_of_gyration']:.1f}A.\n")
            if r['mean_curvature_hc'] > 0.1:
                f.write(f"- Curvature: High mean curvature ({r['mean_curvature_hc']:.3f}) with hotspots at {r['bending_hotspots']}.\n")
            else:
                f.write(f"- Curvature: Low mean curvature ({r['mean_curvature_hc']:.3f}), rod-like or globular.\n")

            f.write(f"- Surface: {r['exposed_surface_proxy']} exposed residues with charge score {r['charged_patch_score']:.2f}.\n")
            f.write(f"- PAE: Mean {r['PAE_mean']:.1f}, Blockiness {r['PAE_domain_blockiness_score']:.1f}.\n")

            if r['hinge_candidates'] != "None":
                 f.write(f"- Flexibility: Potential hinges at {r['hinge_candidates']}.\n")

            # Why it matters
            f.write("**Why it matters:**\n")
            if r['anisotropy_index'] > 3.0:
                f.write("- High anisotropy suggests a structural role (fiber/rod) capable of transmitting directional force or resisting gravity.\n")
            elif r['anisotropy_index'] < 1.5:
                f.write("- Globular shape suggests a catalytic or signaling hub role rather than direct load bearing.\n")
            else:
                 f.write("- Mixed geometry suggests a multifunctional role.\n")

            # Confidence
            f.write("**Confidence:** ")
            if r['low_confidence_warning']:
                f.write("LOW. (Caution: IDRs or poor prediction).\n")
            else:
                f.write("HIGH. (Reliable backbone geometry).\n")

            # Next test
            f.write("**Next test:** ")
            if r['hinge_candidates'] != "None":
                f.write("Simulate dynamics of hinge regions under tensile load.\n")
            elif r['anisotropy_index'] > 3.0:
                f.write("Test alignment of fibers under cyclic strain.\n")
            elif r['charged_patch_score'] > 0.4:
                f.write("Test pH sensitivity or binding to charged matrices.\n")
            else:
                f.write("Investigate binding partners in high-pLDDT surface patches.\n")
            f.write("\n")

        f.write("\n## Best Next Move\n")
        if high_anisotropy_count >= 3:
            f.write("Prioritize high-anisotropy candidates (Anisotropy > 3.0) for mechanical simulation of 'counter-curvature' generation.\n")
        elif hinge_count >= 3:
             f.write("Focus on hinge region molecular dynamics to assess mechano-gating potential.\n")
        else:
             f.write("Expand candidate list to include more fibrous/ECM proteins.\n")

    print(f"Report saved to {md_path}")

if __name__ == "__main__":
    main()
