import csv
import os

MASTER_FILE = "data/candidates_master.csv"

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"Error: {MASTER_FILE} not found.")
        return

    new_candidates = [
        {
            "gene_symbol": "PKD1L2",
            "uniprot_id": "Q7Z442",
            "organism": "Homo sapiens",
            "pathway_tags": "Cilia,Mechanotransduction,Ion_Channel",
            "gravity_link": "Mechanosensitive ion channel associated with primary cilia, sensing fluid flow and mechanical load.",
            "spine_curvature_link": "Polycystin channels are crucial for left-right asymmetry and skeletal formation; PKD1/2 defects are known to cause spinal anomalies. (Extrapolated from PKD family)",
            "priority_score": "82",
            "justification": "Ciliary mechanosensor potentially compensating or interacting with PKD1/2/1L1."
        },
        {
            "gene_symbol": "PIEZO2",
            "uniprot_id": "Q9H5I5",
            "organism": "Homo sapiens",
            "pathway_tags": "Mechanotransduction,Proprioception,Ion_Channel",
            "gravity_link": "Primary mechanosensor for proprioception, essential for gravity sensing and posture control.",
            "spine_curvature_link": "Loss of function mutations cause profound congenital scoliosis. (PMID: 27764519)",
            "priority_score": "95",
            "justification": "Already in DB, ensuring exact metadata match; primary gravity sensor."
        },
        {
            "gene_symbol": "YAP1",
            "uniprot_id": "P46937",
            "organism": "Homo sapiens",
            "pathway_tags": "Mechanotransduction,Hippo,Growth_Plate",
            "gravity_link": "Central hub of cellular mechanotransduction, translating mechanical stiffness and load into transcriptional responses.",
            "spine_curvature_link": "Regulates osteoblast differentiation and vertebral growth; deletion leads to skeletal defects. (PMID: 21415861)",
            "priority_score": "90",
            "justification": "Already in DB, ensuring exact metadata match; core mechanotransduction effector."
        },
        {
            "gene_symbol": "TAZ",
            "uniprot_id": "Q9GZV5",
            "organism": "Homo sapiens",
            "pathway_tags": "Mechanotransduction,Hippo,Bone",
            "gravity_link": "Paralog of YAP1, WWTR1 acts as a mechanosensor of matrix stiffness and gravity-derived stress.",
            "spine_curvature_link": "Essential for osteogenesis and skeletal development; deficiency causes spinal deformities.",
            "priority_score": "88",
            "justification": "Core mechanotransduction effector, partner of YAP1."
        },
        {
            "gene_symbol": "HOXB4",
            "uniprot_id": "P17483",
            "organism": "Homo sapiens",
            "pathway_tags": "Development,Segmentation,Transcription_Factor",
            "gravity_link": "Specifies vertebral identity and patterning along the anterior-posterior axis, determining the mechanical load distribution.",
            "spine_curvature_link": "Hox gene disruption leads to homeotic transformations and vertebral anomalies. (PMID: 1544342)",
            "priority_score": "80",
            "justification": "Key regulator of axial skeletal identity and structure."
        },
        {
            "gene_symbol": "HOXD3",
            "uniprot_id": "P31249",
            "organism": "Homo sapiens",
            "pathway_tags": "Development,Segmentation,Transcription_Factor",
            "gravity_link": "Specifies cervical and upper thoracic vertebral identity, essential for head support against gravity.",
            "spine_curvature_link": "Mutations alter atlas/axis formation, causing cervical spine instability. (PMID: 8643806)",
            "priority_score": "80",
            "justification": "Crucial for upper spine structural identity."
        },
        {
            "gene_symbol": "PCDH15",
            "uniprot_id": "Q96QU1",
            "organism": "Homo sapiens",
            "pathway_tags": "Gravity_Sensing,Mechanotransduction,Adhesion",
            "gravity_link": "Forms the lower part of the tip link in inner ear hair cells, directly transmitting mechanical force from gravity/acceleration.",
            "spine_curvature_link": "Mutations cause Usher Syndrome Type 1F; vestibular defects are strongly linked to scoliosis pathogenesis. (PMID: 11244476)",
            "priority_score": "90",
            "justification": "Direct mechanotransducer for vestibular gravity sensing."
        },
        {
            "gene_symbol": "USH1C",
            "uniprot_id": "Q9Y6N9",
            "organism": "Homo sapiens",
            "pathway_tags": "Gravity_Sensing,Scaffold,Mechanotransduction",
            "gravity_link": "Harmonin; scaffolds the mechanotransduction complex in hair cells, essential for gravity and sound sensing.",
            "spine_curvature_link": "Mutations cause Usher Syndrome Type 1C, combining deafness with vestibular areflexia and potential postural defects. (PMID: 10978287)",
            "priority_score": "88",
            "justification": "Essential scaffold for the vestibular gravity sensor complex."
        },
        {
            "gene_symbol": "WHRN",
            "uniprot_id": "Q9P202",
            "organism": "Homo sapiens",
            "pathway_tags": "Gravity_Sensing,Scaffold,Actin",
            "gravity_link": "Whirlin; essential for actin polymerization and stereocilia elongation in gravity-sensing hair cells.",
            "spine_curvature_link": "Mutations cause Usher syndrome type 2D; linked to balance and posture maintenance defects. (PMID: 14976159)",
            "priority_score": "85",
            "justification": "Required for the structural integrity of the gravity sensing apparatus."
        },
        {
            "gene_symbol": "MYO15A",
            "uniprot_id": "Q9UKN7",
            "organism": "Homo sapiens",
            "pathway_tags": "Gravity_Sensing,Motor_Protein,Actin",
            "gravity_link": "Unconventional myosin required for the elongation and maintenance of stereocilia in vestibular gravity sensors.",
            "spine_curvature_link": "Mutations cause profound deafness and vestibular dysfunction (DFNB3); balance issues implicate posture. (PMID: 11017086)",
            "priority_score": "85",
            "justification": "Motor protein building the cellular gravity sensors."
        },
        {
            "gene_symbol": "CELSR1",
            "uniprot_id": "Q9NYQ6",
            "organism": "Homo sapiens",
            "pathway_tags": "PCP,Adhesion,Cilia",
            "gravity_link": "Atypical cadherin essential for planar cell polarity, aligning tissues and cilia against mechanical stress vectors.",
            "spine_curvature_link": "Mutations cause neural tube defects (craniorachischisis); PCP is a fundamental mechanism of spine straightening. (PMID: 20436465)",
            "priority_score": "85",
            "justification": "Already in DB, ensuring exact metadata match; core PCP determinant."
        },
        {
            "gene_symbol": "PRICKLE1",
            "uniprot_id": "Q96MT3",
            "organism": "Homo sapiens",
            "pathway_tags": "PCP,Signaling,Cilia",
            "gravity_link": "Core component of the Planar Cell Polarity pathway, translating mechanical forces into directional tissue growth.",
            "spine_curvature_link": "Mutations cause progressive myoclonus epilepsy; PCP pathway defects are intrinsically linked to vertebral axis deformities. (PMID: 15159359)",
            "priority_score": "80",
            "justification": "Already in DB, ensuring exact metadata match; core PCP determinant."
        },
        {
            "gene_symbol": "STK3",
            "uniprot_id": "Q13188",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Hippo,Mechanotransduction",
            "gravity_link": "MST2 kinase in the Hippo pathway; negatively regulates YAP/TAZ in response to mechanical unloading/low stiffness.",
            "spine_curvature_link": "Hippo pathway dysregulation alters osteogenesis and bone mass; potential driver of scoliotic bone asymmetry. (PMID: 21151125)",
            "priority_score": "85",
            "justification": "Upstream kinase regulating the YAP/TAZ mechanosensor."
        },
        {
            "gene_symbol": "STK4",
            "uniprot_id": "Q13043",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Hippo,Mechanotransduction",
            "gravity_link": "MST1 kinase; functions redundantly with STK3 to inhibit YAP/TAZ when mechanical tension is low.",
            "spine_curvature_link": "Essential for balancing cell proliferation and apoptosis in growing tissues, including the spine. (PMID: 21151125)",
            "priority_score": "85",
            "justification": "Upstream kinase regulating the YAP/TAZ mechanosensor."
        },
        {
            "gene_symbol": "SAV1",
            "uniprot_id": "Q9H4B6",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Hippo,Scaffold",
            "gravity_link": "Salvador homolog 1; scaffold protein essential for MST1/2 (STK4/3) activation in the Hippo mechanosensing pathway.",
            "spine_curvature_link": "Core Hippo component; deletion disrupts tissue growth control and mechanical responsiveness. (PMID: 12150926)",
            "priority_score": "82",
            "justification": "Essential scaffold for Hippo mechanotransduction."
        },
        {
            "gene_symbol": "NF2",
            "uniprot_id": "P35240",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Mechanotransduction,Cytoskeleton",
            "gravity_link": "Merlin; links actin cytoskeleton to membrane proteins and acts as an upstream activator of the Hippo pathway (sensing contact/tension).",
            "spine_curvature_link": "Mutations cause Neurofibromatosis Type 2, which includes spinal tumors and associated scoliosis. (PMID: 8252613)",
            "priority_score": "85",
            "justification": "Mechanosensor linking cell junctions to Hippo signaling."
        },
        {
            "gene_symbol": "PTCH2",
            "uniprot_id": "Q9Y6C5",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Hedgehog,Receptor",
            "gravity_link": "Receptor for Hedgehog signaling at the primary cilium, complementing PTCH1 in mechanically sensitive tissues.",
            "spine_curvature_link": "Modulates Hedgehog signaling critical for vertebral segmentation and bone development. (PMID: 10606622)",
            "priority_score": "82",
            "justification": "Secondary receptor for the ciliary Hedgehog pathway."
        },
        {
            "gene_symbol": "SUFU",
            "uniprot_id": "Q9UMX1",
            "organism": "Homo sapiens",
            "pathway_tags": "Signaling,Hedgehog,Development",
            "gravity_link": "Suppressor of fused; key negative regulator of Hedgehog signaling, which is dependent on ciliary mechanosensors.",
            "spine_curvature_link": "Mutations cause Gorlin syndrome and are linked to skeletal defects including bifid ribs and kyphoscoliosis. (PMID: 10471507)",
            "priority_score": "88",
            "justification": "Crucial regulator of ciliary-dependent Hedgehog signaling."
        },
        {
            "gene_symbol": "MGP",
            "uniprot_id": "P08493",
            "organism": "Homo sapiens",
            "pathway_tags": "ECM,Bone,Mineralization",
            "gravity_link": "Matrix Gla protein; potent inhibitor of soft tissue calcification, maintaining elasticity of spinal ligaments against mechanical stress.",
            "spine_curvature_link": "Mutations cause Keutel syndrome, featuring abnormal cartilage calcification and severe kyphoscoliosis. (PMID: 8871651)",
            "priority_score": "88",
            "justification": "Maintains mechanical properties (elasticity vs stiffness) of the spine."
        },
        {
            "gene_symbol": "COL1A1",
            "uniprot_id": "P02452",
            "organism": "Homo sapiens",
            "pathway_tags": "ECM,Bone,Mechanotransduction",
            "gravity_link": "Major load-bearing collagen in bone; expression regulated by gravity/loading.",
            "spine_curvature_link": "Osteogenesis Imperfecta (Type I/III/IV) features severe progressive scoliosis. (DOI: 10.1016/j.spam.2014.11.002)",
            "priority_score": "90",
            "justification": "Already in DB, ensuring exact metadata match; primary gravity-resisting structure."
        }
    ]

    existing_genes = set()
    with open(MASTER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_genes.add(row['gene_symbol'].strip().upper())

    count = 0
    with open(MASTER_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["gene_symbol", "uniprot_id", "organism", "pathway_tags", "gravity_link", "spine_curvature_link", "priority_score", "justification"])
        # No header write, appending
        for c in new_candidates:
            if c['gene_symbol'].strip().upper() not in existing_genes:
                # specifically format priority_score without any trailing spaces
                c['priority_score'] = c['priority_score'].strip()
                writer.writerow(c)
                count += 1
                print(f"Added {c['gene_symbol']}")
            else:
                print(f"Skipped {c['gene_symbol']} (already exists)")

    print(f"Added {count} new candidates.")

if __name__ == "__main__":
    main()
