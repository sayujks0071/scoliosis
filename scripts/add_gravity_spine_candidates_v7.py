import csv
import os

MASTER_FILE = "data/candidates_master.csv"

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"Error: {MASTER_FILE} not found.")
        return

    new_candidates = [
        {
            "gene_symbol": "EPHA4",
            "uniprot_id": "P54764",
            "organism": "Homo sapiens",
            "pathway_tags": "Axon_Guidance,Locomotion,Mechanotransduction",
            "gravity_link": "Ephrin receptor regulating axon guidance and CPG coordination; essential for patterned locomotion against gravity.",
            "spine_curvature_link": "Dysfunction causes CPG defects and idiopathic scoliosis in models. (eLife 2024; DOI: 10.7554/eLife.95324)",
            "priority_score": "92",
            "justification": "Direct link between CPG/locomotor circuit defects and idiopathic scoliosis."
        },
        {
            "gene_symbol": "TENT5A",
            "uniprot_id": "Q8N5L8",
            "organism": "Homo sapiens",
            "pathway_tags": "Muscle,Development,Polyadenylation",
            "gravity_link": "Poly(A) polymerase regulating myogenin stability and muscle fiber formation; essential for postural muscle tone.",
            "spine_curvature_link": "Modulates muscle fiber formation; deficiency leads to AIS-like paraspinal asymmetry. (PMC8891553)",
            "priority_score": "88",
            "justification": "Novel regulator of paraspinal muscle symmetry linked to AIS."
        },
        {
            "gene_symbol": "ABO",
            "uniprot_id": "P16442",
            "organism": "Homo sapiens",
            "pathway_tags": "Mechanotransduction,Cilia,Glycosylation",
            "gravity_link": "Glycosyltransferase modifying surface proteins; affects cilia length and mechanosensitivity in osteoblasts.",
            "spine_curvature_link": "Altered mechanotransduction and cilia length in AIS osteoblasts linked to ABO variants. (PMC8813918)",
            "priority_score": "85",
            "justification": "Direct link to altered cellular mechanotransduction in AIS."
        },
        {
            "gene_symbol": "CDH13",
            "uniprot_id": "P55290",
            "organism": "Homo sapiens",
            "pathway_tags": "Adhesion,Signaling,Calcium",
            "gravity_link": "Cadherin-13 (T-cadherin); GPI-anchored adhesion molecule mediating calcium-dependent signaling.",
            "spine_curvature_link": "Top GWAS hit for Adolescent Idiopathic Scoliosis; regulates adiponectin levels and bone mass. (Harmonizome 2025)",
            "priority_score": "88",
            "justification": "Consistently identified top GWAS candidate with adhesion function."
        },
        {
            "gene_symbol": "KIF24",
            "uniprot_id": "Q5T7B8",
            "organism": "Homo sapiens",
            "pathway_tags": "Cilia,Cytoskeleton,Motor_Protein",
            "gravity_link": "Kinesin-13 family member that depolymerizes centriolar microtubules; regulates ciliogenesis.",
            "spine_curvature_link": "GWAS hit for AIS; essential for ciliary remodeling (gravity sensors). (Harmonizome 2025)",
            "priority_score": "85",
            "justification": "Ciliary remodeling protein linked to AIS via GWAS."
        },
        {
            "gene_symbol": "AJAP1",
            "uniprot_id": "Q9UKB5",
            "organism": "Homo sapiens",
            "pathway_tags": "Adhesion,Cytoskeleton,Signaling",
            "gravity_link": "Adherens junction-associated protein; connects E-cadherin to the actin cytoskeleton (force transmission).",
            "spine_curvature_link": "GWAS hit for AIS; essential for epithelial integrity and force transmission. (Harmonizome 2025)",
            "priority_score": "82",
            "justification": "Linker between adhesion and cytoskeleton identified in GWAS."
        },
        {
            "gene_symbol": "BOC",
            "uniprot_id": "Q9BWV1",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Hedgehog,Muscle",
            "gravity_link": "Brother of CDO; Hedgehog co-receptor promoting myogenic differentiation and neurite outgrowth.",
            "spine_curvature_link": "GWAS hit for AIS; essential for muscle development and Hedgehog signaling. (Harmonizome 2025)",
            "priority_score": "85",
            "justification": "Hedgehog pathway component regulating muscle/neural development."
        },
        {
            "gene_symbol": "MEIS1",
            "uniprot_id": "O00470",
            "organism": "Homo sapiens",
            "pathway_tags": "Transcription_Factor,Development,Segmentation",
            "gravity_link": "Homeobox transcription factor; regulates paraxial mesoderm patterning and myogenesis.",
            "spine_curvature_link": "GWAS hit for AIS; essential for vertebral column patterning. (Harmonizome 2025)",
            "priority_score": "85",
            "justification": "Developmental regulator of paraxial mesoderm linked to AIS."
        },
        {
            "gene_symbol": "TNIK",
            "uniprot_id": "Q9UKE5",
            "organism": "Homo sapiens",
            "pathway_tags": "Cytoskeleton,Signaling,Wnt",
            "gravity_link": "TRAF2 and NCK interacting kinase; regulates actin cytoskeleton and Wnt signaling (mechanosensitive).",
            "spine_curvature_link": "GWAS hit for AIS; regulates neuronal dendrite extension and cytoskeletal rearrangement. (Harmonizome 2025)",
            "priority_score": "82",
            "justification": "Cytoskeletal regulator and Wnt effector linked to AIS."
        },
        {
            "gene_symbol": "CNKSR3",
            "uniprot_id": "Q6P9H4",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Scaffold,MAPK",
            "gravity_link": "Connector enhancer of KSR 3; scaffold protein for MAPK/ERK and sodium transport (ENaC).",
            "spine_curvature_link": "GWAS hit for AIS; regulates epithelial sodium transport and signaling. (Harmonizome 2025)",
            "priority_score": "82",
            "justification": "Scaffold protein identified in AIS GWAS; potential ion transport link."
        }
    ]

    existing_genes = set()
    with open(MASTER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_genes.add(row['gene_symbol'])

    count = 0
    with open(MASTER_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["gene_symbol", "uniprot_id", "organism", "pathway_tags", "gravity_link", "spine_curvature_link", "priority_score", "justification"])
        # No header write, appending
        for c in new_candidates:
            if c['gene_symbol'] not in existing_genes:
                writer.writerow(c)
                count += 1
                print(f"Added {c['gene_symbol']}")
            else:
                print(f"Skipped {c['gene_symbol']} (already exists)")

    print(f"Added {count} new candidates.")

if __name__ == "__main__":
    main()
