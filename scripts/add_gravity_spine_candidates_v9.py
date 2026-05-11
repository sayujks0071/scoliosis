import csv
import os

MASTER_FILE = "data/candidates_master.csv"

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"Error: {MASTER_FILE} not found.")
        return

    new_candidates = [
        {
            "gene_symbol": "SMAD6",
            "uniprot_id": "O43541",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,BMP,Mechanotransduction",
            "gravity_link": "Inhibitory SMAD; negatively regulates BMP signaling, which is mechanically activated in bone.",
            "spine_curvature_link": "Mutations are implicated in craniosynostosis and cardiovascular defects; crucial for balancing osteogenesis in the spine. (PMID: 9435649)",
            "priority_score": "80",
            "justification": "Key negative regulator of mechanosensitive BMP pathway."
        },
        {
            "gene_symbol": "PKD2L1",
            "uniprot_id": "Q9P0L9",
            "organism": "Homo sapiens",
            "pathway_tags": "Cilia,Mechanotransduction,Ion_Channel",
            "gravity_link": "Forms mechanosensitive complex with PKD1L1 in primary cilia, sensing fluid flow and acting as a gravity/posture proxy.",
            "spine_curvature_link": "Essential for establishing left-right asymmetry and cerebrospinal fluid flow sensing; Pkd2l1 mutant zebrafish show curvature defects. (PMID: 30206132)",
            "priority_score": "85",
            "justification": "Partner of PKD1L1 in ciliary mechanosensing, directly linked to spine straightness."
        },
        {
            "gene_symbol": "PTPN14",
            "uniprot_id": "Q15678",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Mechanotransduction,Hippo",
            "gravity_link": "Regulates YAP1 activity independent of the core Hippo kinase cascade; responds to cell density and mechanics.",
            "spine_curvature_link": "Mutations cause choanal atresia and lymphedema, with potential skeletal/spinal involvement via YAP1 dysregulation. (PMID: 22446702)",
            "priority_score": "80",
            "justification": "Key YAP1 regulator acting as a mechanical sensor."
        },
        {
            "gene_symbol": "FZD7",
            "uniprot_id": "O75084",
            "organism": "Homo sapiens",
            "pathway_tags": "PCP,Signaling,Wnt",
            "gravity_link": "Receptor for Wnt11 in the Planar Cell Polarity (PCP) pathway, transmitting mechanical cues to align tissues.",
            "spine_curvature_link": "Crucial for convergent extension and neural tube closure; disruption causes severe axial defects. (PMID: 15315758)",
            "priority_score": "85",
            "justification": "Primary receptor for Wnt11 in the PCP pathway."
        },
        {
            "gene_symbol": "CELSR2",
            "uniprot_id": "Q9HCU4",
            "organism": "Homo sapiens",
            "pathway_tags": "PCP,Cilia,Adhesion",
            "gravity_link": "Atypical cadherin (PCP) regulating ciliary orientation and tissue polarity.",
            "spine_curvature_link": "PCP pathway defects are a fundamental cause of neural tube defects and scoliosis. (DOI: 10.1038/nature01614)",
            "priority_score": "85",
            "justification": "Core PCP component regulating ciliary polarity."
        },
        {
            "gene_symbol": "FAT3",
            "uniprot_id": "Q8BXT9",
            "organism": "Homo sapiens",
            "pathway_tags": "PCP,Adhesion,Development",
            "gravity_link": "Atypical cadherin; controls planar cell polarity and tissue morphogenesis under tension.",
            "spine_curvature_link": "Regulates neuronal morphogenesis and polarity; potential links to proprioceptive neural network establishment. (PMID: 23142725)",
            "priority_score": "75",
            "justification": "PCP component linking to neural polarity."
        },
        {
            "gene_symbol": "MACF1",
            "uniprot_id": "Q9UPN3",
            "organism": "Homo sapiens",
            "pathway_tags": "Cytoskeleton,Mechanotransduction,Wnt",
            "gravity_link": "Spectraplakin linking actin and microtubules; essential for focal adhesion turnover and Wnt signaling in osteoblasts.",
            "spine_curvature_link": "Knockout impairs osteoblast differentiation and bone formation under mechanical load; potential link to scoliotic asymmetry. (PMID: 29849033)",
            "priority_score": "88",
            "justification": "Core cytolinker translating mechanical load to osteogenic Wnt signaling."
        },
        {
            "gene_symbol": "MYO6",
            "uniprot_id": "Q9UM54",
            "organism": "Homo sapiens",
            "pathway_tags": "Gravity_Sensing,Cilia,Motor_Protein",
            "gravity_link": "Motor protein essential for maintaining the structure of hair cell stereocilia, which sense gravity and motion.",
            "spine_curvature_link": "Mutations cause deafness and vestibular dysfunction (Usher syndrome proxy); vestibular defects are linked to spine alignment. (PMID: 10427063)",
            "priority_score": "85",
            "justification": "Critical motor protein for the vestibular gravity sensor."
        },
        {
            "gene_symbol": "USH2A",
            "uniprot_id": "O75445",
            "organism": "Homo sapiens",
            "pathway_tags": "Gravity_Sensing,Cilia,Adhesion",
            "gravity_link": "Usherin; structural component of the ankle links in hair cell stereocilia, essential for mechanosensitivity.",
            "spine_curvature_link": "Mutations cause Usher Syndrome Type II; combined visual/vestibular defects contribute to postural instability and scoliosis. (PMID: 9635396)",
            "priority_score": "88",
            "justification": "Major structural component of the vestibular gravity sensing apparatus."
        },
        {
            "gene_symbol": "LAMA1",
            "uniprot_id": "P25391",
            "organism": "Homo sapiens",
            "pathway_tags": "ECM,Development,Adhesion",
            "gravity_link": "Major component of basement membranes; provides structural support and translates mechanical forces via integrins.",
            "spine_curvature_link": "Mutations cause Poretti-Boltshauser syndrome with cerebellar and potential skeletal anomalies; regulates early axis formation. (PMID: 22683713)",
            "priority_score": "82",
            "justification": "Basement membrane component essential for early structural support."
        }
    ]

    existing_genes = set()
    with open(MASTER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_genes.add(row['gene_symbol'].strip().upper())

    count = 0
    with open(MASTER_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["gene_symbol", "uniprot_id", "organism", "pathway_tags", "gravity_link", "spine_curvature_link", "priority_score", "justification"])
        for c in new_candidates:
            if c['gene_symbol'].strip().upper() not in existing_genes:
                c['priority_score'] = c['priority_score'].strip()
                writer.writerow(c)
                count += 1
                print(f"Added {c['gene_symbol']}")
            else:
                print(f"Skipped {c['gene_symbol']} (already exists)")

    print(f"Added {count} new candidates.")

if __name__ == "__main__":
    main()
