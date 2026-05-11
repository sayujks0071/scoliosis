import time
from pathlib import Path

from alphafold_analysis.analyze_bcc_structures import analyze_structure

pdb_dir = Path("alphafold_analysis/predictions")
pdb_files = list(pdb_dir.glob("*.pdb"))[:20] # Take first 20 for speed

start_time = time.time()
for pdb_file in pdb_files:
    analyze_structure(pdb_file)
end_time = time.time()

print(f"Processed {len(pdb_files)} files in {end_time - start_time:.4f} seconds")
