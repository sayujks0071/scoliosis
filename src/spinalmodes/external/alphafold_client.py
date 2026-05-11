from pathlib import Path

import pandas as pd
import requests


def fetch_alphafold_metadata(uniprot_id: str):
    """Fetch metadata from AlphaFold Database API."""
    url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
    except Exception:
        pass
    return None

def analyze_structural_information():
    """Analyze key developmental proteins via AlphaFold metadata."""
    # Using specific validated proteins for the spinal axis
    proteins = {
        "HOXC8": "P31273",   # Thoracic identity, highly conserved
        "HOXB13": "Q92826",  # Sacral identity
        "ADGRG6": "Q86SQ4"   # Linked to AIS morphology
    }

    results = []
    print("Connecting to AlphaFold API...")
    for name, uid in proteins.items():
        print(f"  Fetching {name} ({uid})...")
        meta = fetch_alphafold_metadata(uid)
        if meta:
            # AlphaFold structures have "globalMetricValue" which is avg pLDDT
            results.append({
                "protein": name,
                "uniprot_id": uid,
                "plddt_avg": meta.get("globalMetricValue", 0),
                "model_url": meta.get("pdbUrl", ""),
                "cif_url": meta.get("cifUrl", ""),
                "length": meta.get("uniprotEnd", 0) - meta.get("uniprotStart", 0) + 1,
                "confidence_high_frac": meta.get("fractionPlddtConfident", 0) + meta.get("fractionPlddtVeryHigh", 0)
            })

    df = pd.DataFrame(results)
    output_path = Path("src/spinalmodes/external/protein_structural_data.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved AlphaFold structural data to {output_path}")

    # Generate a small summary for the manuscript
    summary_path = Path("src/spinalmodes/external/alphafold_summary.txt")
    with open(summary_path, "w") as f:
        f.write("AlphaFold Structural Support for Information Field\n")
        f.write("==============================================\n\n")
        for _, row in df.iterrows():
            f.write(f"Protein: {row['protein']} ({row['uniprot_id']})\n")
            f.write(f"  - Avg pLDDT: {row['plddt_avg']:.2f}\n")
            f.write(f"  - Stable Regions: {row['confidence_high_frac']*100:.1f}%\n")
            f.write("  - Interpretation: High confidence domains provide binding specificity which anchors the IEC information field.\n\n")

    return df

if __name__ == "__main__":
    analyze_structural_information()
