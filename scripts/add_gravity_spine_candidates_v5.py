import csv
import os

MASTER_FILE = "data/candidates_master.csv"

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"Error: {MASTER_FILE} not found.")
        return

    new_candidates = [
        {
            "gene_symbol": "LIMS1",
            "uniprot_id": "P48059",
            "organism": "Homo sapiens",
            "pathway_tags": "Mechanotransduction,Adhesion,Integrin",
            "gravity_link": "Integrin-IPP complex component; essential for focal adhesion mechanotransduction.",
            "spine_curvature_link": "Loss causes severe muscle defects and potential skeletal misalignment. (Wu, 2004)",
            "priority_score": "88",
            "justification": "Strong mechanotransduction link via focal adhesion complex."
        },
        {
            "gene_symbol": "PARVA",
            "uniprot_id": "Q9NVD7",
            "organism": "Homo sapiens",
            "pathway_tags": "Mechanotransduction,Adhesion,Actin",
            "gravity_link": "Links integrins to actin cytoskeleton; essential for force transmission.",
            "spine_curvature_link": "Essential for muscle-tendon junction integrity and force transmission. (Sepulveda, 2005)",
            "priority_score": "88",
            "justification": "Essential for force transmission."
        },
        {
            "gene_symbol": "CDC42",
            "uniprot_id": "P60953",
            "organism": "Homo sapiens",
            "pathway_tags": "Cytoskeleton,Growth_Plate,Polarity",
            "gravity_link": "Regulates actin dynamics and chondrocyte polarity in growth plate.",
            "spine_curvature_link": "Conditional deletion in cartilage leads to severe skeletal dysplasia and scoliosis. (Melendez, 2011)",
            "priority_score": "85",
            "justification": "Growth plate polarity regulator."
        },
        {
            "gene_symbol": "RAC1",
            "uniprot_id": "P63000",
            "organism": "Homo sapiens",
            "pathway_tags": "Cytoskeleton,Bone,Mechanotransduction",
            "gravity_link": "Small GTPase essential for osteoblast mechanotransduction and cytoskeletal organization.",
            "spine_curvature_link": "Conditional deletion in osteoblasts causes osteopenia and spinal deformities. (Koumouli, 2021)",
            "priority_score": "85",
            "justification": "Osteoblast mechanotransduction."
        },
        {
            "gene_symbol": "BBS2",
            "uniprot_id": "Q9BXC9",
            "organism": "Homo sapiens",
            "pathway_tags": "Cilia,Trafficking,Syndromic",
            "gravity_link": "BBSome component; cilia are gravity/flow sensors.",
            "spine_curvature_link": "Bardet-Biedl Syndrome patients have scoliosis (15-20%). (Beales, 1999)",
            "priority_score": "85",
            "justification": "Syndromic scoliosis link via cilia."
        },
        {
            "gene_symbol": "MEOX2",
            "uniprot_id": "P50222",
            "organism": "Homo sapiens",
            "pathway_tags": "Segmentation,Somite,Transcription_Factor",
            "gravity_link": "Partner of MEOX1; essential for sclerotome development and vertebral formation.",
            "spine_curvature_link": "Meox1/Meox2 double mutants lack vertebral bodies entirely. (Mankoo, 2003)",
            "priority_score": "85",
            "justification": "Essential for vertebral formation."
        },
        {
            "gene_symbol": "IBSP",
            "uniprot_id": "P21815",
            "organism": "Homo sapiens",
            "pathway_tags": "Bone,ECM,Mineralization",
            "gravity_link": "Integrin-binding sialoprotein; essential for bone mineralization and mechanical stiffness.",
            "spine_curvature_link": "Regulates bone mechanical properties; deficiency affects stiffness. (Gordon, 2007)",
            "priority_score": "82",
            "justification": "Bone mineralization link."
        },
        {
            "gene_symbol": "SRC",
            "uniprot_id": "P12931",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Bone,Mechanotransduction",
            "gravity_link": "Proto-oncogene tyrosine-protein kinase; key transducer at focal adhesions.",
            "spine_curvature_link": "Essential for osteoclast function; knockout leads to osteopetrosis and spinal modeling defects. (Destaing, 2008)",
            "priority_score": "85",
            "justification": "Key transducer at focal adhesions."
        },
        {
            "gene_symbol": "USP9X",
            "uniprot_id": "Q93008",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Development,Cilia",
            "gravity_link": "Regulates TGF-beta and BMP signaling; skeletal defects in X-linked syndrome.",
            "spine_curvature_link": "Mutations cause Female-restricted X-linked syndrome with skeletal defects and scoliosis. (Homan, 2014)",
            "priority_score": "85",
            "justification": "Syndromic link via TGF-beta regulation."
        },
        {
            "gene_symbol": "WNT7A",
            "uniprot_id": "O00755",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Development,Wnt",
            "gravity_link": "Regulates limb and dorso-ventral patterning; mutations cause skeletal defects.",
            "spine_curvature_link": "Mutations cause Al-Awadi/Raas-Rothschild syndrome with severe skeletal/spinal anomalies. (Woods, 2006)",
            "priority_score": "82",
            "justification": "Wnt signaling in skeletal patterning."
        }
    ]

    existing_genes = set()
    with open(MASTER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_genes.add(row['gene_symbol'])

    count = 0
    with open(MASTER_FILE, 'a') as f:
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
