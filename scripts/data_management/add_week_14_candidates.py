import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "MMP13",
        "uniprot_id": "P45452",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Degradation,Cartilage",
        "gravity_link": "Collagenase-3; main enzyme degrading type II collagen in cartilage; mechanically regulated.",
        "spine_curvature_link": "Upregulated in intervertebral disc degeneration and under mechanical overload. (DOI: 10.1002/art.10515)",
        "priority_score": 88,
        "justification": "Key collagenase in load-induced disc degeneration."
    },
    {
        "gene_symbol": "ADAMTS5",
        "uniprot_id": "Q9UNA0",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Degradation,Cartilage",
        "gravity_link": "Aggrecanase-2; key enzyme for aggrecan degradation; mechanically induced.",
        "spine_curvature_link": "Major driver of osteoarthritis and disc degeneration; mechanically induced. (DOI: 10.1016/j.joca.2008.06.015)",
        "priority_score": 88,
        "justification": "Primary aggrecanase driven by mechanical stress."
    },
    {
        "gene_symbol": "CHAD",
        "uniprot_id": "O15335",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Adhesion,Integrin",
        "gravity_link": "Chondroadherin; cartilage matrix protein promoting cell attachment via alpha2beta1 integrin.",
        "spine_curvature_link": "Essential for cartilage matrix organization; knockout mice have skeletal defects. (DOI: 10.1083/jcb.200109015)",
        "priority_score": 85,
        "justification": "Critical for chondrocyte-ECM mechanical coupling."
    },
    {
        "gene_symbol": "ASPN",
        "uniprot_id": "Q9BXN1",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Signaling,TGF-beta",
        "gravity_link": "Asporin; SLRP binding collagen and inhibiting TGF-beta; modulates matrix stiffness.",
        "spine_curvature_link": "Polymorphisms associated with disc degeneration and osteoarthritis susceptibility. (DOI: 10.1038/ng1520)",
        "priority_score": 85,
        "justification": "Genetic link to disc degeneration via TGF-beta inhibition."
    },
    {
        "gene_symbol": "OGN",
        "uniprot_id": "P20774",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Structure,Bone",
        "gravity_link": "Osteoglycin (Mimecan); SLRP regulating collagen fibrillogenesis and bone mass.",
        "spine_curvature_link": "Regulates bone mass and diameter; deficiency leads to thicker fibrils and weaker bone. (DOI: 10.1038/ng.252)",
        "priority_score": 82,
        "justification": "Regulates collagen fibril diameter and bone strength."
    },
    {
        "gene_symbol": "LUM",
        "uniprot_id": "P51884",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Structure,Collagen",
        "gravity_link": "Lumican; SLRP regulating collagen fibril assembly and tissue transparency.",
        "spine_curvature_link": "Mice deficient in lumican show skin and tendon fragility; potential spinal ligament role. (DOI: 10.1083/jcb.139.1.267)",
        "priority_score": 80,
        "justification": "Proteoglycan essential for collagen fibril organization."
    },
    {
        "gene_symbol": "FGFR2",
        "uniprot_id": "P21802",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Growth_Plate,Development",
        "gravity_link": "Fibroblast Growth Factor Receptor 2; regulates osteoblast differentiation under load.",
        "spine_curvature_link": "Mutations cause Crouzon/Apert syndromes with craniosynostosis and spinal fusion. (DOI: 10.1038/ng1294-375)",
        "priority_score": 88,
        "justification": "Key receptor for skeletal growth and fusion."
    },
    {
        "gene_symbol": "SMAD1",
        "uniprot_id": "Q15797",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Mechanotransduction,BMP",
        "gravity_link": "BMP signaling effector; mechanically phosphorylated in response to stiffness.",
        "spine_curvature_link": "Mechanically phosphorylated in response to matrix stiffness; drives osteogenesis. (DOI: 10.1038/ncb2091)",
        "priority_score": 85,
        "justification": "Mechanotransducer of BMP signaling."
    },
    {
        "gene_symbol": "TIMP1",
        "uniprot_id": "P01033",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Signaling,Inhibitor",
        "gravity_link": "Tissue inhibitor of metalloproteinases; balances MMP activity under load.",
        "spine_curvature_link": "Upregulated by mechanical strain in disc cells to counter MMPs; essential for homeostasis. (DOI: 10.1016/S0021-9290(02)00244-9)",
        "priority_score": 85,
        "justification": "Protects ECM from load-induced degradation."
    },
    {
        "gene_symbol": "DDR1",
        "uniprot_id": "Q08345",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Adhesion,Receptor",
        "gravity_link": "Collagen receptor tyrosine kinase; activation is independent of growth factors.",
        "spine_curvature_link": "Regulates ECM remodeling and cell adhesion; mechanotransduction independent of integrins. (DOI: 10.1038/ncb1570)",
        "priority_score": 85,
        "justification": "Non-integrin collagen receptor sensing matrix stiffness."
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
