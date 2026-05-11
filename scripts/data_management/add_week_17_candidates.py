import csv
import os

MASTER_FILE = "data/candidates_master.csv"

new_candidates = [
    {
        "gene_symbol": "HIF1A",
        "uniprot_id": "Q16665",
        "organism": "Homo sapiens",
        "pathway_tags": "Signaling,Metabolism,Nucleus",
        "gravity_link": "Master regulator of hypoxic response; upregulated in IVD under 'Convective Shutdown' (microgravity).",
        "spine_curvature_link": "Drives catabolic remodeling and MMP expression in loaded/unloaded discs. (Sato et al. 2025).",
        "priority_score": 95,
        "justification": "Master regulator of the Hypoxic trigger in IVD."
    },
    {
        "gene_symbol": "NR1D1",
        "uniprot_id": "P20393",
        "organism": "Homo sapiens",
        "pathway_tags": "Circadian,Metabolism,Nucleus",
        "gravity_link": "Rev-erb alpha; regulates circadian metabolism and inflammation; target of 'Chrono-Therapy' for jetlag.",
        "spine_curvature_link": "Essential for IVD clock function; regulates disc inflammation and degeneration. (Dudek et al. 2017).",
        "priority_score": 92,
        "justification": "Ligand-regulatable clock component linking rhythm to metabolism."
    },
    {
        "gene_symbol": "CLOCK",
        "uniprot_id": "O15516",
        "organism": "Homo sapiens",
        "pathway_tags": "Circadian,Nucleus",
        "gravity_link": "Core clock component (heterodimer with BMAL1); essential for sensing daily load cycles.",
        "spine_curvature_link": "IVD has an autonomous clock; disruption leads to degeneration. (Dudek et al. 2017).",
        "priority_score": 90,
        "justification": "The partner of BMAL1 in the core loop."
    },
    {
        "gene_symbol": "TEAD1",
        "uniprot_id": "P28347",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Hippo,Transcription_Factor",
        "gravity_link": "Main DNA-binding partner of YAP/TAZ; translates mechanical signals into gene expression.",
        "spine_curvature_link": "Essential for notochord integrity and vertebral growth plate function. (Dupont et al. 2011 context).",
        "priority_score": 90,
        "justification": "The effector of the YAP/TAZ gravity sensor."
    },
    {
        "gene_symbol": "PER2",
        "uniprot_id": "O15055",
        "organism": "Homo sapiens",
        "pathway_tags": "Circadian,Bone",
        "gravity_link": "Core clock gene; expression oscillates with load; regulates bone mass.",
        "spine_curvature_link": "Mutation affects bone formation and potentially spinal alignment (leptin link). (Fu et al. 2005).",
        "priority_score": 88,
        "justification": "Links circadian rhythm directly to bone mass regulation."
    },
    {
        "gene_symbol": "KANK1",
        "uniprot_id": "Q14678",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Cytoskeleton,Adhesion",
        "gravity_link": "Connects microtubules to focal adhesions; regulates integrin-mediated gravity sensing.",
        "spine_curvature_link": "Mutations cause cerebral palsy with spastic quadriplegia and scoliosis (CPSQ2). (OMIM 612936).",
        "priority_score": 88,
        "justification": "Direct genetic link to spasticity/scoliosis and mechanotransduction."
    },
    {
        "gene_symbol": "ITGB3",
        "uniprot_id": "P05106",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Adhesion,Bone",
        "gravity_link": "Forms avb3 integrin (mechanosensor); essential for osteocyte response to fluid flow/load.",
        "spine_curvature_link": "Regulates bone remodeling; polymorphisms linked to bone density/spine issues.",
        "priority_score": 85,
        "justification": "Key osteocyte mechanosensor."
    },
    {
        "gene_symbol": "TBX15",
        "uniprot_id": "Q96SF7",
        "organism": "Homo sapiens",
        "pathway_tags": "Development,Skeleton,Segmentation",
        "gravity_link": "Regulates skeletal development; patterning of the dorso-ventral axis.",
        "spine_curvature_link": "Mutations cause Cousin syndrome with cervical vertebral anomalies and scapular/pelvic hypoplasia. (PMC2668032).",
        "priority_score": 85,
        "justification": "Defining gene for Cousin syndrome vertebral defects."
    },
    {
        "gene_symbol": "PAX9",
        "uniprot_id": "P55771",
        "organism": "Homo sapiens",
        "pathway_tags": "Development,Segmentation,Vertebra",
        "gravity_link": "Essential for sclerotome differentiation (vertebral body formation).",
        "spine_curvature_link": "Pax9-deficient mice lack vertebral bodies; linked to tooth/spine anomalies. (Genes & Dev 1998).",
        "priority_score": 85,
        "justification": "Essential for vertebral body formation."
    },
    {
        "gene_symbol": "ITGA2",
        "uniprot_id": "P17301",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Adhesion,ECM",
        "gravity_link": "Collagen receptor (a2b1); senses matrix stiffness and composition.",
        "spine_curvature_link": "Expressed in IVD; mediates cell-matrix interaction in nucleus pulposus.",
        "priority_score": 82,
        "justification": "Primary collagen receptor in the IVD."
    },
    {
        "gene_symbol": "DLC1",
        "uniprot_id": "Q96QB1",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Signaling,Cytoskeleton",
        "gravity_link": "RhoGAP localized to focal adhesions; negatively regulates RhoA (gravity response).",
        "spine_curvature_link": "Essential for embryonic development; regulates cell contractility and shape.",
        "priority_score": 80,
        "justification": "Negative regulator of the RhoA gravity response."
    },
    {
        "gene_symbol": "INPP5E",
        "uniprot_id": "Q9NRR6",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Signaling,Phosphatase",
        "gravity_link": "Ciliary phosphatase essential for stability and signaling (flow sensing).",
        "spine_curvature_link": "Mutations cause Joubert syndrome (ciliopathy) with skeletal defects. (PMC5685896).",
        "priority_score": 82,
        "justification": "Phosphatase regulating ciliary membrane composition."
    },
    {
        "gene_symbol": "CEP164",
        "uniprot_id": "Q9P2B2",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Centrosome",
        "gravity_link": "Distal appendage protein required for docking the basal body (ciliogenesis).",
        "spine_curvature_link": "Mutations cause Nephronophthisis and ciliopathies with skeletal involvement.",
        "priority_score": 82,
        "justification": "Critical for the initial step of ciliogenesis."
    },
    {
        "gene_symbol": "MESP1",
        "uniprot_id": "P59096",
        "organism": "Homo sapiens",
        "pathway_tags": "Segmentation,Somite",
        "gravity_link": "Master regulator of cardiovascular and mesodermal differentiation.",
        "spine_curvature_link": "Functional redundancy with MESP2 in somite segmentation.",
        "priority_score": 80,
        "justification": "Partner of MESP2 in establishing somite polarity."
    },
    {
        "gene_symbol": "CRY1",
        "uniprot_id": "Q16526",
        "organism": "Homo sapiens",
        "pathway_tags": "Circadian,Nucleus",
        "gravity_link": "Repressor in the core clock loop; essential for rhythm generation.",
        "spine_curvature_link": "Part of the IVD autonomous clock.",
        "priority_score": 80,
        "justification": "Essential repressor in the circadian feedback loop."
    },
    {
        "gene_symbol": "TMEM216",
        "uniprot_id": "Q9P0N5",
        "organism": "Homo sapiens",
        "pathway_tags": "Cilia,Membrane",
        "gravity_link": "Localizes to ciliary base; required for ciliogenesis.",
        "spine_curvature_link": "Mutations cause Meckel-Gruber and Joubert syndromes (ciliopathies).",
        "priority_score": 80,
        "justification": "Core component of the transition zone in cilia."
    },
    {
        "gene_symbol": "TEAD4",
        "uniprot_id": "Q15561",
        "organism": "Homo sapiens",
        "pathway_tags": "Mechanotransduction,Development",
        "gravity_link": "YAP partner; regulates lineage specification.",
        "spine_curvature_link": "Involved in early embryonic patterning.",
        "priority_score": 78,
        "justification": "Developmental paralog of TEAD1."
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
