from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yaml


def load_config(config_path: Path) -> Dict[str, Any]:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_base_score_record() -> Dict[str, Any]:
    """Returns a default score record initialized to 0."""
    return {
        'D': 0, 'I': 0, 'S': 0, 'E': 0, 'C': 0,
        'T': 0, 'R': 0, 'I_iso': 0, 'O': 0, 'E_exp': 0,
        'manual_review_needed': True,
        'notes': ''
    }

def calculate_total_score(scores: Dict[str, Any], weights: Dict[str, float]) -> float:
    """Calculates weighted sum of scores."""
    total = 0.0
    for key, weight in weights.items():
        if key in scores:
            try:
                val = float(scores[key])
                total += val * weight
            except (ValueError, TypeError):
                continue
    return total

def build_candidate_list(
    targets_config_path: Path,
    scoring_config_path: Path,
    overrides_path: Path
) -> pd.DataFrame:
    """
    Builds the master candidate list from seeds, controls, and overrides.
    """
    targets = load_config(targets_config_path)
    weights = load_config(scoring_config_path).get('weights', {})
    overrides = load_config(overrides_path).get('overrides', {}) or {}

    candidates = {}

    # 1. Process Seeds (HOX, PAX)
    # Default D=2 for these
    seed_groups = targets.get('seeds', {})
    for group_name, genes in seed_groups.items():
        if group_name == 'expansion_modules': continue # handle separately

        for gene in genes:
            if gene not in candidates:
                rec = get_base_score_record()
                rec['gene_symbol'] = gene
                rec['source'] = f"seed_{group_name}"
                rec['D'] = 2 # Developmental relevance high by definition
                candidates[gene] = rec

    # 2. Process Expansion Modules
    expansion_modules = seed_groups.get('expansion_modules', {})
    include_flags = targets.get('include_expansion', {})

    for module_name, genes in expansion_modules.items():
        if include_flags.get(module_name, False):
            for gene in genes:
                if gene not in candidates:
                    rec = get_base_score_record()
                    rec['gene_symbol'] = gene
                    rec['source'] = f"expansion_{module_name}"
                    # D score might be lower or manual for expansions, but let's set 1 as baseline
                    rec['D'] = 1
                    candidates[gene] = rec

    # 3. Process Controls
    if targets.get('include_controls', True):
        controls = targets.get('controls', [])
        # Cap controls if needed, though usually small list
        for gene in controls:
            if gene not in candidates:
                rec = get_base_score_record()
                rec['gene_symbol'] = gene
                rec['source'] = "control"
                rec['D'] = 0
                rec['manual_review_needed'] = False # It's a control
                candidates[gene] = rec

    # 4. Apply Overrides
    for gene, scores in overrides.items():
        if gene not in candidates:
            # If a gene appears in overrides but not seeds, add it?
            # Let's assume yes, it's a manual addition.
            rec = get_base_score_record()
            rec['gene_symbol'] = gene
            rec['source'] = "manual_override"
            candidates[gene] = rec

        # Update scores
        for k, v in scores.items():
            if k in candidates[gene]:
                candidates[gene][k] = v

        if 'notes' in scores:
             candidates[gene]['notes'] = scores['notes']

        # If manually touched, maybe review is done?
        if len(scores) > 0:
            candidates[gene]['manual_review_needed'] = False

    # 5. Finalize DataFrame
    df_data = []
    for gene, rec in candidates.items():
        rec['total_score'] = calculate_total_score(rec, weights)
        df_data.append(rec)

    df = pd.DataFrame(df_data)

    # Sort by total score desc
    if not df.empty:
        df = df.sort_values(by=['total_score', 'gene_symbol'], ascending=[False, True])

    return df
