import csv
import os
import sys

# Ensure data directory exists
MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "DNAAF1",
        "uniprot_id": "Q96ME1",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Motility,Assembly",
        "gravity_link": "Dynein assembly factor; essential for motile cilia function (flow sensing).",
        "spine_curvature_link": "Mutations cause PCD with situs inversus and potential scoliosis. (Frontiers 2020)",
        "priority_score": 85,
        "justification": "Dynein assembly factor linked to ciliary motility and laterality."
    },
    {
        "gene_symbol": "NPHP4",
        "uniprot_id": "O75161",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Transition_Zone",
        "gravity_link": "Nephrocystin; regulates ciliary transition zone and signaling.",
        "spine_curvature_link": "Mutations cause Nephronophthisis with skeletal defects (Senior-Loken). (Genetics 2022)",
        "priority_score": 85,
        "justification": "Ciliopathy gene linking transition zone defects to skeletal form."
    },
    {
        "gene_symbol": "BBS5",
        "uniprot_id": "Q8N3I7",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Trafficking,Syndromic",
        "gravity_link": "Component of the BBSome; essential for ciliary protein trafficking (mechanosensors).",
        "spine_curvature_link": "Bardet-Biedl Syndrome features scoliosis. (Genetics 2022)",
        "priority_score": 85,
        "justification": "BBSome component essential for ciliary signaling."
    },
    {
        "gene_symbol": "TBXT",
        "uniprot_id": "O15178",
        "organism": "Homo sapiens",
        "pathway_tags": "Notochord,Segmentation,Development",
        "gravity_link": "Essential for notochord formation (the primary hydrostatic skeleton).",
        "spine_curvature_link": "Mutations cause vertebral malformations and 'tailless' phenotype. (DOI: 10.1038/ng1196-302)",
        "priority_score": 90,
        "justification": "Master regulator of notochord formation and axial elongation."
    },
    {
        "gene_symbol": "MSGN1",
        "uniprot_id": "A6NI15",
        "organism": "Homo sapiens",
        "pathway_tags": "Segmentation,Somite,Development",
        "gravity_link": "Master regulator of paraxial mesoderm differentiation (somites).",
        "spine_curvature_link": "Essential for somite formation and vertebral segmentation. (DOI: 10.1038/nature02677)",
        "priority_score": 85,
        "justification": "Master regulator of paraxial mesoderm essential for somites."
    },
    {
        "gene_symbol": "TCTN3",
        "uniprot_id": "Q6NUS6",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Transition_Zone,Signaling",
        "gravity_link": "Tectonic family member; regulates ciliary membrane composition.",
        "spine_curvature_link": "Mutations cause Orofaciodigital syndrome IV with severe skeletal defects. (DOI: 10.1016/j.ajhg.2012.08.014)",
        "priority_score": 85,
        "justification": "Ciliary transition zone protein linked to severe skeletal dysplasia."
    },
    {
        "gene_symbol": "NPR3",
        "uniprot_id": "P17342",
        "organism": "Homo sapiens",
        "pathway_tags": "Growth_Plate,Signaling,Bone",
        "gravity_link": "Clearance receptor for natriuretic peptides; regulates bone growth under load.",
        "spine_curvature_link": "Mutations cause tall stature with skeletal overgrowth and scoliosis. (DOI: 10.1016/j.ajhg.2013.10.023)",
        "priority_score": 85,
        "justification": "Regulator of bone growth rate and skeletal proportions."
    },
    {
        "gene_symbol": "AMOTL2",
        "uniprot_id": "Q9Y2J4",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Junctions,Hippo",
        "gravity_link": "Angiomotin-like 2; inhibitor of YAP/TAZ and regulator of cell junctions under tension.",
        "spine_curvature_link": "Essential for notochord and vertebral morphogenesis. (DOI: 10.1016/j.devcel.2011.02.007)",
        "priority_score": 85,
        "justification": "YAP/TAZ inhibitor and junctional mechanotransducer."
    },
    {
        "gene_symbol": "SMURF1",
        "uniprot_id": "Q9HCE7",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Bone,Ubiquitination",
        "gravity_link": "E3 ubiquitin ligase regulating BMP signaling and PCP pathway.",
        "spine_curvature_link": "Essential for osteoblast activity and potentially vertebral patterning. (DOI: 10.1016/j.cell.2005.05.003)",
        "priority_score": 82,
        "justification": "Regulator of BMP signaling and PCP."
    },
    {
        "gene_symbol": "FZD6",
        "uniprot_id": "O60353",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Signaling,Wnt",
        "gravity_link": "Frizzled-6; non-canonical Wnt receptor essential for PCP.",
        "spine_curvature_link": "Regulates hair follicle and tissue polarity; linked to neural tube defects. (DOI: 10.1038/ng1378)",
        "priority_score": 80,
        "justification": "Core PCP receptor."
    },
    {
        "gene_symbol": "ANKRD6",
        "uniprot_id": "Q9Y2G4",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Signaling,Wnt",
        "gravity_link": "Diversin; regulates Wnt signaling and PCP.",
        "spine_curvature_link": "Essential for gastrulation and axis elongation. (DOI: 10.1038/ncb747)",
        "priority_score": 80,
        "justification": "Regulator of Wnt/PCP pathway."
    },
    {
        "gene_symbol": "PRICKLE3",
        "uniprot_id": "O43900",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Signaling",
        "gravity_link": "Prickle homolog; PCP component aligning tissues.",
        "spine_curvature_link": "Implicated in neural tube defects and polarity. (DOI: 10.1016/j.ajhg.2011.06.008)",
        "priority_score": 80,
        "justification": "PCP pathway member."
    },
    {
        "gene_symbol": "WNT11",
        "uniprot_id": "O96014",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Signaling,Wnt",
        "gravity_link": "Non-canonical Wnt ligand driving PCP and convergent extension.",
        "spine_curvature_link": "Essential for vertebral axis elongation and shape. (DOI: 10.1016/j.devcel.2006.12.008)",
        "priority_score": 85,
        "justification": "Key ligand for PCP signaling and axis elongation."
    },
    {
        "gene_symbol": "LRP4",
        "uniprot_id": "O75096",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Bone,Neuromuscular",
        "gravity_link": "Receptor for Wnt and Agrin; essential for NMJ formation (muscle tone).",
        "spine_curvature_link": "Mutations cause Cenani-Lenz syndrome and sclerosteosis with spinal defects. (DOI: 10.1016/j.ajhg.2010.02.012)",
        "priority_score": 88,
        "justification": "Critical for both bone density (Wnt) and muscle innervation (Agrin)."
    },
    {
        "gene_symbol": "MUSK",
        "uniprot_id": "O15146",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Neuromuscular,Signaling",
        "gravity_link": "Receptor tyrosine kinase essential for NMJ formation (proprioception/tone).",
        "spine_curvature_link": "Mutations cause Congenital Myasthenic Syndrome with scoliosis. (DOI: 10.1016/j.ajhg.2004.05.002)",
        "priority_score": 88,
        "justification": "Essential for neuromuscular junction maintenance and muscle tone."
    }
]

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"Error: {MASTER_FILE} not found.")
        sys.exit(1)

    existing_symbols = set()
    file_fieldnames = []

    # Read existing
    try:
        with open(MASTER_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            file_fieldnames = reader.fieldnames

            if not file_fieldnames or 'gene_symbol' not in file_fieldnames:
                print("Error: CSV missing header or 'gene_symbol' column.")
                sys.exit(1)

            for row in reader:
                if row['gene_symbol']:
                    existing_symbols.add(row['gene_symbol'].strip().upper())
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    # Append new candidates
    added_count = 0
    skipped_count = 0

    try:
        with open(MASTER_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=file_fieldnames)

            for cand in new_candidates:
                symbol = cand['gene_symbol'].strip().upper()
                if symbol in existing_symbols:
                    print(f"Skipping {cand['gene_symbol']} (already exists)")
                    skipped_count += 1
                    continue

                # Ensure we only write fields that exist in the CSV
                row_to_write = {k: v for k, v in cand.items() if k in file_fieldnames}

                writer.writerow(row_to_write)
                print(f"Added {cand['gene_symbol']}")
                added_count += 1

    except Exception as e:
        print(f"Error writing to CSV: {e}")
        sys.exit(1)

    print(f"\nSummary: Added {added_count} candidates. Skipped {skipped_count} duplicates.")

if __name__ == "__main__":
    main()
