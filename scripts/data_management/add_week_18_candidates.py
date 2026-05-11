import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "COL1A2",
        "uniprot_id": "P08123",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Bone,Mechanotransduction",
        "gravity_link": "Major load-bearing collagen type I alpha 2 chain; essential for tissue stiffness against gravity.",
        "spine_curvature_link": "Mutations cause Osteogenesis Imperfecta Type I-IV, characterized by severe progressive scoliosis. (DOI: 10.1016/j.spam.2014.11.002)",
        "priority_score": 90,
        "justification": "Primary structural failure against gravity in OI; partner of COL1A1."
    },
    {
        "gene_symbol": "COL6A2",
        "uniprot_id": "P12110",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Muscle,Adhesion",
        "gravity_link": "Collagen VI microfibrils anchor muscle cells to the ECM, transmitting contractile force.",
        "spine_curvature_link": "Mutations cause Ullrich Congenital Muscular Dystrophy, featuring severe scoliosis and spinal rigidity. (PMC8283577)",
        "priority_score": 88,
        "justification": "Critical for muscle-matrix coupling and spinal stability."
    },
    {
        "gene_symbol": "COL6A3",
        "uniprot_id": "P12111",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Muscle,Adhesion",
        "gravity_link": "Collagen VI alpha 3 chain; essential for microfibril assembly and muscle anchorage.",
        "spine_curvature_link": "Mutations cause Ullrich CMD and Bethlem Myopathy with prominent spinal deformities. (PMC8283577)",
        "priority_score": 88,
        "justification": "Critical for muscle-matrix coupling and spinal stability."
    },
    {
        "gene_symbol": "NEB",
        "uniprot_id": "P20929",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Cytoskeleton,Mechanotransduction",
        "gravity_link": "Giant actin-binding protein regulating thin filament length and force generation against gravity.",
        "spine_curvature_link": "Mutations cause Nemaline Myopathy Type 2, frequently associated with scoliosis and rigid spine. (DOI: 10.1093/brain/awh615)",
        "priority_score": 88,
        "justification": "Regulator of sarcomere structure and muscle tone."
    },
    {
        "gene_symbol": "ACTA1",
        "uniprot_id": "P68133",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Cytoskeleton,Contractility",
        "gravity_link": "Skeletal muscle alpha-actin; the core component of the contractile apparatus resisting gravity.",
        "spine_curvature_link": "Mutations cause Nemaline Myopathy Type 3 with severe congenital scoliosis. (DOI: 10.1093/brain/awh615)",
        "priority_score": 88,
        "justification": "Core contractile protein essential for postural muscle function."
    },
    {
        "gene_symbol": "TPM3",
        "uniprot_id": "P06753",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Cytoskeleton,Contractility",
        "gravity_link": "Tropomyosin 3; regulates actin-myosin interaction and muscle contraction tone.",
        "spine_curvature_link": "Mutations cause Nemaline Myopathy Type 1 and Congenital Fiber Type Disproportion with scoliosis. (DOI: 10.1093/brain/awh615)",
        "priority_score": 85,
        "justification": "Regulator of muscle contraction and fiber type identity."
    },
    {
        "gene_symbol": "ITGA7",
        "uniprot_id": "Q13683",
        "organism": "Homo sapiens",
        "pathway_tags": "Adhesion,Muscle,Mechanotransduction",
        "gravity_link": "Integrin alpha-7; primary laminin receptor in muscle, transmitting force to ECM.",
        "spine_curvature_link": "Mutations cause Congenital Muscular Dystrophy with early-onset scoliosis. (DOI: 10.1038/ng0698-151)",
        "priority_score": 88,
        "justification": "Primary mechanolink between muscle cytoskeleton and ECM."
    },
    {
        "gene_symbol": "TNNT1",
        "uniprot_id": "P13805",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Contractility",
        "gravity_link": "Troponin T1 (slow skeletal); regulates muscle contraction in postural (slow-twitch) muscles.",
        "spine_curvature_link": "Mutations cause Nemaline Myopathy Type 5 (Amish type) with severe scoliosis. (DOI: 10.1038/ng0600-172)",
        "priority_score": 85,
        "justification": "Essential for function of slow-twitch postural muscles."
    },
    {
        "gene_symbol": "CFL2",
        "uniprot_id": "Q9Y281",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Cytoskeleton,Regulation",
        "gravity_link": "Cofilin-2; regulates actin filament dynamics in muscle.",
        "spine_curvature_link": "Mutations cause Nemaline Myopathy Type 7 with scoliosis. (DOI: 10.1016/j.ajhg.2006.11.014)",
        "priority_score": 85,
        "justification": "Regulator of actin dynamics in muscle."
    },
    {
        "gene_symbol": "KBTBD13",
        "uniprot_id": "C9JR72",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Cytoskeleton,Ubiquitination",
        "gravity_link": "Kelch repeat protein regulating muscle structure and ubiquitin-mediated degradation.",
        "spine_curvature_link": "Mutations cause Nemaline Myopathy Type 6 with specific core-rod pathology and scoliosis. (DOI: 10.1016/j.ajhg.2010.10.019)",
        "priority_score": 85,
        "justification": "Muscle-specific ubiquitin ligase adaptor linked to myopathy."
    },
    {
        "gene_symbol": "LMOD3",
        "uniprot_id": "Q0VAK6",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Cytoskeleton,Assembly",
        "gravity_link": "Leiomodin-3; essential for thin filament nucleation and length regulation in sarcomeres.",
        "spine_curvature_link": "Mutations cause Nemaline Myopathy Type 10 with severe scoliosis. (DOI: 10.1038/ncomms6067)",
        "priority_score": 85,
        "justification": "Critical for sarcomere assembly and maintenance."
    },
    {
        "gene_symbol": "KLHL40",
        "uniprot_id": "Q2TBA0",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Ubiquitination,Stability",
        "gravity_link": "Promotes stability of thin filament proteins (NEB, LMOD3) essential for gravity resistance.",
        "spine_curvature_link": "Mutations cause Nemaline Myopathy Type 8 with severe fetal akinesia and scoliosis. (DOI: 10.1016/j.ajhg.2013.05.026)",
        "priority_score": 88,
        "justification": "Master stabilizer of the thin filament complex."
    },
    {
        "gene_symbol": "KLHL41",
        "uniprot_id": "O60662",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Ubiquitination,Stability",
        "gravity_link": "Regulates stability of Nebulin; essential for sarcomere integrity.",
        "spine_curvature_link": "Mutations cause Nemaline Myopathy Type 9 with scoliosis. (DOI: 10.1016/j.ajhg.2013.10.013)",
        "priority_score": 85,
        "justification": "Stabilizer of Nebulin."
    },
    {
        "gene_symbol": "MYPN",
        "uniprot_id": "Q86TC9",
        "organism": "Homo sapiens",
        "pathway_tags": "Muscle,Cytoskeleton,Structure",
        "gravity_link": "Myopalladin; links sarcomere to nucleus and sarcoplasmic reticulum (mechanotransduction).",
        "spine_curvature_link": "Mutations cause Nemaline Myopathy Type 11 and cardiomyopathy; scoliosis observed. (DOI: 10.1016/j.nmd.2016.10.005)",
        "priority_score": 82,
        "justification": "Linker protein in the sarcomeric mechanotransduction network."
    },
    {
        "gene_symbol": "MEPE",
        "uniprot_id": "Q9NQ76",
        "organism": "Homo sapiens",
        "pathway_tags": "Bone,Mineralization,Mechanotransduction",
        "gravity_link": "Matrix Extracellular Phosphoglycoprotein; osteocyte mechanosensor regulating mineralization.",
        "spine_curvature_link": "Regulates bone mass and phosphate homeostasis; dysfunction leads to osteomalacia/deformity. (DOI: 10.1359/jbmr.2003.18.8.1486)",
        "priority_score": 82,
        "justification": "Key regulator of bone mineralization density under load."
    },
    {
        "gene_symbol": "FGF23",
        "uniprot_id": "Q9GZV9",
        "organism": "Homo sapiens",
        "pathway_tags": "Bone,Signaling,Metabolism",
        "gravity_link": "Regulates phosphate homeostasis and vitamin D; essential for bone stiffness.",
        "spine_curvature_link": "Excess FGF23 causes X-linked Hypophosphatemia (XLH) with rachitic spinal deformities (kyphoscoliosis). (DOI: 10.1056/NEJMoa1902430)",
        "priority_score": 88,
        "justification": "Major systemic regulator of bone mineral content and stiffness."
    },
    {
        "gene_symbol": "MKS1",
        "uniprot_id": "Q9NXB0",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,PCP,Development",
        "gravity_link": "Meckel Syndrome Type 1; essential for ciliary transition zone and signaling.",
        "spine_curvature_link": "Mutations cause Meckel-Gruber syndrome; skeletal dysplasia and polydactyly common. (DOI: 10.1038/ng1714)",
        "priority_score": 85,
        "justification": "Ciliopathy gene essential for ciliary integrity."
    },
    {
        "gene_symbol": "TMEM138",
        "uniprot_id": "Q9NPI0",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,PCP,Development",
        "gravity_link": "Required for ciliogenesis and vesicular transport to the cilium.",
        "spine_curvature_link": "Mutations cause Joubert Syndrome with skeletal defects. (DOI: 10.1038/ng.1027)",
        "priority_score": 82,
        "justification": "Essential for ciliary vesicle trafficking."
    },
    {
        "gene_symbol": "TMEM231",
        "uniprot_id": "Q9H6L2",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,PCP,Development",
        "gravity_link": "Component of the transition zone complex; barrier for ciliary membrane protein diffusion.",
        "spine_curvature_link": "Mutations cause Meckel-Gruber and Joubert syndromes with skeletal anomalies. (DOI: 10.1038/ng.1027)",
        "priority_score": 82,
        "justification": "Essential for ciliary transition zone function."
    },
    {
        "gene_symbol": "TCTN2",
        "uniprot_id": "Q96GX1",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,PCP,Signaling",
        "gravity_link": "Tectonic family member; regulates ciliary membrane composition and Hedgehog signaling.",
        "spine_curvature_link": "Mutations cause Meckel-Gruber and Joubert syndromes. (DOI: 10.1038/ng.902)",
        "priority_score": 82,
        "justification": "Regulator of ciliary membrane composition."
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
