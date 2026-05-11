import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "BMP1",
        "uniprot_id": "P13497",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Enzyme,Bone",
        "gravity_link": "Procollagen C-proteinase essential for collagen maturation and tissue tensile strength against gravity.",
        "spine_curvature_link": "Mutations cause Osteogenesis Imperfecta (types XIII) with severe spinal deformities. (DOI: 10.1002/humu.22744)",
        "priority_score": 90,
        "justification": "Enzyme defining collagen stiffness and mechanical integrity."
    },
    {
        "gene_symbol": "WNT1",
        "uniprot_id": "P04628",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Bone,Mechanotransduction",
        "gravity_link": "Key Wnt ligand regulating bone mass accumulation in response to mechanical loading.",
        "spine_curvature_link": "Mutations cause Osteogenesis Imperfecta (type XV) and early-onset severe osteoporosis/scoliosis. (DOI: 10.1056/NEJMoa1215458)",
        "priority_score": 90,
        "justification": "Direct bone mass regulator; high relevance to bone fragility/mechanics."
    },
    {
        "gene_symbol": "PLS3",
        "uniprot_id": "O60493",
        "organism": "Homo sapiens",
        "pathway_tags": "Cytoskeleton,Mechanotransduction,Actin",
        "gravity_link": "Actin bundling protein crucial for cytoskeletal stiffness and mechanotransduction.",
        "spine_curvature_link": "Mutations cause X-linked Osteoporosis with fractures and progressive scoliosis/kyphosis. (DOI: 10.1056/NEJMoa1306611)",
        "priority_score": 88,
        "justification": "Cytoskeletal regulator linking actin dynamics to bone fragility and spine curvature."
    },
    {
        "gene_symbol": "CHD7",
        "uniprot_id": "Q9P2D1",
        "organism": "Homo sapiens",
        "pathway_tags": "Chromatin,Development,Epigenetics",
        "gravity_link": "Chromatin remodeler regulating expression of developmental genes under stress.",
        "spine_curvature_link": "Mutations cause CHARGE syndrome, where scoliosis is a major feature (60-80% prevalence). (DOI: 10.1002/ajmg.a.32677)",
        "priority_score": 88,
        "justification": "Key epigenetic regulator with strong syndromic link to spinal defects."
    },
    {
        "gene_symbol": "HAS2",
        "uniprot_id": "Q92819",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Metabolism,Epigenetics",
        "gravity_link": "Synthesizes hyaluronan, essential for osmotic swelling pressure and tissue hydration against compression.",
        "spine_curvature_link": "Identified as a top epigenetic candidate with differential methylation/expression in AIS. (PMC12429667)",
        "priority_score": 85,
        "justification": "Crucial for IVD mechanics (swelling pressure) and linked to AIS via epigenetics."
    },
    {
        "gene_symbol": "KIF22",
        "uniprot_id": "Q14807",
        "organism": "Homo sapiens",
        "pathway_tags": "Cytoskeleton,Motor_Protein,Development",
        "gravity_link": "Kinesin-like protein regulating microtubule dynamics and potentially mechanosensing.",
        "spine_curvature_link": "Mutations cause Spondylocarpotarsal Synostosis Syndrome with vertebral fusions and scoliosis. (DOI: 10.1038/ng.2060)",
        "priority_score": 85,
        "justification": "Cytoskeletal motor protein with direct link to vertebral fusion."
    },
    {
        "gene_symbol": "SEC24D",
        "uniprot_id": "O95622",
        "organism": "Homo sapiens",
        "pathway_tags": "Transport,ECM,Bone",
        "gravity_link": "Essential for COPII-mediated export of procollagen from ER, determining matrix quality.",
        "spine_curvature_link": "Mutations cause Cole-Carpenter syndrome (OI-like) with severe bone fragility and scoliosis. (DOI: 10.1016/j.ajhg.2013.08.013)",
        "priority_score": 85,
        "justification": "Essential for collagen secretion and bone matrix integrity."
    },
    {
        "gene_symbol": "TMEM38B",
        "uniprot_id": "Q9NVV0",
        "organism": "Homo sapiens",
        "pathway_tags": "Ion_Channel,Bone,Signaling",
        "gravity_link": "TRIC-B channel regulating intracellular calcium release; essential for osteoblast function under load.",
        "spine_curvature_link": "Mutations cause Osteogenesis Imperfecta (type XIV) with moderate-severe scoliosis. (DOI: 10.1038/ng.2334)",
        "priority_score": 82,
        "justification": "Ion channel critical for calcium handling in bone cells."
    },
    {
        "gene_symbol": "LRP6",
        "uniprot_id": "O00144",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Bone,Wnt",
        "gravity_link": "Wnt co-receptor essential for transducing mechanical signals in bone (mechanosome).",
        "spine_curvature_link": "Mutations cause osteoporosis and neural tube defects; essential for vertebral segmentation. (DOI: 10.1056/NEJMoa013478)",
        "priority_score": 82,
        "justification": "Core component of Wnt mechanotransduction complex."
    },
    {
        "gene_symbol": "FRZB",
        "uniprot_id": "Q92563",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Wnt,Development",
        "gravity_link": "Secreted Frizzled-related protein (sFRP3); modulates Wnt signaling range and activity.",
        "spine_curvature_link": "Polymorphisms associated with hip osteoarthritis and potentially spinal alignment (spondylosis). (DOI: 10.1093/hmg/ddl100)",
        "priority_score": 80,
        "justification": "Regulator of Wnt signaling diffusion and activity."
    },
    {
        "gene_symbol": "PCDH10",
        "uniprot_id": "Q9H7H6",
        "organism": "Homo sapiens",
        "pathway_tags": "Adhesion,Signaling,Epigenetics",
        "gravity_link": "Protocadherin involved in cell-cell adhesion and tissue boundary formation.",
        "spine_curvature_link": "Downregulated in bone tissue of AIS patients; potential epigenetic biomarker. (PMC12429667)",
        "priority_score": 80,
        "justification": "Adhesion molecule identified as a tissue-specific biomarker in AIS."
    },
    {
        "gene_symbol": "SPARC",
        "uniprot_id": "P09486",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Signaling,Bone",
        "gravity_link": "Osteonectin; matricellular protein regulating collagen assembly and mineralization under load.",
        "spine_curvature_link": "Mutations cause Osteogenesis Imperfecta (type XVII) with scoliosis/kyphosis. (DOI: 10.1016/j.ajhg.2015.04.017)",
        "priority_score": 80,
        "justification": "Matricellular regulator of collagen and bone quality."
    },
    {
        "gene_symbol": "IFITM5",
        "uniprot_id": "A6NNB3",
        "organism": "Homo sapiens",
        "pathway_tags": "Bone,Mineralization,Immune",
        "gravity_link": "BRIL; osteoblast-specific membrane protein essential for mineralization.",
        "spine_curvature_link": "Mutations cause Osteogenesis Imperfecta (type V) with hyperplastic callus and scoliosis. (DOI: 10.1056/NEJMoa1208643)",
        "priority_score": 82,
        "justification": "Critical for bone mineralization and structure."
    },
    {
        "gene_symbol": "NPR2",
        "uniprot_id": "P20594",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Growth_Plate,Mechanotransduction",
        "gravity_link": "Receptor for C-type Natriuretic Peptide (CNP); regulates endochondral ossification.",
        "spine_curvature_link": "Mutations cause Acromesomelic Dysplasia, Maroteaux type (AMDM) with spinal abnormalities. (DOI: 10.1038/ng1100-305)",
        "priority_score": 82,
        "justification": "Regulator of long bone growth and vertebral plate physiology."
    },
    {
        "gene_symbol": "EN1",
        "uniprot_id": "Q05925",
        "organism": "Homo sapiens",
        "pathway_tags": "Development,Transcription_Factor,Patterning",
        "gravity_link": "Engrailed-1; regulates dorso-ventral patterning and limb development.",
        "spine_curvature_link": "Essential for proper vertebral column segmentation and dorsal identity. (DOI: 10.1038/361699a0)",
        "priority_score": 80,
        "justification": "Transcription factor determining dorsal (spine) vs ventral identity."
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
