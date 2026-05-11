import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "CCDC151",
        "uniprot_id": "Q5XM36",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Motility,PCP",
        "gravity_link": "Essential for IFT-dependent assembly of outer dynein arms (gravity/flow sensors).",
        "spine_curvature_link": "Mutations cause PCD with Situs Inversus; laterality defects link to spinal curvature. (DOI: 10.1038/nature09445)",
        "priority_score": 90,
        "justification": "Direct link between ciliary motility, laterality, and spinal symmetry."
    },
    {
        "gene_symbol": "TTC21B",
        "uniprot_id": "Q7Z4L5",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,IFT,Skeleton",
        "gravity_link": "Retrograde IFT component (IFT139) essential for ciliary signal transduction.",
        "spine_curvature_link": "Mutations cause Jeune Asphyxiating Thoracic Dystrophy and Nephronophthisis with skeletal defects. (DOI: 10.1038/ng.776)",
        "priority_score": 88,
        "justification": "Skeletal ciliopathy gene regulating ciliary signaling."
    },
    {
        "gene_symbol": "MAPK7",
        "uniprot_id": "Q13164",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Signaling,Flow",
        "gravity_link": "ERK5 is a critical sensor of fluid shear stress in endothelial cells and bone.",
        "spine_curvature_link": "Regulates osteoblast differentiation; deletion leads to bone loss and potential structural weakness. (DOI: 10.1016/j.bone.2017.10.026)",
        "priority_score": 85,
        "justification": "Primary shear stress signaling hub."
    },
    {
        "gene_symbol": "KLF2",
        "uniprot_id": "Q9Y5W3",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Flow,Mechanotransduction",
        "gravity_link": "Master transcription factor driven by fluid flow and ciliary signaling.",
        "spine_curvature_link": "Essential for vascular tone (Batson's plexus relevance) and bone homeostasis. (DOI: 10.1161/CIRCRESAHA.108.176222)",
        "priority_score": 85,
        "justification": "Master regulator of flow-mediated gene expression."
    },
    {
        "gene_symbol": "SMO",
        "uniprot_id": "Q99835",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Signaling,Mechanotransduction",
        "gravity_link": "Smoothened is the primary transducer of Hedgehog signaling in the primary cilium.",
        "spine_curvature_link": "Hedgehog signaling is essential for vertebral patterning; SMO inhibition mimics scoliosis-like defects. (DOI: 10.1016/j.ydbio.2009.05.572)",
        "priority_score": 88,
        "justification": "Central node of the ciliary Hedgehog pathway."
    },
    {
        "gene_symbol": "KIF17",
        "uniprot_id": "Q9P2E2",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Transport,Motor_Protein",
        "gravity_link": "Kinesin-2 motor for anterograde IFT; maintains ciliary structure for flow sensing.",
        "spine_curvature_link": "Essential for zebrafish spine straightening; ciliary defect link. (DOI: 10.1016/j.devcel.2005.10.019)",
        "priority_score": 85,
        "justification": "Motor protein maintaining the ciliary sensor."
    },
    {
        "gene_symbol": "THBS1",
        "uniprot_id": "P07996",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Mechanotransduction,Signaling",
        "gravity_link": "Mechanically activates TGF-beta by unfolding; matricellular stress response.",
        "spine_curvature_link": "Regulates bone remodeling and collagen fibril organization. (DOI: 10.1038/nature04177)",
        "priority_score": 85,
        "justification": "Mechanically activated regulator of TGF-beta."
    },
    {
        "gene_symbol": "THBS2",
        "uniprot_id": "P35442",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Structure,Development",
        "gravity_link": "Regulates collagen fibrillogenesis and tissue tensile strength.",
        "spine_curvature_link": "Deficiency leads to ligamentous laxity and kyphosis/scoliosis in mice. (DOI: 10.1038/sj.jid.5700762)",
        "priority_score": 85,
        "justification": "Critical for ligamentous integrity of the spine."
    },
    {
        "gene_symbol": "ITGA10",
        "uniprot_id": "O75578",
        "organism": "Homo sapiens",
        "pathway_tags": "Adhesion,Mechanotransduction,Growth_Plate",
        "gravity_link": "Chondrocyte-specific integrin binding collagen type II; senses growth plate load.",
        "spine_curvature_link": "Mutations cause chondrodysplasia in dogs; essential for growth plate proliferation/mechanics. (DOI: 10.1371/journal.pgen.1004580)",
        "priority_score": 88,
        "justification": "The growth plate specific integrin receptor."
    },
    {
        "gene_symbol": "BANF1",
        "uniprot_id": "O75531",
        "organism": "Homo sapiens",
        "pathway_tags": "Nucleus,Mechanotransduction,Structure",
        "gravity_link": "Bridges DNA to inner nuclear membrane (LINC); determines nuclear stiffness.",
        "spine_curvature_link": "Mutations cause Nestor-Guillermo Progeria Syndrome with skeletal lysis and potential deformities. (DOI: 10.1016/j.ajhg.2011.10.013)",
        "priority_score": 88,
        "justification": "Key regulator of nuclear stiffness and stability."
    },
    {
        "gene_symbol": "SORBS1",
        "uniprot_id": "Q9BX66",
        "organism": "Homo sapiens",
        "pathway_tags": "Adhesion,Cytoskeleton,Signaling",
        "gravity_link": "Ponsin; localizes to focal adhesions and stress fibers, sensing tension.",
        "spine_curvature_link": "Regulates cytoskeletal organization; potential link via focal adhesion signaling. (UniProt)",
        "priority_score": 82,
        "justification": "Focal adhesion scaffold linking signaling to tension."
    },
    {
        "gene_symbol": "DLC1",
        "uniprot_id": "Q96QB1",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Cytoskeleton,Mechanotransduction",
        "gravity_link": "RhoGAP activated by mechanical tension; regulates actomyosin contractility.",
        "spine_curvature_link": "Essential for neural tube closure and axial elongation; knockout is lethal/defective. (DOI: 10.1091/mbc.E06-03-0174)",
        "priority_score": 82,
        "justification": "Tension-regulated inhibitor of RhoA."
    },
    {
        "gene_symbol": "CFAP53",
        "uniprot_id": "Q96M91",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Motility,PCP",
        "gravity_link": "Essential for nodal flow (symmetry breaking); gravity/flow sensing.",
        "spine_curvature_link": "Mutations cause visceral heterotaxy and laterality defects often with spinal anomalies. (DOI: 10.1016/j.ajhg.2011.08.004)",
        "priority_score": 88,
        "justification": "Laterality gene linking nodal flow to body axis."
    },
    {
        "gene_symbol": "GPR161",
        "uniprot_id": "Q8N6U8",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Signaling,GPCR",
        "gravity_link": "Ciliary GPCR sensing flow/mechanics; represses Hedgehog in absence of signal.",
        "spine_curvature_link": "Mutations cause skeletal defects and spina bifida; essential for vertebral patterning. (DOI: 10.1073/pnas.1422844112)",
        "priority_score": 85,
        "justification": "G-protein coupled receptor gating ciliary signals."
    },
    {
        "gene_symbol": "CRIM1",
        "uniprot_id": "Q9NZV1",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Development,BMP",
        "gravity_link": "Tethers BMPs to the cell surface; sensitizes cells to local signals.",
        "spine_curvature_link": "Variants associated with AIS in GWAS studies; regulates bone morphogen gradients. (DOI: 10.1038/s41467-018-06619-7)",
        "priority_score": 82,
        "justification": "BMP modulator linked to scoliosis susceptibility."
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
