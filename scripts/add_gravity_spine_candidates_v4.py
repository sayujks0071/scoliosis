import csv
import os

MASTER_FILE = "data/candidates_master.csv"

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"Error: {MASTER_FILE} not found.")
        return

    new_candidates = [
        {
            "gene_symbol": "TGFB3",
            "uniprot_id": "P10600",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Mechanotransduction,ECM",
            "gravity_link": "TGF-beta signaling is mechanically regulated by ECM strain; essential for tissue maintenance under load.",
            "spine_curvature_link": "Loeys-Dietz Syndrome Type 5 features scoliosis and aortic aneurysm. (DOI: 10.1038/ng.974)",
            "priority_score": "88",
            "justification": "Syndromic link + mechanotransduction."
        },
        {
            "gene_symbol": "TTC21B",
            "uniprot_id": "Q7Z4L5",
            "organism": "Homo sapiens",
            "pathway_tags": "Cilia,Transport,IFT",
            "gravity_link": "IFT139; retrograde ciliary transport essential for flow sensing (gravity proxy).",
            "spine_curvature_link": "Mutations cause Jeune Asphyxiating Thoracic Dystrophy and Nephronophthisis with skeletal defects. (DOI: 10.1038/ng.812)",
            "priority_score": "85",
            "justification": "Ciliopathy skeletal link."
        },
        {
            "gene_symbol": "WDR19",
            "uniprot_id": "Q8NEZ3",
            "organism": "Homo sapiens",
            "pathway_tags": "Cilia,Transport,IFT",
            "gravity_link": "IFT144; essential for retrograde ciliary transport and signaling.",
            "spine_curvature_link": "Mutations cause Jeune Syndrome and Sensenbrenner Syndrome (Cranioectodermal Dysplasia). (DOI: 10.1016/j.ajhg.2011.10.003)",
            "priority_score": "85",
            "justification": "Ciliopathy skeletal link."
        },
        {
            "gene_symbol": "NSD1",
            "uniprot_id": "Q96L73",
            "organism": "Homo sapiens",
            "pathway_tags": "Epigenetics,Growth,Chromatin",
            "gravity_link": "Epigenetic regulator of growth genes; rapid growth is a key risk factor for spinal instability (Energy Deficit).",
            "spine_curvature_link": "Sotos Syndrome (Cerebral Gigantism) features overgrowth and scoliosis (40-50%). (GeneReviews)",
            "priority_score": "88",
            "justification": "Strong 'Rapid Growth' link to scoliosis."
        },
        {
            "gene_symbol": "EZH2",
            "uniprot_id": "Q15910",
            "organism": "Homo sapiens",
            "pathway_tags": "Epigenetics,Growth,Chromatin",
            "gravity_link": "Histone methyltransferase regulating developmental timing and growth.",
            "spine_curvature_link": "Weaver Syndrome features overgrowth, accelerated bone age, and scoliosis. (DOI: 10.1038/ng.2058)",
            "priority_score": "88",
            "justification": "Strong 'Rapid Growth' link to scoliosis."
        },
        {
            "gene_symbol": "PTPN11",
            "uniprot_id": "Q06124",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Mechanotransduction,Integrin",
            "gravity_link": "SHP2 is essential for integrin signaling and mechanotransduction downstream of focal adhesions.",
            "spine_curvature_link": "Noonan Syndrome features scoliosis (15-30%) and chest deformities. (GeneReviews)",
            "priority_score": "85",
            "justification": "Mechanotransduction core + syndromic link."
        },
        {
            "gene_symbol": "PORCN",
            "uniprot_id": "Q9H237",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Wnt,Secretion",
            "gravity_link": "Essential for Wnt ligand secretion; Wnt pathway is mechanically regulated in bone.",
            "spine_curvature_link": "Focal Dermal Hypoplasia (Goltz Syndrome) features skeletal defects including scoliosis and vertebral anomalies. (GeneReviews)",
            "priority_score": "82",
            "justification": "Wnt secretion link to skeletal defects."
        },
        {
            "gene_symbol": "MBTPS2",
            "uniprot_id": "O43462",
            "organism": "Homo sapiens",
            "pathway_tags": "ER,Stress,Signaling",
            "gravity_link": "Regulates UPR and response to ER stress (mechanical stress); cleaves OASIS (CREB3L1).",
            "spine_curvature_link": "Osteogenesis Imperfecta Type XIX features scoliosis and bone fragility. (DOI: 10.1038/s41467-017-00566-7 context)",
            "priority_score": "85",
            "justification": "UPR/ER stress mechanosensing link."
        },
        {
            "gene_symbol": "SP7",
            "uniprot_id": "Q8NFJ8",
            "organism": "Homo sapiens",
            "pathway_tags": "Bone,Transcription_Factor,Mechanotransduction",
            "gravity_link": "Essential for osteoblast differentiation downstream of mechanosensitive Runx2.",
            "spine_curvature_link": "Mutations cause Osteogenesis Imperfecta Type XII with bone fragility and deformities. (DOI: 10.1016/j.ajhg.2006.10.008)",
            "priority_score": "88",
            "justification": "Master regulator of bone formation downstream of mechanics."
        },
        {
            "gene_symbol": "IFT43",
            "uniprot_id": "Q96EF6",
            "organism": "Homo sapiens",
            "pathway_tags": "Cilia,Transport,IFT",
            "gravity_link": "Component of IFT complex A; essential for retrograde transport.",
            "spine_curvature_link": "Mutations cause Sensenbrenner Syndrome (Cranioectodermal Dysplasia) with skeletal anomalies. (DOI: 10.1016/j.ajhg.2011.04.020)",
            "priority_score": "82",
            "justification": "Ciliopathy link."
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
