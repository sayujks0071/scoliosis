import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "PCDH15",
        "uniprot_id": "Q96QU1",
        "organism": "Homo sapiens",
        "pathway_tags": "Gravity_Sensing,Mechanotransduction,Tip_Link",
        "gravity_link": "Tip link component; essential for mechanotransduction in hair cells.",
        "spine_curvature_link": "Mutations cause Usher Syndrome Type 1F; vestibular dysfunction often linked to spinal anomalies. (PubMed: 12068292)",
        "priority_score": 90,
        "justification": "Essential tip-link component for gravity mechanotransduction."
    },
    {
        "gene_symbol": "USH1C",
        "uniprot_id": "Q9Y6N9",
        "organism": "Homo sapiens",
        "pathway_tags": "Gravity_Sensing,Scaffold,Mechanotransduction",
        "gravity_link": "Harmonin; scaffolding protein in stereocilia essential for mechanotransduction.",
        "spine_curvature_link": "Mutations cause Usher Syndrome Type 1C; linked to vestibular defects and scoliosis. (PubMed: 10985330)",
        "priority_score": 90,
        "justification": "Key scaffold for the mechanotransduction complex."
    },
    {
        "gene_symbol": "TMC1",
        "uniprot_id": "Q8TDI8",
        "organism": "Homo sapiens",
        "pathway_tags": "Gravity_Sensing,Ion_Channel,Mechanotransduction",
        "gravity_link": "Pore-forming subunit of the mechanotransduction channel in hair cells.",
        "spine_curvature_link": "Mutations cause deafness and vestibular dysfunction; potential link to postural control. (PubMed: 25168391)",
        "priority_score": 90,
        "justification": "The core mechanotransduction channel pore."
    },
    {
        "gene_symbol": "TMC2",
        "uniprot_id": "Q8TDI7",
        "organism": "Homo sapiens",
        "pathway_tags": "Gravity_Sensing,Ion_Channel,Mechanotransduction",
        "gravity_link": "Redundant function with TMC1 in mechanotransduction channel formation.",
        "spine_curvature_link": "Essential for vestibular hair cell function; knockout mice show balance defects. (PubMed: 25168391)",
        "priority_score": 88,
        "justification": "Redundant core mechanotransduction channel."
    },
    {
        "gene_symbol": "WDR19",
        "uniprot_id": "Q8NEZ3",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Transport,IFT",
        "gravity_link": "IFT144; component of IFT-A complex essential for retrograde ciliary transport.",
        "spine_curvature_link": "Mutations cause Sensenbrenner syndrome (Cranioectodermal dysplasia) with skeletal anomalies. (PubMed: 21940737)",
        "priority_score": 88,
        "justification": "IFT-A component linked to syndromic skeletal defects."
    },
    {
        "gene_symbol": "RSPH1",
        "uniprot_id": "Q8WXN3",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Motility,Structure",
        "gravity_link": "Radial Spoke Head 1; structural component of radial spokes in motile cilia.",
        "spine_curvature_link": "Mutations cause Primary Ciliary Dyskinesia (PCD); cilia motility essential for spine straightness. (PubMed: 22464730)",
        "priority_score": 88,
        "justification": "Radial spoke component critical for ciliary motility."
    },
    {
        "gene_symbol": "RSPH4A",
        "uniprot_id": "Q53AD0",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Motility,Structure",
        "gravity_link": "Radial Spoke Head 4 Homolog A; essential for radial spoke assembly.",
        "spine_curvature_link": "Mutations cause PCD with specific ultrastructural defects; linked to scoliosis in PCD. (PubMed: 17351641)",
        "priority_score": 88,
        "justification": "Radial spoke head essential for ciliary function."
    },
    {
        "gene_symbol": "RSPH9",
        "uniprot_id": "Q9H1X1",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Motility,Structure",
        "gravity_link": "Radial Spoke Head 9; component of the radial spoke head.",
        "spine_curvature_link": "Mutations cause PCD with central pair defects; associated with scoliosis. (PubMed: 19131665)",
        "priority_score": 88,
        "justification": "Radial spoke component linked to PCD and spine."
    },
    {
        "gene_symbol": "DNAI1",
        "uniprot_id": "Q9UI46",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Motility,Motor_Protein",
        "gravity_link": "Outer dynein arm intermediate chain 1; essential for ciliary beating.",
        "spine_curvature_link": "Mutations cause PCD; dynein arms drive the ciliary motility required for spine alignment. (PubMed: 11598177)",
        "priority_score": 88,
        "justification": "Major outer dynein arm component."
    },
    {
        "gene_symbol": "DNAI2",
        "uniprot_id": "Q9GZS0",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Motility,Motor_Protein",
        "gravity_link": "Outer dynein arm intermediate chain 2; essential for dynein assembly.",
        "spine_curvature_link": "Mutations cause PCD; loss of motility leads to potential spinal curvature. (PubMed: 18451862)",
        "priority_score": 88,
        "justification": "Outer dynein arm component."
    },
    {
        "gene_symbol": "CCNO",
        "uniprot_id": "P22674",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Multiciliogenesis",
        "gravity_link": "Cyclin O; essential for generation of multiple motile cilia.",
        "spine_curvature_link": "Mutations cause reduced ciliary generation and PCD-like symptoms. (PubMed: 25109062)",
        "priority_score": 85,
        "justification": "Master regulator of multiciliogenesis."
    },
    {
        "gene_symbol": "MCIDAS",
        "uniprot_id": "Q8N5S5",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Multiciliogenesis,Transcription_Factor",
        "gravity_link": "Multiciliate Differentiation And DNA Synthesis Associated Cell Cycle Protein.",
        "spine_curvature_link": "Promotes multiciliogenesis; essential for mucociliary clearance and potentially CSF flow. (PubMed: 20616174)",
        "priority_score": 85,
        "justification": "Key driver of multiciliated cell differentiation."
    },
    {
        "gene_symbol": "PIFO",
        "uniprot_id": "Q8WZ60",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Formation",
        "gravity_link": "Primary Cilia Formation protein; involved in ciliary node formation.",
        "spine_curvature_link": "Essential for left-right asymmetry; defects lead to laterality and spinal issues. (PubMed: 21256070)",
        "priority_score": 85,
        "justification": "Regulator of ciliary node formation and asymmetry."
    },
    {
        "gene_symbol": "COL10A1",
        "uniprot_id": "Q03692",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Cartilage,Growth_Plate",
        "gravity_link": "Collagen Type X Alpha 1; specific to hypertrophic zone of growth plate.",
        "spine_curvature_link": "Mutations cause Schmid Metaphyseal Chondrodysplasia (SMCD) with spinal changes. (PubMed: 8240439)",
        "priority_score": 85,
        "justification": "Hypertrophic cartilage collagen essential for ossification."
    },
    {
        "gene_symbol": "MATN3",
        "uniprot_id": "O15232",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Cartilage",
        "gravity_link": "Matrilin-3; filamentous matrix protein in cartilage.",
        "spine_curvature_link": "Mutations cause Multiple Epiphyseal Dysplasia (MED) with spinal involvement. (PubMed: 11135246)",
        "priority_score": 85,
        "justification": "Cartilage matrix protein linked to dysplasia."
    },
    {
        "gene_symbol": "TRAAK",
        "uniprot_id": "Q9NYG8",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Ion_Channel",
        "gravity_link": "Mechanosensitive Potassium Channel; activated by membrane stretch.",
        "spine_curvature_link": "Involved in noxious mechanosensation; potential role in proprioception. (PubMed: 10619472)",
        "priority_score": 82,
        "justification": "Mechanosensitive K+ channel modulating excitability."
    },
    {
        "gene_symbol": "CELSR2",
        "uniprot_id": "Q9HCU4",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Cadherin,Signaling",
        "gravity_link": "Cadherin EGF LAG Seven-Pass G-Type Receptor 2; PCP component.",
        "spine_curvature_link": "Essential for motile cilia orientation and neural tube closure. (PubMed: 16908628)",
        "priority_score": 85,
        "justification": "PCP receptor regulating cilia polarity."
    },
    {
        "gene_symbol": "CELSR3",
        "uniprot_id": "Q9NYQ7",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Cadherin,Axon_Guidance",
        "gravity_link": "Cadherin EGF LAG Seven-Pass G-Type Receptor 3; PCP component.",
        "spine_curvature_link": "Regulates axonal tract formation; potential link to neural control of posture. (PubMed: 16908628)",
        "priority_score": 82,
        "justification": "PCP receptor critical for neural wiring."
    },
    {
        "gene_symbol": "PRICKLE2",
        "uniprot_id": "Q7Z3G6",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Signaling",
        "gravity_link": "Prickle Homolog 2; PCP pathway component.",
        "spine_curvature_link": "Regulates tissue polarity; implicated in neural tube defects. (PubMed: 21540846)",
        "priority_score": 80,
        "justification": "PCP component linking polarity to structure."
    },
    {
        "gene_symbol": "ANKRD6",
        "uniprot_id": "Q9BZ71",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Wnt_Signaling",
        "gravity_link": "Diversin; ankyrin repeat protein in Wnt/PCP signaling.",
        "spine_curvature_link": "Modulates Wnt signaling; essential for PCP-dependent processes. (PubMed: 11459846)",
        "priority_score": 80,
        "justification": "Wnt/PCP modulator."
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
