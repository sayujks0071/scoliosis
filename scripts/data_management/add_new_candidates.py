import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "NTRK3",
        "uniprot_id": "Q16288",
        "organism": "Homo sapiens",
        "pathway_tags": "Proprioception,Signaling",
        "gravity_link": "Essential for development of proprioceptive neurons (gravity sensing).",
        "spine_curvature_link": "Loss of function mutations cause congenital scoliosis due to lack of proprioceptive input. (Blecher et al., 2017)",
        "priority_score": 95,
        "justification": "Primary driver of proprioceptive-dependent spinal alignment."
    },
    {
        "gene_symbol": "OTOP1",
        "uniprot_id": "Q7RTS5",
        "organism": "Homo sapiens",
        "pathway_tags": "Gravity_Sensing,Ion_Channel",
        "gravity_link": "Forms proton channels in otoconia; essential for otolith formation (gravity sensors).",
        "spine_curvature_link": "Vestibular dysfunction is strongly linked to Idiopathic Scoliosis onset. (DOI: 10.1007/s40141-013-0026-6)",
        "priority_score": 92,
        "justification": "Essential for the hardware of vestibular gravity sensing."
    },
    {
        "gene_symbol": "CDH23",
        "uniprot_id": "Q9H251",
        "organism": "Homo sapiens",
        "pathway_tags": "Gravity_Sensing,Mechanotransduction",
        "gravity_link": "Forms tip links in hair cells; primary mechanosensor for gravity in otoliths.",
        "spine_curvature_link": "Mutations cause Usher Syndrome; vestibular defects often accompany spinal anomalies. (PubMed: 11138009)",
        "priority_score": 90,
        "justification": "Primary mechanosensor of the vestibular gravity system."
    },
    {
        "gene_symbol": "MYO7A",
        "uniprot_id": "Q13402",
        "organism": "Homo sapiens",
        "pathway_tags": "Gravity_Sensing,Motor_Protein",
        "gravity_link": "Essential for tensioning tip links in hair cells (gravity sensors).",
        "spine_curvature_link": "Usher syndrome 1B; linked to vestibular dysfunction and potential spinal alignment issues.",
        "priority_score": 90,
        "justification": "Motor protein tuning the sensitivity of gravity sensors."
    },
    {
        "gene_symbol": "ETV1",
        "uniprot_id": "Q9Y6J9",
        "organism": "Homo sapiens",
        "pathway_tags": "Proprioception,Transcription_Factor",
        "gravity_link": "Required for development of Ia afferent sensory neurons (muscle spindles).",
        "spine_curvature_link": "Essential for the stretch reflex arc maintaining postural tone against gravity. (Arber et al., 2000)",
        "priority_score": 90,
        "justification": "Transcription factor specifying the gravity-sensing reflex arc."
    },
    {
        "gene_symbol": "CCDC57",
        "uniprot_id": "Q6NSZ9",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,PCP",
        "gravity_link": "Regulates ependymal polarity and cilia beating; essential for CSF flow.",
        "spine_curvature_link": "Loss causes severe hydrocephalus and scoliosis in zebrafish. (PLOS Biology 2023)",
        "priority_score": 90,
        "justification": "Ependymal polarity regulator linking CSF flow to spine."
    },
    {
        "gene_symbol": "GPX4",
        "uniprot_id": "P36969",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Ferroptosis",
        "gravity_link": "Prevents ferroptosis downstream of Piezo1-mediated mechanical overload.",
        "spine_curvature_link": "PIEZO1-GPX4 axis drives vertebral growth plate dysplasia in scoliosis. (PMC12533149)",
        "priority_score": 88,
        "justification": "Crucial metabolic guard against mechanically-induced cell death."
    },
    {
        "gene_symbol": "DNAH5",
        "uniprot_id": "Q8TE73",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Motor_Protein",
        "gravity_link": "Outer dynein arm heavy chain; essential for motile cilia (flow sensing).",
        "spine_curvature_link": "Primary Ciliary Dyskinesia (PCD) patients have high prevalence of scoliosis. (DOI: 10.1183/09031936.00046808)",
        "priority_score": 88,
        "justification": "Classic PCD gene with strong scoliosis comorbidity."
    },
    {
        "gene_symbol": "HYDIN",
        "uniprot_id": "Q4G0P3",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Structure",
        "gravity_link": "Central pair protein essential for ciliary motility and flow sensing.",
        "spine_curvature_link": "Mutations cause hydrocephalus and scoliosis in mice and zebrafish. (UniProt)",
        "priority_score": 88,
        "justification": "Central pair protein linking ciliary motility to spine stability."
    },
    {
        "gene_symbol": "ZMYND10",
        "uniprot_id": "O75800",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Assembly",
        "gravity_link": "Essential for assembly of dynein arms in motile cilia.",
        "spine_curvature_link": "Mutations cause PCD; zmynd10 mutant zebrafish develop scoliosis. (UniProt)",
        "priority_score": 88,
        "justification": "Dynein assembly factor linked to ciliary scoliosis."
    },
    {
        "gene_symbol": "FGFR3",
        "uniprot_id": "P22607",
        "organism": "Homo sapiens",
        "pathway_tags": "Growth_Plate,Mechanotransduction",
        "gravity_link": "Negative regulator of bone growth; signaling is mechanically modulated.",
        "spine_curvature_link": "Achondroplasia features spinal stenosis and kyphosis; regulates growth plate mechanics. (PMC3087869)",
        "priority_score": 88,
        "justification": "Major growth plate regulator responsive to load."
    },
    {
        "gene_symbol": "XYLT1",
        "uniprot_id": "Q86Y38",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Enzyme",
        "gravity_link": "Initiates GAG synthesis on proteoglycans (shock absorbers).",
        "spine_curvature_link": "Mutations cause Desbuquois dysplasia with severe scoliosis. (UniProt)",
        "priority_score": 85,
        "justification": "Essential for proteoglycan synthesis and cartilage stiffness."
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
