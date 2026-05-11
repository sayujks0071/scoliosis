import csv
import os

MASTER_FILE = "data/candidates_master.csv"

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"Error: {MASTER_FILE} not found.")
        return

    new_candidates = [
        {
            "gene_symbol": "DAAM1",
            "uniprot_id": "Q9Y4D1",
            "organism": "Homo sapiens",
            "pathway_tags": "PCP,Cytoskeleton,Wnt",
            "gravity_link": "Formin that nucleates actin polymerization downstream of Wnt/PCP; essential for cell polarity and shape against stress.",
            "spine_curvature_link": "Regulates myocardial and gut rotation; knockout mice have cardiac defects; PCP defects are linked to scoliosis. (PMID: 15312739)",
            "priority_score": "85",
            "justification": "Core PCP effector."
        },
        {
            "gene_symbol": "SMAD1",
            "uniprot_id": "Q15797",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,BMP,Bone",
            "gravity_link": "BMP effector; pathway is mechanically modulated in bone; essential for osteoblast differentiation.",
            "spine_curvature_link": "Conditional deletion in cartilage leads to chondrodysplasia and potential spinal defects. (PMID: 15630473)",
            "priority_score": "82",
            "justification": "BMP effector essential for bone formation."
        },
        {
            "gene_symbol": "CHRD",
            "uniprot_id": "Q9H2X0",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Development,BMP",
            "gravity_link": "BMP antagonist establishing dorso-ventral axis; essential for vertebral patterning.",
            "spine_curvature_link": "Mutations in Chrd causes vertebral fusion and segmentation defects in mice. (PMID: 9814708)",
            "priority_score": "85",
            "justification": "Axis patterning regulator."
        },
        {
            "gene_symbol": "GPC6",
            "uniprot_id": "Q9Y625",
            "organism": "Homo sapiens",
            "pathway_tags": "ECM,Signaling,Wnt",
            "gravity_link": "Cell surface heparan sulfate proteoglycan; regulates Wnt/Hedgehog distribution.",
            "spine_curvature_link": "Mutations cause Omodysplasia 1, characterized by severe short stature and scoliosis/kyphosis. (PMID: 19481194)",
            "priority_score": "88",
            "justification": "Strong syndromic link via morphogen gradient regulation."
        },
        {
            "gene_symbol": "CSNK1E",
            "uniprot_id": "P49674",
            "organism": "Homo sapiens",
            "pathway_tags": "PCP,Circadian,Wnt",
            "gravity_link": "Phosphorylates Dishevelled; regulates Wnt/PCP signaling and Circadian clock (Period proteins).",
            "spine_curvature_link": "Wnt/PCP regulation is key for spine; circadian disruption affects bone mass. (PMID: 24726359)",
            "priority_score": "82",
            "justification": "Dual PCP/Circadian role."
        },
        {
            "gene_symbol": "FZD3",
            "uniprot_id": "Q9NPG1",
            "organism": "Homo sapiens",
            "pathway_tags": "PCP,Signaling,Wnt",
            "gravity_link": "Wnt receptor mediating PCP signaling and neural tube closure.",
            "spine_curvature_link": "Fzd3 knockout mice exhibit neural tube defects and skeletal anomalies. (PMID: 12514104)",
            "priority_score": "80",
            "justification": "Wnt receptor essential for PCP."
        },
        {
            "gene_symbol": "WNT9B",
            "uniprot_id": "O14905",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Wnt,Development",
            "gravity_link": "Regulates plane of cell division (oriented cell division) in kidney and skeleton.",
            "spine_curvature_link": "Essential for convergent extension; loss leads to skeletal defects. (PMID: 16051731)",
            "priority_score": "80",
            "justification": "Wnt ligand regulating oriented cell division."
        },
        {
            "gene_symbol": "RSPO2",
            "uniprot_id": "Q6UXX9",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Wnt,Limb",
            "gravity_link": "Potentiates Wnt signaling; essential for limb and skeletal development.",
            "spine_curvature_link": "Mutations cause Tetra-amelia syndrome with severe spinal column defects. (PMID: 18451854)",
            "priority_score": "85",
            "justification": "Strong Wnt potentiator linked to severe skeletal defects."
        },
        {
            "gene_symbol": "SOX5",
            "uniprot_id": "Q02938",
            "organism": "Homo sapiens",
            "pathway_tags": "Transcription_Factor,Cartilage,Development",
            "gravity_link": "Essential for chondrogenesis (Sox trio); regulates notochord sheath formation (hydrostatic skeleton).",
            "spine_curvature_link": "Sox5 knockout mice have severe skeletal defects and kyphosis. (PMID: 9635432)",
            "priority_score": "85",
            "justification": "Master chondrogenic factor defining notochord sheath."
        },
        {
            "gene_symbol": "SOX6",
            "uniprot_id": "P35712",
            "organism": "Homo sapiens",
            "pathway_tags": "Transcription_Factor,Cartilage,Development",
            "gravity_link": "Partners with Sox5/Sox9; essential for growth plate proliferation and notochord sheath.",
            "spine_curvature_link": "Sox6 null mice exhibit severe skeletal dysplasia and spinal curvature. (PMID: 9635432)",
            "priority_score": "85",
            "justification": "Master chondrogenic factor defining growth plate mechanics."
        },
        {
            "gene_symbol": "ACVR2B",
            "uniprot_id": "Q13705",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Left-Right,BMP",
            "gravity_link": "Activin receptor type IIB; essential for left-right asymmetry sensing at the node.",
            "spine_curvature_link": "Mutations cause Heterotaxy syndrome with frequent scoliosis and vertebral anomalies. (PMID: 11504841)",
            "priority_score": "90",
            "justification": "Direct link to L-R asymmetry sensing and heterotaxy."
        },
        {
            "gene_symbol": "GDF1",
            "uniprot_id": "P20753",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Left-Right,BMP",
            "gravity_link": "Nodal cofactor; essential for establishing left-right asymmetry.",
            "spine_curvature_link": "Mutations cause Right Atrial Isomerism and skeletal defects (scoliosis/vertebral anomalies). (PMID: 11707563)",
            "priority_score": "88",
            "justification": "L-R asymmetry ligand essential for axis establishment."
        },
        {
            "gene_symbol": "NODAL",
            "uniprot_id": "Q96S42",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Left-Right,Development",
            "gravity_link": "Master regulator of left-right asymmetry; expression driven by nodal flow (ciliary sensing).",
            "spine_curvature_link": "Heterotaxy syndromes often feature scoliosis due to organ/skeletal situs defects. (PMID: 10471506)",
            "priority_score": "88",
            "justification": "L-R asymmetry master regulator."
        },
        {
            "gene_symbol": "PITX2",
            "uniprot_id": "Q99697",
            "organism": "Homo sapiens",
            "pathway_tags": "Transcription_Factor,Left-Right,Muscle",
            "gravity_link": "Downstream of Nodal; specifies left-sided identity in organs and muscle.",
            "spine_curvature_link": "Regulates asymmetric muscle development; mutations cause Axenfeld-Rieger syndrome (potential skeletal links). (PMID: 9782098)",
            "priority_score": "85",
            "justification": "L-R asymmetry effector in muscle."
        },
        {
            "gene_symbol": "ZIC3",
            "uniprot_id": "O60481",
            "organism": "Homo sapiens",
            "pathway_tags": "Transcription_Factor,Left-Right,Wnt",
            "gravity_link": "Zinc finger protein regulating left-right axis formation and Wnt signaling.",
            "spine_curvature_link": "Mutations cause X-linked Heterotaxy with vertebral anomalies and scoliosis. (PMID: 9731535)",
            "priority_score": "88",
            "justification": "L-R asymmetry and Wnt signaling regulator."
        },
        {
            "gene_symbol": "FOXH1",
            "uniprot_id": "O75593",
            "organism": "Homo sapiens",
            "pathway_tags": "Transcription_Factor,Signaling,TGF-beta",
            "gravity_link": "Transduces Nodal signaling; essential for midline patterning and L-R axis.",
            "spine_curvature_link": "Essential for anterior primitive streak formation; defects lead to midline and vertebral anomalies. (PMID: 9782099)",
            "priority_score": "82",
            "justification": "Nodal transducer essential for midline."
        },
        {
            "gene_symbol": "CFC1",
            "uniprot_id": "P0CG37",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Left-Right,Nodal",
            "gravity_link": "Cripto-FRL-1-Cryptic family; cofactor for Nodal signaling (L-R asymmetry).",
            "spine_curvature_link": "Mutations cause Heterotaxy syndrome with vertebral segmentation defects. (PMID: 11593318)",
            "priority_score": "85",
            "justification": "Nodal cofactor linked to segmentation."
        },
        {
            "gene_symbol": "DAND5",
            "uniprot_id": "Q8N907",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Left-Right,Cilia",
            "gravity_link": "Cerberus-like 2; antagonizes Nodal on the right side; expression regulated by ciliary flow.",
            "spine_curvature_link": "Mutations cause Heterotaxy and congenital heart defects; linked to ciliary flow sensing failure. (PMID: 23603762)",
            "priority_score": "90",
            "justification": "Direct link to ciliary flow sensing and symmetry breaking."
        },
        {
            "gene_symbol": "MMP14",
            "uniprot_id": "P50281",
            "organism": "Homo sapiens",
            "pathway_tags": "ECM,Remodeling,Mechanotransduction",
            "gravity_link": "Membrane-type 1 MMP; essential for pericellular collagenolysis and cell migration; activity increases with stiffness.",
            "spine_curvature_link": "Mmp14 knockout mice develop severe skeletal defects, osteopenia, and kyphosis. (PMID: 10471506)",
            "priority_score": "90",
            "justification": "Direct collagenolysis link to kyphosis."
        },
        {
            "gene_symbol": "INPPL1",
            "uniprot_id": "O15037",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Mechanotransduction,ECM",
            "gravity_link": "SHIP2; regulates PI3K signaling and focal adhesion dynamics; negative regulator of insulin signaling.",
            "spine_curvature_link": "Mutations cause Opsismodysplasia with severe vertebral ossification defects. (PMID: 23312969)",
            "priority_score": "85",
            "justification": "Skeletal dysplasia link via focal adhesion signaling."
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
