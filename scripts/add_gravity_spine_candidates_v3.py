import csv
import os

MASTER_FILE = "data/candidates_master.csv"

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"Error: {MASTER_FILE} not found.")
        return

    new_candidates = [
        {
            "gene_symbol": "PTRF",
            "uniprot_id": "Q6NZI2",
            "organism": "Homo sapiens",
            "pathway_tags": "Mechanotransduction,Muscle,Membrane",
            "gravity_link": "Essential for caveolae formation, which buffer membrane tension during mechanical stress.",
            "spine_curvature_link": "Mutations cause Congenital Generalized Lipodystrophy type 4 with myopathy and skeletal muscle hypertrophy/stiffness. (DOI: 10.1086/526555)",
            "priority_score": "88",
            "justification": "Caveolae are critical mechanosensors; loss leads to severe muscle/skeletal phenotype."
        },
        {
            "gene_symbol": "CILP",
            "uniprot_id": "O75339",
            "organism": "Homo sapiens",
            "pathway_tags": "ECM,Cartilage,Mechanotransduction",
            "gravity_link": "Upregulated in response to mechanical loading in cartilage.",
            "spine_curvature_link": "Polymorphisms associated with Lumbar Disc Disease and potential spinal alignment issues. (DOI: 10.1038/ng1564)",
            "priority_score": "85",
            "justification": "Cartilage protein linked to disc degeneration and mechanical response."
        },
        {
            "gene_symbol": "SCX",
            "uniprot_id": "Q7RTU7",
            "organism": "Homo sapiens",
            "pathway_tags": "Tendon,Development,Transcription_Factor",
            "gravity_link": "Essential for development of tendons and ligaments, the primary force transmission tissues.",
            "spine_curvature_link": "Loss leads to severe defects in force transmission and potential spinal instability. (DOI: 10.1242/dev.01306)",
            "priority_score": "88",
            "justification": "Master regulator of tendon/ligament fate; crucial for spine stability."
        },
        {
            "gene_symbol": "MKX",
            "uniprot_id": "Q8IYA7",
            "organism": "Homo sapiens",
            "pathway_tags": "Tendon,Mechanotransduction,Transcription_Factor",
            "gravity_link": "Transcription factor regulating tendon differentiation; expression is mechanically regulated.",
            "spine_curvature_link": "Essential for collagen fibril assembly in tendons; loss leads to wavy tendons and reduced stiffness. (DOI: 10.1073/pnas.1215462110)",
            "priority_score": "85",
            "justification": "Mechanosensitive regulator of tendon stiffness."
        },
        {
            "gene_symbol": "TNMD",
            "uniprot_id": "Q9H2S6",
            "organism": "Homo sapiens",
            "pathway_tags": "Tendon,ECM,Growth",
            "gravity_link": "Regulator of tenocyte proliferation and collagen fibril maturation under load.",
            "spine_curvature_link": "Essential for tendon stiffness and integrity; disruption leads to altered mechanical properties. (DOI: 10.1128/MCB.23.16.5560-5569.2003)",
            "priority_score": "85",
            "justification": "Key marker for mature, stiff tendons resisting gravity."
        },
        {
            "gene_symbol": "PANX1",
            "uniprot_id": "Q96RD7",
            "organism": "Homo sapiens",
            "pathway_tags": "Ion_Channel,Mechanotransduction,Signaling",
            "gravity_link": "Mechanosensitive ATP release channel activated by stretch.",
            "spine_curvature_link": "Mediates purinergic signaling in osteoblasts/chondrocytes in response to load. (DOI: 10.1152/ajpcell.00222.2010)",
            "priority_score": "82",
            "justification": "Mechanosensitive ATP release channel."
        },
        {
            "gene_symbol": "WNT16",
            "uniprot_id": "Q9UBV4",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Bone,Mechanotransduction",
            "gravity_link": "Mechanosensitive Wnt ligand regulating cortical bone thickness.",
            "spine_curvature_link": "Regulation of cortical bone thickness affects vertebral fracture susceptibility and strength. (DOI: 10.1038/nature11164)",
            "priority_score": "85",
            "justification": "Key regulator of cortical bone geometry under load."
        },
        {
            "gene_symbol": "ADAMTS5",
            "uniprot_id": "Q9UNA0",
            "organism": "Homo sapiens",
            "pathway_tags": "ECM,Degradation,Cartilage",
            "gravity_link": "Major aggrecanase in cartilage; expression is mechanically regulated.",
            "spine_curvature_link": " implicated in intervertebral disc degeneration and OA; driven by abnormal loading. (DOI: 10.1002/art.22415)",
            "priority_score": "85",
            "justification": "Mechanosensitive enzyme degrading the primary compressive load bearer (aggrecan)."
        },
        {
            "gene_symbol": "ITGA10",
            "uniprot_id": "O75578",
            "organism": "Homo sapiens",
            "pathway_tags": "Adhesion,Cartilage,ECM",
            "gravity_link": "Collagen receptor on chondrocytes sensing matrix composition.",
            "spine_curvature_link": "Mutations cause chondrodysplasia with short limbs and potential spinal involvement. (DOI: 10.1371/journal.pgen.0030134)",
            "priority_score": "82",
            "justification": "Chondrocyte-specific integrin."
        },
        {
            "gene_symbol": "MYF5",
            "uniprot_id": "P13349",
            "organism": "Homo sapiens",
            "pathway_tags": "Muscle,Segmentation,Development",
            "gravity_link": "Myogenic regulatory factor defining the epaxial (back) muscle lineage.",
            "spine_curvature_link": "Essential for paraspinal muscle formation; defects lead to muscle asymmetry. (DOI: 10.1038/361699a0)",
            "priority_score": "85",
            "justification": "Defines the paraspinal muscle lineage essential for spinal support."
        },
        {
            "gene_symbol": "PAX3",
            "uniprot_id": "P23760",
            "organism": "Homo sapiens",
            "pathway_tags": "Development,Neural_Crest,Muscle",
            "gravity_link": "Key regulator of dermomyotome and migratory muscle precursors.",
            "spine_curvature_link": "Mutations cause Waardenburg syndrome; associated with skeletal defects and muscle hypoplasia. (DOI: 10.1038/ng0592-26)",
            "priority_score": "85",
            "justification": "Regulator of paraspinal and limb muscle progenitors."
        },
        {
            "gene_symbol": "COL24A1",
            "uniprot_id": "Q17RW2",
            "organism": "Homo sapiens",
            "pathway_tags": "ECM,Bone,Development",
            "gravity_link": "Fibril-forming collagen expressed in developing bone.",
            "spine_curvature_link": "Marker of osteoblast differentiation and bone formation. (DOI: 10.1016/S0945-053X(03)00021-9)",
            "priority_score": "80",
            "justification": "Bone-specific collagen."
        },
        {
            "gene_symbol": "TMEM150C",
            "uniprot_id": "Q8N7T1",
            "organism": "Homo sapiens",
            "pathway_tags": "Ion_Channel,Mechanotransduction",
            "gravity_link": "Tentonin 3; enhances mechanosensitivity of Piezo1.",
            "spine_curvature_link": "Modulates cellular response to mechanical stimuli; potential role in proprioception. (DOI: 10.1016/j.neuron.2016.06.014)",
            "priority_score": "82",
            "justification": "Amplifier of Piezo1 mechanosensitivity."
        },
        {
            "gene_symbol": "ASPN",
            "uniprot_id": "Q9BXN1",
            "organism": "Homo sapiens",
            "pathway_tags": "ECM,Cartilage,Signaling",
            "gravity_link": "Asporin; SLRP binding collagen and TGF-beta; modulates mineralization.",
            "spine_curvature_link": "Strongly associated with Intervertebral Disc Degeneration and OA. (DOI: 10.1038/ng1518)",
            "priority_score": "82",
            "justification": "SLRP linking ECM to TGF-beta signaling in the disc."
        },
        {
            "gene_symbol": "OGN",
            "uniprot_id": "P20774",
            "organism": "Homo sapiens",
            "pathway_tags": "ECM,Bone,Signaling",
            "gravity_link": "Osteoglycin; SLRP regulating collagen fibrillogenesis and bone mass.",
            "spine_curvature_link": "Linked to bone mass regulation and potential spinal fragility. (DOI: 10.1038/ng.253)",
            "priority_score": "80",
            "justification": "Regulator of bone mass and collagen organization."
        }
    ]

    existing_genes = set()
    with open(MASTER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_genes.add(row['gene_symbol'])

    with open(MASTER_FILE, 'a') as f:
        writer = csv.DictWriter(f, fieldnames=["gene_symbol", "uniprot_id", "organism", "pathway_tags", "gravity_link", "spine_curvature_link", "priority_score", "justification"])
        # No header write, appending
        count = 0
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
