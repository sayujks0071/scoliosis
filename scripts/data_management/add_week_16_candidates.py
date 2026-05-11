import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "ITGAV",
        "uniprot_id": "P06756",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Integrin,Signaling",
        "gravity_link": "Integrin alpha-V; mechanosensor activating TGF-beta from latent complex (LAP) upon cytoskeletal tension.",
        "spine_curvature_link": "TGF-beta signaling is critical for spine development; deletion leads to cleft palate/skeletal defects. (DOI: 10.1242/dev.00843)",
        "priority_score": 88,
        "justification": "Primary mechanotransducer activating the TGF-beta pathway."
    },
    {
        "gene_symbol": "ITGA5",
        "uniprot_id": "P08648",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Adhesion,Somite",
        "gravity_link": "Integrin alpha-5; fibronectin receptor sensing matrix assembly under tension.",
        "spine_curvature_link": "Essential for somite boundary formation and maintenance; defects lead to vertebral fusion. (PMID: 8666677)",
        "priority_score": 85,
        "justification": "Required for fibronectin matrix assembly and somite integrity."
    },
    {
        "gene_symbol": "ITGA11",
        "uniprot_id": "Q9UKX5",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Adhesion,ECM",
        "gravity_link": "Integrin alpha-11; major collagen receptor on MSCs sensing tissue stiffness.",
        "spine_curvature_link": "Regulates myofibroblast differentiation and fibrosis; potential role in asymmetric stiffness in scoliosis. (DOI: 10.1016/j.matbio.2014.01.001)",
        "priority_score": 85,
        "justification": "Key stiffness sensor for mesenchymal stem cells."
    },
    {
        "gene_symbol": "LATS1",
        "uniprot_id": "O95835",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Hippo,Signaling",
        "gravity_link": "LATS1 kinase; phosphorylates YAP/TAZ in response to low stiffness/unloading.",
        "spine_curvature_link": "Hippo pathway regulates vertebral growth plate proliferation; loss leads to overgrowth. (DOI: 10.1126/science.1145880)",
        "priority_score": 85,
        "justification": "Core kinase of the Hippo mechanotransduction pathway."
    },
    {
        "gene_symbol": "LATS2",
        "uniprot_id": "Q9NRM7",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Hippo,Signaling",
        "gravity_link": "LATS2 kinase; partner of LATS1 in YAP/TAZ regulation under mechanical stress.",
        "spine_curvature_link": "Redundant role with LATS1; essential for skeletal development control. (DOI: 10.1038/ncb2207)",
        "priority_score": 85,
        "justification": "Core kinase of the Hippo mechanotransduction pathway."
    },
    {
        "gene_symbol": "DVL2",
        "uniprot_id": "O14641",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Wnt,Segmentation",
        "gravity_link": "Dishevelled-2; essential for PCP signaling aligning tissues against stress.",
        "spine_curvature_link": "Knockout mice have truncated tails and vertebral segmentation defects (Robinow-like). (DOI: 10.1038/ng856)",
        "priority_score": 85,
        "justification": "PCP effector essential for vertebral segmentation."
    },
    {
        "gene_symbol": "DVL3",
        "uniprot_id": "Q92997",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Wnt,Segmentation",
        "gravity_link": "Dishevelled-3; PCP signaling mediator.",
        "spine_curvature_link": "Dvl3-/- mice exhibit conotruncal heart defects and skeletal malformations. (DOI: 10.1242/dev.01533)",
        "priority_score": 82,
        "justification": "PCP effector linked to skeletal development."
    },
    {
        "gene_symbol": "WNT5B",
        "uniprot_id": "Q9H1J7",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Signaling,Growth_Plate",
        "gravity_link": "Wnt ligand regulating chondrocyte stacking (PCP) in the growth plate.",
        "spine_curvature_link": "Essential for proper vertebral column elongation and segmentation; shortness leads to defects. (DOI: 10.1242/dev.02104)",
        "priority_score": 85,
        "justification": "Regulates oriented cell division in the growth plate."
    },
    {
        "gene_symbol": "RYK",
        "uniprot_id": "P34925",
        "organism": "Homo sapiens",
        "pathway_tags": "PCP,Receptor,Wnt",
        "gravity_link": "Wnt receptor (atypical) transducing Wnt5a/PCP signals for tissue polarity.",
        "spine_curvature_link": "Ryk-/- mice have skeletal defects including craniofacial and spinal shortening. (DOI: 10.1038/nature03215)",
        "priority_score": 80,
        "justification": "Receptor for Wnt/PCP pathway regulating body axis elongation."
    },
    {
        "gene_symbol": "COL27A1",
        "uniprot_id": "Q8IZC6",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Cartilage,Structure",
        "gravity_link": "Collagen XXVII; structural component of the cartilage to bone transition.",
        "spine_curvature_link": "Mutations cause Steel syndrome (cervical spine instability/scoliosis). (OMIM: 615155)",
        "priority_score": 88,
        "justification": "Defining gene for Steel Syndrome with spinal instability."
    },
    {
        "gene_symbol": "ADAMTS4",
        "uniprot_id": "O75173",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Degradation,Cartilage",
        "gravity_link": "Aggrecanase-1; enzyme degrading aggrecan under mechanical stress.",
        "spine_curvature_link": "Implicated in intervertebral disc degeneration; activity increases with load. (DOI: 10.1074/jbc.M000254200)",
        "priority_score": 82,
        "justification": "Mechanosensitive enzyme degrading disc matrix."
    },
    {
        "gene_symbol": "CYR61",
        "uniprot_id": "O00622",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,ECM,Signaling",
        "gravity_link": "CCN1; matricellular protein and direct YAP/TAZ target; highly mechanosensitive.",
        "spine_curvature_link": "Regulates chondrogenesis; overexpression leads to skeletal defects. (DOI: 10.1074/jbc.M409028200)",
        "priority_score": 82,
        "justification": "Direct transcriptional target of YAP/TAZ mechanotransduction."
    },
    {
        "gene_symbol": "NOV",
        "uniprot_id": "P48745",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,ECM,Notch",
        "gravity_link": "CCN3; matricellular protein modulating Notch signaling under stress.",
        "spine_curvature_link": "Regulates osteogenesis; mutant mice have skeletal defects. (DOI: 10.1186/1471-213X-6-35)",
        "priority_score": 80,
        "justification": "Matricellular regulator of Notch signaling in bone."
    },
    {
        "gene_symbol": "MATN3",
        "uniprot_id": "O15232",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Cartilage,Structure",
        "gravity_link": "Matrilin-3; filamentous matrix protein essential for cartilage stiffness.",
        "spine_curvature_link": "Mutations cause Multiple Epiphyseal Dysplasia (MED) and potentially spinal changes. (DOI: 10.1038/ng766)",
        "priority_score": 85,
        "justification": "Structural component of cartilage matrix linked to dysplasia."
    },
    {
        "gene_symbol": "COL9A3",
        "uniprot_id": "Q14050",
        "organism": "Homo sapiens",
        "pathway_tags": "ECM,Cartilage,Structure",
        "gravity_link": "Collagen IX; FACIT collagen bridging fibrils and providing shear resistance.",
        "spine_curvature_link": "Mutations cause Multiple Epiphyseal Dysplasia (MED) with spinal involvement. (DOI: 10.1086/300460)",
        "priority_score": 85,
        "justification": "FACIT collagen essential for cartilage mechanical integrity."
    },
    {
        "gene_symbol": "HES1",
        "uniprot_id": "Q14469",
        "organism": "Homo sapiens",
        "pathway_tags": "Segmentation,Notch,Clock",
        "gravity_link": "Hairy and enhancer of split 1; cyclic expression (clock) essential for segmentation timing.",
        "spine_curvature_link": "Hes1 loss leads to severe vertebral segmentation defects and fusion. (DOI: 10.1126/science.1070283)",
        "priority_score": 85,
        "justification": "Core component of the segmentation clock oscillator."
    },
    {
        "gene_symbol": "DLL1",
        "uniprot_id": "O00548",
        "organism": "Homo sapiens",
        "pathway_tags": "Segmentation,Notch,Ligand",
        "gravity_link": "Delta-like 1; Notch ligand essential for somite boundary formation.",
        "spine_curvature_link": "Null mice have fused vertebrae and severe segmentation defects. (DOI: 10.1038/361699a0)",
        "priority_score": 88,
        "justification": "Essential ligand for establishing somite boundaries."
    },
    {
        "gene_symbol": "TBX18",
        "uniprot_id": "O95935",
        "organism": "Homo sapiens",
        "pathway_tags": "Segmentation,Somite,Transcription_Factor",
        "gravity_link": "T-box factor regulating anterior somite identity and sclerotome differentiation.",
        "spine_curvature_link": "Essential for vertebral pedicle/lamina formation; maintains segmentation. (DOI: 10.1242/dev.00971)",
        "priority_score": 85,
        "justification": "Regulator of anterior somite polarity and vertebral shape."
    },
    {
        "gene_symbol": "PHEX",
        "uniprot_id": "P78562",
        "organism": "Homo sapiens",
        "pathway_tags": "Bone,Mineralization,Signaling",
        "gravity_link": "Phosphate regulating endopeptidase; regulates bone stiffness via mineralization.",
        "spine_curvature_link": "Mutations cause X-linked hypophosphatemia with rachitic spine deformities/kyphosis. (DOI: 10.1038/ng0695-130)",
        "priority_score": 85,
        "justification": "Regulator of bone mineralization and mechanical stiffness."
    },
    {
        "gene_symbol": "DMP1",
        "uniprot_id": "Q13316",
        "organism": "Homo sapiens",
        "pathway_tags": "Bone,Mechanotransduction,Osteocyte",
        "gravity_link": "Dentin matrix acidic phosphoprotein 1; essential for osteocyte maturation and load sensing.",
        "spine_curvature_link": "Loss leads to osteomalacia and spinal deformity; critical for osteocyte dendrite formation. (DOI: 10.1016/j.cell.2003.11.002)",
        "priority_score": 88,
        "justification": "Key protein for osteocyte mechanosensing and mineralization."
    },
    {
        "gene_symbol": "IFT80",
        "uniprot_id": "Q9NVS2",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Transport,IFT",
        "gravity_link": "Intraflagellar Transport 80; essential for ciliary assembly and flow sensing.",
        "spine_curvature_link": "Mutations cause Jeune Asphyxiating Thoracic Dystrophy with short ribs and spinal anomalies. (DOI: 10.1038/ng.150)",
        "priority_score": 88,
        "justification": "Ciliopathy gene linking flow sensing to thoracic/spinal skeletal defects."
    },
    {
        "gene_symbol": "IFT172",
        "uniprot_id": "Q9UG01",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Transport,IFT",
        "gravity_link": "Intraflagellar Transport 172; regulates ciliary signaling (Hedgehog).",
        "spine_curvature_link": "Mutations cause Mainzer-Saldino syndrome (skeletal dysplasia) and Jeune syndrome. (DOI: 10.1016/j.ajhg.2013.10.019)",
        "priority_score": 85,
        "justification": "IFT complex component essential for skeletal ciliogenesis."
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
