import os
import re


def combine_sections():
    print("Combining sections for Nature manuscript...")

    # Target directory
    out_dir = "submission_package"
    os.makedirs(out_dir, exist_ok=True)

    # 1. Abstract (must be exactly 150 words)
    # The current Nature abstract: "Living systems routinely maintain structure against gravity..."
    abstract_text = r"""\textbf{Living systems routinely maintain structure against gravity, yet the physical cost of this victory remains unquantified. Here we show that Adolescent Idiopathic Scoliosis (AIS)—a deformity affecting 3\% of children—is a "Metabolic Buckling" event caused by a mismatch between the scaling laws of mechanical demand and metabolic supply. We model the spine as a "Thermodynamic Standing Wave," a dissipative structure requiring continuous energy to maintain its S-shape against gravity. Using a Cosserat rod model coupled to a developmental information field, we identify a critical "Energy Deficit Window" at spinal lengths $L > 0.35$m where the thermodynamic cost of straightness ($L^4$) exceeds metabolic capacity ($L^2$). Structural analysis reveals that key mechanosensors (e.g., PIEZO2, anisotropy 4.44) are thermodynamically expensive to maintain. Our simulations demonstrate that this high anisotropy accelerates instability, while reducing sensor anisotropy ($A \to 2.4$) delays buckling. These results suggest that scoliosis is a survival response to an unaffordable "Anisotropy Tax," and that targeting cytoskeletal stiffness may offer a non-surgical rescue strategy.}"""

    # Let's count words in the abstract roughly
    words = re.findall(r'\b\w+\b', abstract_text)
    print(f"Abstract word count: {len(words)}") # Need to get it to ~150.

    # Current main text sections:
    # 1. Introduction
    # 2. Theory
    # 3. Results
    # 4. Discussion (with preemptive rebuttal)

    with open("manuscript/sections/introduction.tex", "r") as f:
        intro = f.read()
    with open("manuscript/sections/theory.tex", "r") as f:
        theory = f.read()
    with open("manuscript/sections/results.tex", "r") as f:
        results = f.read()
    with open("manuscript/sections/discussion.tex", "r") as f:
        discussion = f.read()
    with open("manuscript/sections/methods.tex", "r") as f:
        methods = f.read()

    # Remove \section{}, \subsection{}, \subsubsection{} from main text
    def remove_headings(text):
        text = re.sub(r'\\section\*?\{[^}]+\}', '', text)
        text = re.sub(r'\\subsection\*?\{[^}]+\}', '', text)
        text = re.sub(r'\\subsubsection\*?\{[^}]+\}', '', text)
        # also remove empty lines left behind
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        return text.strip()

    main_text = intro + "\n\n" + theory + "\n\n" + results + "\n\n" + discussion
    main_text = remove_headings(main_text)

    # Inject preemptive rebuttal into discussion
    rebuttal = "While direct metabolic flux measurements in the growing human spine are currently invasive, the allometric scaling laws ($L^4$ vs $L^2$) provide a robust theoretical bound on energy availability that aligns with the observed clinical window of deformity. The specific molecular candidates identified (e.g., Vimentin) are functional nodes in the control loop, and their failure modes match the predicted instability."

    if "While direct metabolic flux measurements" not in main_text:
        main_text += "\n\n" + rebuttal

    # We show that... (Declarative tone check - already mostly declarative in the text, but let's just make sure it flows).

    # Methods (Keep as separate section at the end)
    # The Methods section in Nature CAN have subheadings.
    methods_text = r"\section*{Methods}" + "\n" + methods

    # Build full tex
    full_tex = f"""\\documentclass[11pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{geometry}}
\\geometry{{a4paper, margin=1in}}
\\usepackage{{graphicx}}
\\usepackage{{amsmath, amssymb, bm}}
\\usepackage{{lineno}}
\\usepackage{{setspace}}
\\usepackage[superscript,biblabel]{{cite}}

\\title{{Metabolic buckling of the growing spine}}

\\author{{Sayuj Krishnan S., MBBS, DNB (Neurosurgery) \\\\
\\textit{{Yashoda Hospitals, Hyderabad, India}} \\\\
Correspondence: hellodr@drsayuj.info}}

\\date{{}}

\\begin{{document}}
\\linenumbers
\\maketitle

{abstract_text}

\\vspace{{1em}}

{main_text}

{methods_text}

\\input{{tables}}

\\bibliography{{references}}
\\bibliographystyle{{naturemag}}

\\end{{document}}
"""

    with open(os.path.join(out_dir, "submission_manuscript.tex"), "w") as f:
        f.write(full_tex)

    print(f"Generated {os.path.join(out_dir, 'submission_manuscript.tex')}")

if __name__ == "__main__":
    combine_sections()
