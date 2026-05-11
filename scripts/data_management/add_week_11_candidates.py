import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "FERMT2",
        "uniprot_id": "Q96AC1",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Adhesion,Integrin",
        "gravity_link": "Kindlin-2; essential for integrin activation and force transmission at focal adhesions (gravity sensing).",
        "spine_curvature_link": "Chondrocyte-specific deletion causes severe kyphosis and dwarfism. (DOI: 10.1371/journal.pgen.1005345)",
        "priority_score": 90,
        "justification": "Direct skeletal defect + mechanotransduction core."
    },
    {
        "gene_symbol": "CREBBP",
        "uniprot_id": "Q92793",
        "organism": "Homo sapiens",
        "pathway_tags": "Epigenetics,Development,Signaling",
        "gravity_link": "HAT activity regulates expression of mechanosensitive genes during development.",
        "spine_curvature_link": "Rubinstein-Taybi Syndrome features scoliosis/kyphosis in >50% of patients. (GeneReviews)",
        "priority_score": 88,
        "justification": "Strong syndromic link to spinal curvature."
    },
    {
        "gene_symbol": "IFT140",
        "uniprot_id": "Q96RY7",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Transport",
        "gravity_link": "Essential for retrograde ciliary transport (IFT-A) and flow sensing.",
        "spine_curvature_link": "Mutations cause Mainzer-Saldino syndrome (skeletal dysplasia) with potential spine involvement. (DOI: 10.1016/j.ajhg.2012.04.014)",
        "priority_score": 85,
        "justification": "Ciliopathy link to skeletal dysplasia."
    },
    {
        "gene_symbol": "DKK1",
        "uniprot_id": "O94907",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Bone,Unloading",
        "gravity_link": "Major inhibitor of Wnt signaling upregulated in mechanical unloading (microgravity). (DOI: 10.1371/journal.pone.0033204)",
        "spine_curvature_link": "Regulates vertebral bone mass; antibodies prevent unloading-induced bone loss.",
        "priority_score": 88,
        "justification": "Key mediator of unloading-induced bone loss."
    },
    {
        "gene_symbol": "IGF1",
        "uniprot_id": "P05019",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Growth,Muscle",
        "gravity_link": "Systemic growth factor sensitive to loading status; decreases in spaceflight.",
        "spine_curvature_link": "Serum levels correlate with AIS curve progression during pubertal growth spurt. (DOI: 10.1097/BRS.0b013e31816f286d)",
        "priority_score": 85,
        "justification": "Growth factor connecting systemic loading to spine progression."
    },
    {
        "gene_symbol": "COL10A1",
        "uniprot_id": "Q03692",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Growth_Plate",
        "gravity_link": "Specific to hypertrophic chondrocytes in the load-bearing zone of the growth plate.",
        "spine_curvature_link": "Mutations cause Schmid Metaphyseal Chondrodysplasia; associated with spinal changes. (DOI: 10.1002/humu.1380010104)",
        "priority_score": 85,
        "justification": "Specific marker of the load-bearing growth plate zone."
    },
    {
        "gene_symbol": "TWIST2",
        "uniprot_id": "Q8WVJ9",
        "organism": "Homo sapiens",
        "pathway_tags": "Development,Transcription_Factor",
        "gravity_link": "Regulates dermis/bone differentiation; implicated in mechanosensory differentiation.",
        "spine_curvature_link": "Mutations cause Setleis Syndrome and Ablepharon-Macrostomia Syndrome with skeletal abnormalities. (DOI: 10.1038/ng1419)",
        "priority_score": 82,
        "justification": "Syndromic link via TWIST pathway."
    },
    {
        "gene_symbol": "PRICKLE2",
        "uniprot_id": "Q7Z3G6",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Signaling",
        "gravity_link": "Component of PCP pathway aligning tissue polarity against stress.",
        "spine_curvature_link": "PCP pathway defects are a fundamental cause of neural tube defects and scoliosis. (General PCP link)",
        "priority_score": 80,
        "justification": "PCP pathway member."
    },
    {
        "gene_symbol": "WNT10B",
        "uniprot_id": "O00744",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Bone",
        "gravity_link": "Promotes osteogenesis via Wnt; signaling is mechanically regulated.",
        "spine_curvature_link": "Mutations cause Split-Hand/Foot Malformation 6; Wnt is key for vertebral bone mass. (DOI: 10.1086/521524)",
        "priority_score": 80,
        "justification": "Regulator of bone mass under Wnt control."
    },
    {
        "gene_symbol": "AXIN2",
        "uniprot_id": "Q9Y2T1",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Wnt",
        "gravity_link": "Scaffold protein for Wnt destruction complex; negative feedback for mechanosensitive Wnt.",
        "spine_curvature_link": "Mutations cause tooth agenesis and colorectal cancer; Wnt regulation essential for spine. (DOI: 10.1086/382227)",
        "priority_score": 78,
        "justification": "Negative regulator of Wnt mechanosignaling."
    }
]

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"Error: {MASTER_FILE} not found.")
        return

    # Read existing
    existing_symbols = set()
    with open(MASTER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            existing_symbols.add(row['gene_symbol'])

    # Append new
    with open(MASTER_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        count = 0
        for cand in new_candidates:
            if cand['gene_symbol'] in existing_symbols:
                print(f"Skipping {cand['gene_symbol']} (already exists)")
                continue

            writer.writerow(cand)
            print(f"Added {cand['gene_symbol']}")
            count += 1

    print(f"Successfully added {count} new candidates.")

if __name__ == "__main__":
    main()
