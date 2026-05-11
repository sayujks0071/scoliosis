import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent

# Paths to scripts
SCRIPTS_DIR = REPO_ROOT / "research" / "alphafold_countercurvature" / "scripts"
SCRIPT_00 = SCRIPTS_DIR / "00_build_candidate_list.py"
SCRIPT_04 = SCRIPTS_DIR / "04_analyze_metrics.py"

@pytest.fixture
def pipeline_env(tmp_path):
    """Sets up a temporary environment for the pipeline."""
    base_dir = tmp_path / "afcc_test_env"
    base_dir.mkdir()

    # Create config structure
    config_dir = base_dir / "config"
    config_dir.mkdir()

    # Create targets.yaml
    targets_data = {
        "organism": "Homo sapiens",
        "max_targets": 1,
        "include_controls": False,
        "seeds": {
            "Test_Seed": ["TEST_GENE"]
        },
        "controls": []
    }
    with open(config_dir / "targets.yaml", "w") as f:
        yaml.dump(targets_data, f)

    # Create scoring_disectrioe.yaml
    scoring_data = {
        "weights": {"D": 1.0},
        "thresholds": {"min_score_to_fetch": 0.0}
    }
    with open(config_dir / "scoring_disectrioe.yaml", "w") as f:
        yaml.dump(scoring_data, f)

    # Create curation_overrides.yaml
    with open(config_dir / "curation_overrides.yaml", "w") as f:
        yaml.dump({"overrides": {}}, f)

    return base_dir

def run_script(script_path, base_dir):
    """Helper to run a script in the test environment."""
    run_env = os.environ.copy()
    run_env["AFCC_BASE_DIR"] = str(base_dir)
    # Ensure src is importable if script relies on sys.path hack that might fail in some envs,
    # but scripts explicitly add repo_root to sys.path so it should be fine.

    cmd = [sys.executable, str(script_path)]
    result = subprocess.run(
        cmd,
        env=run_env,
        capture_output=True,
        text=True
    )
    return result

def test_minimal_pipeline(pipeline_env):
    """Runs the minimal pipeline (00 -> Mock 01/02 -> 04)."""

    # --- Step 0: Build Candidate List ---
    print("\nRunning Step 0...")
    res0 = run_script(SCRIPT_00, pipeline_env)
    if res0.returncode != 0:
        print(f"STDOUT: {res0.stdout}")
        print(f"STDERR: {res0.stderr}")
    assert res0.returncode == 0, "Step 0 failed"

    candidates_path = pipeline_env / "data" / "processed" / "candidates.csv"
    assert candidates_path.exists(), "candidates.csv not created"

    candidates_df = pd.read_csv(candidates_path)
    assert "TEST_GENE" in candidates_df["gene_symbol"].values

    # --- Step 1: Map to UniProt (Mocked) ---
    print("\nMocking Step 1...")
    # Manually create mapping file
    mapping_path = pipeline_env / "data" / "processed" / "uniprot_mapping.csv"
    mapping_df = pd.DataFrame({
        "gene_symbol": ["TEST_GENE"],
        "uniprot_accession": ["P12345"],
        "organism_id": ["9606"],
        "status": ["mapped"]
    })
    mapping_df.to_csv(mapping_path, index=False)

    # --- Step 2: Fetch AFDB (Mocked) ---
    print("\nMocking Step 2...")
    # Create raw/afdb dir
    afdb_dir = pipeline_env / "data" / "raw" / "afdb" / "P12345"
    afdb_dir.mkdir(parents=True)

    # Create dummy PDB (Minimal valid PDB with a few atoms to allow parsing)
    pdb_path = afdb_dir / "P12345.pdb"
    with open(pdb_path, "w") as f:
        f.write("ATOM      1  N   ALA A   1      -0.525   1.362   0.000  1.00  0.00           N\n")
        f.write("ATOM      2  CA  ALA A   1       0.000   0.000   0.000  1.00  0.00           C\n")
        f.write("ATOM      3  C   ALA A   1       1.525   0.000   0.000  1.00  0.00           C\n")
        f.write("ATOM      4  O   ALA A   1       2.153   1.088   0.000  1.00  0.00           O\n")
        f.write("ATOM      5  CB  ALA A   1      -0.511  -0.778  -1.217  1.00  0.00           C\n")
        f.write("ATOM      6  N   ALA A   2       2.146  -1.168   0.000  1.00  0.00           N\n")
        f.write("ATOM      7  CA  ALA A   2       3.671  -1.168   0.000  1.00  0.00           C\n")
        f.write("ATOM      8  C   ALA A   2       4.196  -2.589   0.000  1.00  0.00           C\n")
        f.write("ATOM      9  O   ALA A   2       3.568  -3.614   0.000  1.00  0.00           O\n")
        f.write("TER      10      ALA A   2\n")
        f.write("END\n")

    # Update Manifest (using absolute path for pdb_path)
    manifest_path = pipeline_env / "data" / "manifest.csv"
    manifest_df = pd.DataFrame([{
        "uniprot": "P12345",
        "gene_symbol": "TEST_GENE",
        "status": "downloaded",
        "pdb_path": str(pdb_path.resolve()),
        "pae_path": None,
        "sha256_pdb": "dummy_sha",
        "retrieved_at": "2023-01-01"
    }])
    manifest_df.to_csv(manifest_path, index=False)

    # --- Step 4: Analyze Metrics ---
    print("\nRunning Step 4...")
    res4 = run_script(SCRIPT_04, pipeline_env)
    if res4.returncode != 0:
        print(f"STDOUT: {res4.stdout}")
        print(f"STDERR: {res4.stderr}")
    assert res4.returncode == 0, "Step 4 failed"

    metrics_path = pipeline_env / "data" / "processed" / "protein_metrics.csv"
    assert metrics_path.exists(), "protein_metrics.csv not created"

    metrics_df = pd.read_csv(metrics_path)
    print(f"Metrics columns: {metrics_df.columns.tolist()}")

    assert not metrics_df.empty
    assert "TEST_GENE" in metrics_df["gene_symbol"].values
