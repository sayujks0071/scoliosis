import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "FKBP14",
        "uniprot_id": "Q9NWM8",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Chaperone,ER",
        "gravity_link": "ER chaperone for collagen folding; essential for maintaining tissue tensile strength against gravity.",
        "spine_curvature_link": "Mutations cause Ehlers-Danlos Syndrome, Kyphoscoliotic Type 2. (DOI: 10.1016/j.ajhg.2012.01.003)",
        "priority_score": 88,
        "justification": "Essential collagen chaperone; defining gene for Kyphoscoliotic EDS."
    },
    {
        "gene_symbol": "SLC39A13",
        "uniprot_id": "Q96H72",
        "organism": "Homo sapiens",
        "pathway_tags": "Ion_Transport,ECM,Mechanotransduction",
        "gravity_link": "Zinc transporter required for lysyl hydroxylase function (PLOD1/3) and collagen crosslinking stiffness.",
        "spine_curvature_link": "Mutations cause Ehlers-Danlos Syndrome, Spondylodysplastic Type 3. (DOI: 10.1016/j.ajhg.2008.05.005)",
        "priority_score": 85,
        "justification": "Zinc transporter required for lysyl hydroxylase function and collagen crosslinking stiffness."
    },
    {
        "gene_symbol": "B3GALT6",
        "uniprot_id": "Q96L58",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Enzyme,Glycosylation",
        "gravity_link": "Linker region enzyme for proteoglycan GAG synthesis; essential for matrix spacing and compressive resistance.",
        "spine_curvature_link": "Mutations cause Ehlers-Danlos Syndrome, Spondylodysplastic Type 2. (DOI: 10.1016/j.ajhg.2013.04.020)",
        "priority_score": 85,
        "justification": "Linker region enzyme for proteoglycan GAG synthesis; essential for matrix spacing."
    },
    {
        "gene_symbol": "B4GALT7",
        "uniprot_id": "Q9UBV7",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Enzyme,Glycosylation",
        "gravity_link": "Linker region enzyme for proteoglycan GAG synthesis; essential for matrix spacing and compressive resistance.",
        "spine_curvature_link": "Mutations cause Ehlers-Danlos Syndrome, Spondylodysplastic Type 1. (DOI: 10.1016/j.ajhg.2008.12.002)",
        "priority_score": 85,
        "justification": "Linker region enzyme for proteoglycan GAG synthesis; essential for matrix spacing."
    },
    {
        "gene_symbol": "CHST14",
        "uniprot_id": "Q8NCG5",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Enzyme,Glycosylation",
        "gravity_link": "Dermatan sulfate sulfotransferase; essential for collagen fibril organization and tissue integrity.",
        "spine_curvature_link": "Mutations cause Ehlers-Danlos Syndrome, Musculocontractural Type 1. (DOI: 10.1016/j.ajhg.2009.11.011)",
        "priority_score": 88,
        "justification": "Dermatan sulfate sulfotransferase; essential for collagen fibril organization."
    },
    {
        "gene_symbol": "DSE",
        "uniprot_id": "Q9UL01",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Enzyme,Glycosylation",
        "gravity_link": "Dermatan sulfate epimerase; essential for collagen fibril organization and tissue integrity.",
        "spine_curvature_link": "Mutations cause Ehlers-Danlos Syndrome, Musculocontractural Type 2. (DOI: 10.1016/j.ajhg.2010.05.014)",
        "priority_score": 85,
        "justification": "Dermatan sulfate epimerase; essential for collagen fibril organization."
    },
    {
        "gene_symbol": "ZNF469",
        "uniprot_id": "Q96JG9",
        "organism": "Homo sapiens",
        "pathway_tags": "Transcription_Factor,ECM,Development",
        "gravity_link": "Regulates corneal and skeletal ECM genes; essential for tissue stiffness.",
        "spine_curvature_link": "Mutations cause Brittle Cornea Syndrome 1, characterized by severe kyphoscoliosis and joint hypermobility. (DOI: 10.1086/588173)",
        "priority_score": 88,
        "justification": "Regulates corneal and skeletal ECM genes; mutations cause severe kyphoscoliosis."
    },
    {
        "gene_symbol": "PRDM5",
        "uniprot_id": "Q9NQX1",
        "organism": "Homo sapiens",
        "pathway_tags": "Transcription_Factor,ECM,Development",
        "gravity_link": "Regulates corneal and skeletal ECM genes (COL11A1, COL4A1); essential for tissue stiffness.",
        "spine_curvature_link": "Mutations cause Brittle Cornea Syndrome 2, characterized by severe kyphoscoliosis. (DOI: 10.1016/j.ajhg.2011.05.005)",
        "priority_score": 85,
        "justification": "Regulates corneal and skeletal ECM genes; mutations cause severe kyphoscoliosis."
    },
    {
        "gene_symbol": "GORAB",
        "uniprot_id": "Q8N8F7",
        "organism": "Homo sapiens",
        "pathway_tags": "Golgi,Cilia,Signaling",
        "gravity_link": "Golgi protein essential for Hedgehog signaling and skeletal development; cilia are gravity sensors.",
        "spine_curvature_link": "Mutations cause Gerodermia osteodysplastica, featuring osteoporosis and fractures/scoliosis. (DOI: 10.1038/ng.297)",
        "priority_score": 85,
        "justification": "Golgi protein essential for Hedgehog signaling and skeletal development."
    },
    {
        "gene_symbol": "RIN2",
        "uniprot_id": "Q8WYP3",
        "organism": "Homo sapiens",
        "pathway_tags": "Trafficking,Signaling,ECM",
        "gravity_link": "Rab5 effector regulating BMP signaling and ECM trafficking; essential for connective tissue maintenance.",
        "spine_curvature_link": "Mutations cause MACS syndrome (Macrocephaly, Alopecia, Cutis laxa, Scoliosis). (DOI: 10.1016/j.ajhg.2007.09.022)",
        "priority_score": 82,
        "justification": "Rab5 effector regulating BMP signaling and ECM trafficking."
    },
    {
        "gene_symbol": "ATP6V0A2",
        "uniprot_id": "Q9Y487",
        "organism": "Homo sapiens",
        "pathway_tags": "Trafficking,ECM,Glycosylation",
        "gravity_link": "V-ATPase subunit regulating Golgi pH and glycosylation of ECM proteins; essential for matrix quality.",
        "spine_curvature_link": "Mutations cause Autosomal Recessive Cutis Laxa Type IIA, featuring scoliosis. (OMIM)",
        "priority_score": 82,
        "justification": "V-ATPase subunit regulating Golgi pH and glycosylation of ECM proteins."
    },
    {
        "gene_symbol": "PYCR1",
        "uniprot_id": "P32322",
        "organism": "Homo sapiens",
        "pathway_tags": "Metabolism,ECM,Proline",
        "gravity_link": "Key enzyme for proline synthesis, the primary amino acid of collagen (stiffness).",
        "spine_curvature_link": "Mutations cause Autosomal Recessive Cutis Laxa Type 2B with osteopenia and scoliosis. (DOI: 10.1038/ng.413)",
        "priority_score": 85,
        "justification": "Key enzyme for proline synthesis, the primary amino acid of collagen."
    },
    {
        "gene_symbol": "ALDH18A1",
        "uniprot_id": "P54886",
        "organism": "Homo sapiens",
        "pathway_tags": "Metabolism,ECM,Proline",
        "gravity_link": "Key enzyme for proline synthesis, the primary amino acid of collagen (stiffness).",
        "spine_curvature_link": "Mutations cause Autosomal Recessive Cutis Laxa Type 3A with scoliosis. (DOI: 10.1038/ng.413)",
        "priority_score": 85,
        "justification": "Key enzyme for proline synthesis, the primary amino acid of collagen."
    },
    {
        "gene_symbol": "TNNT3",
        "uniprot_id": "P45378",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Contractility",
        "gravity_link": "Fast skeletal muscle troponin; regulates muscle contraction tone against gravity.",
        "spine_curvature_link": "Mutations cause Distal Arthrogryposis Type 2B (Freeman-Sheldon variant) with contractures. (DOI: 10.1086/521136)",
        "priority_score": 85,
        "justification": "Fast skeletal muscle troponin; mutations cause distal arthrogryposis and contractures."
    },
    {
        "gene_symbol": "MYH8",
        "uniprot_id": "P13535",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Motor_Protein",
        "gravity_link": "Neonatal/masticatory myosin; mutations cause contractures limiting movement against gravity.",
        "spine_curvature_link": "Mutations cause Trismus-pseudocamptodactyly syndrome, featuring contractures. (DOI: 10.1038/ng1855)",
        "priority_score": 85,
        "justification": "Neonatal/masticatory myosin; mutations cause trismus-pseudocamptodactyly syndrome."
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
