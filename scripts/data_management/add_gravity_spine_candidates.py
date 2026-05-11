import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "ACVR1",
        "uniprot_id": "Q04771",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Mechanotransduction,Bone",
        "gravity_link": "FOP causative mutation (R206H) alters mechanosensing (stiffness sensing) and leads to heterotopic ossification.",
        "spine_curvature_link": "Fibrodysplasia Ossificans Progressiva (FOP) causes severe spinal fusion and deformities. (DOI: 10.1091/mbc.E18-05-0311)",
        "priority_score": "95",
        "justification": "Direct causative mutation linking mechanosensing failure to catastrophic spinal ossification."
    },
    {
        "gene_symbol": "TGFB2",
        "uniprot_id": "P61812",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,ECM,Mechanotransduction",
        "gravity_link": "TGF-beta signaling is mechanically regulated by ECM strain; essential for tissue maintenance under load.",
        "spine_curvature_link": "Loeys-Dietz Syndrome Type 4 features severe, rapidly progressive scoliosis. (DOI: 10.1038/ng.974)",
        "priority_score": "88",
        "justification": "Key signaling ligand for load-dependent tissue maintenance; strong syndromic link."
    },
    {
        "gene_symbol": "SLC26A2",
        "uniprot_id": "P50443",
        "organism": "Homo sapiens",
        "pathway_tags": "Ion_Transport,Cartilage,Mechanotransduction",
        "gravity_link": "Sulfate transporter essential for cartilage proteoglycan sulfation (aggrecan), which provides compressive stiffness against gravity.",
        "spine_curvature_link": "Diastrophic Dysplasia is characterized by severe kyphoscoliosis. (DOI: 10.1002/humu.1380050104)",
        "priority_score": "88",
        "justification": "Essential for the chemical basis of cartilage stiffness (sulfation)."
    },
    {
        "gene_symbol": "ELN",
        "uniprot_id": "P15502",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Structure,Elasticity",
        "gravity_link": "Elastin provides long-range elasticity and recoil against gravity loading.",
        "spine_curvature_link": "Williams Syndrome (Elastin haploinsufficiency) has 34% scoliosis prevalence. (PMC4081883)",
        "priority_score": "88",
        "justification": "Major structural determinant of tissue elasticity; strong clinical link."
    },
    {
        "gene_symbol": "SKI",
        "uniprot_id": "P12755",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Development",
        "gravity_link": "Repressor of TGF-beta signaling; pathway is mechanically activated by ECM strain.",
        "spine_curvature_link": "Shprintzen-Goldberg Syndrome causes Marfanoid habitus and scoliosis. (DOI: 10.1038/ng1016)",
        "priority_score": "85",
        "justification": "Negative regulator of the mechanosensitive TGF-beta pathway."
    },
    {
        "gene_symbol": "BBS10",
        "uniprot_id": "Q8TAM1",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Chaperone",
        "gravity_link": "Chaperonin essential for BBSome assembly and ciliogenesis; cilia are gravity/flow sensors.",
        "spine_curvature_link": "Bardet-Biedl Syndrome (major locus) has 16-20% scoliosis prevalence. (GeneReviews)",
        "priority_score": "85",
        "justification": "Major ciliopathy gene with significant scoliosis comorbidity."
    },
    {
        "gene_symbol": "P3H1",
        "uniprot_id": "Q32P28",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Enzyme",
        "gravity_link": "Modifies collagen (prolyl 3-hydroxylation) to ensure proper folding and stability under mechanical stress.",
        "spine_curvature_link": "Osteogenesis Imperfecta Type VIII (recessive) causes severe scoliosis. (DOI: 10.1056/NEJMoa063804)",
        "priority_score": "85",
        "justification": "Essential enzyme for collagen mechanical quality."
    },
    {
        "gene_symbol": "CRTAP",
        "uniprot_id": "O75718",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Protein",
        "gravity_link": "Part of the collagen prolyl 3-hydroxylation complex; essential for bone matrix quality.",
        "spine_curvature_link": "Osteogenesis Imperfecta Type VII (recessive) causes scoliosis. (DOI: 10.1056/NEJMoa063804)",
        "priority_score": "85",
        "justification": "Component of the collagen modification complex essential for stiffness."
    },
    {
        "gene_symbol": "PPIB",
        "uniprot_id": "P23284",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Chaperone",
        "gravity_link": "Cyclophilin B; collagen chaperone ensuring proper folding for load resistance.",
        "spine_curvature_link": "Osteogenesis Imperfecta Type IX (recessive) causes scoliosis. (DOI: 10.1086/522237)",
        "priority_score": "85",
        "justification": "Collagen chaperone critical for matrix integrity."
    },
    {
        "gene_symbol": "MYH7",
        "uniprot_id": "P12883",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Motor_Protein",
        "gravity_link": "Slow myosin heavy chain; essential for maintaining postural tone against gravity.",
        "spine_curvature_link": "Mutations cause Congenital Scoliosis (PMC11525624) and Laing distal myopathy.",
        "priority_score": "85",
        "justification": "Primary motor protein for slow-twitch postural muscles; direct scoliosis link."
    },
    {
        "gene_symbol": "SMAD2",
        "uniprot_id": "Q15796",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Mechanotransduction",
        "gravity_link": "Effector of TGF-beta signaling; pathway is mechanically activated.",
        "spine_curvature_link": "Loeys-Dietz Syndrome Type 6 features scoliosis. (DOI: 10.1038/ng.974)",
        "priority_score": "85",
        "justification": "Downstream effector of the mechanosensitive TGF-beta pathway."
    },
    {
        "gene_symbol": "TRPS1",
        "uniprot_id": "Q9UHF7",
        "organism": "Homo sapiens",
        "pathway_tags": "Transcription_Factor,Bone",
        "gravity_link": "Regulates chondrocyte proliferation and differentiation under load; zinc finger factor.",
        "spine_curvature_link": "Trichorhinophalangeal Syndrome Type I features scoliosis. (MedlinePlus)",
        "priority_score": "82",
        "justification": "Transcriptional regulator of chondrocyte phenotype."
    },
    {
        "gene_symbol": "SHOX",
        "uniprot_id": "O15266",
        "organism": "Homo sapiens",
        "pathway_tags": "Transcription_Factor,Growth",
        "gravity_link": "Dose-dependent regulator of growth in limb and vertebral column.",
        "spine_curvature_link": "Leri-Weill Dyschondrosteosis; mesomelic shortening and scoliosis are common. (GeneReviews)",
        "priority_score": "82",
        "justification": "Key regulator of skeletal growth proportions."
    },
    {
        "gene_symbol": "GDF11",
        "uniprot_id": "O95390",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Segmentation",
        "gravity_link": "TGF-beta family member regulating anterior-posterior patterning (axial identity).",
        "spine_curvature_link": "Linked to vertebral hypersegmentation and rib anomalies. (PMC10829358)",
        "priority_score": "80",
        "justification": "Regulator of vertebral segmentation number and identity."
    },
    {
        "gene_symbol": "FLNC",
        "uniprot_id": "Q14315",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Cytoskeleton,Mechanotransduction",
        "gravity_link": "Filamin C; actin crosslinker acting as mechanosensor in muscle Z-discs.",
        "spine_curvature_link": "Mutations cause myofibrillar myopathy; linked to muscle weakness and potential spine issues. (Orphanet)",
        "priority_score": "80",
        "justification": "Muscle-specific mechanosensor essential for Z-disc integrity."
    }
]

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"Error: {MASTER_FILE} not found.")
        return

    existing_symbols = set()
    with open(MASTER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_symbols.add(row['gene_symbol'])

    new_rows = []
    for c in new_candidates:
        if c['gene_symbol'] not in existing_symbols:
            new_rows.append(c)
            print(f"Adding new candidate: {c['gene_symbol']}")
        else:
            print(f"Skipping existing candidate: {c['gene_symbol']}")

    if new_rows:
        with open(MASTER_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=new_candidates[0].keys())
            for row in new_rows:
                writer.writerow(row)
        print(f"Added {len(new_rows)} new candidates to {MASTER_FILE}")
    else:
        print("No new candidates added.")

if __name__ == "__main__":
    main()
