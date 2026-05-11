import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "KDM4C",
        "uniprot_id": "Q9H3R0",
        "organism": "Homo sapiens",
        "pathway_tags": "Epigenetics,Mechanotransduction,Nucleus",
        "gravity_link": "Mechanosensitive demethylase; reduced H3K9me3 levels observed in soft nuclear environments (microgravity).",
        "spine_curvature_link": "Loss of H3K9me3 heterochromatin leads to 'Epigenetic Drift' and genomic instability, a driver of scoliotic progression. (Nava et al., 2020)",
        "priority_score": 88,
        "justification": "Key epigenetic stiffness sensor linking nuclear mechanics to gene expression stability."
    },
    {
        "gene_symbol": "SUV39H1",
        "uniprot_id": "O43463",
        "organism": "Homo sapiens",
        "pathway_tags": "Epigenetics,Mechanotransduction,Nucleus",
        "gravity_link": "Major H3K9me3 methyltransferase; activity is required to maintain nuclear stiffness against gravity.",
        "spine_curvature_link": "Downregulation linked to cellular senescence and loss of tissue integrity in spinal curvature. (Nava et al., 2020 context)",
        "priority_score": 85,
        "justification": "Writer of the heterochromatin 'stiffness code' protecting the genome."
    },
    {
        "gene_symbol": "NFE2L2",
        "uniprot_id": "Q16236",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,ROS,Muscle",
        "gravity_link": "Master regulator of antioxidant response; activated by unloading-induced oxidative stress (ROS).",
        "spine_curvature_link": "ROS-METTL3 axis drives paraspinal muscle asymmetry and atrophy in AIS. (Shao et al., 2025)",
        "priority_score": 85,
        "justification": "Critical defender against microgravity-induced oxidative damage in paraspinal muscles."
    },
    {
        "gene_symbol": "CCN2",
        "uniprot_id": "P29279",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Mechanotransduction,Fibrosis",
        "gravity_link": "Direct target of YAP/TAZ; expression scales with mechanical load and stiffness.",
        "spine_curvature_link": "Upregulated in ligamentum flavum of scoliosis patients; drives asymmetric fibrosis. (DOI: 10.1096/fj.201802652R)",
        "priority_score": 85,
        "justification": "Major effector of fibrosis and stiffness in response to mechanical load."
    },
    {
        "gene_symbol": "PKHD1",
        "uniprot_id": "P08F94",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Mechanotransduction",
        "gravity_link": "Fibrocystin; essential for ciliary sensing of fluid flow (gravity proxy).",
        "spine_curvature_link": "Mutations cause ARPKD and Congenital Hepatic Fibrosis, often associated with scoliosis. (DOI: 10.1007/s00439-014-1430-x)",
        "priority_score": 82,
        "justification": "Ciliary mechanosensor linked to syndromic spinal defects."
    },
    {
        "gene_symbol": "WDR35",
        "uniprot_id": "Q9P2L0",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Transport",
        "gravity_link": "IFT component essential for ciliary structure and flow sensing.",
        "spine_curvature_link": "Mutations cause Sensenbrenner syndrome (Cranioectodermal dysplasia) with narrow thorax and spinal anomalies. (DOI: 10.1016/j.ajhg.2010.04.017)",
        "priority_score": 82,
        "justification": "IFT protein linking ciliary structure to skeletal form."
    },
    {
        "gene_symbol": "UNCX",
        "uniprot_id": "Q96D98",
        "organism": "Homo sapiens",
        "pathway_tags": "Segmentation,Somite",
        "gravity_link": "Defines posterior half of somites; essential for establishing vertebral boundaries.",
        "spine_curvature_link": "Mutations lead to vertebral fusion and segmentation defects (spondylocostal dysostosis-like). (DOI: 10.1038/nature06686)",
        "priority_score": 80,
        "justification": "Transcription factor defining the structural unit of the spine."
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
