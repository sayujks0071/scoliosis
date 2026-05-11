#!/bin/bash
export GEMINI_API_KEY="dummy"
export PATH="/home/jules/self_created_tools/bin:$PATH"

mkdir -p research/figures/

paperbanana generate --input jules_mechanism_derivative_gain_trap.txt --caption 'Derivative Gain Trap' --output research/figures/jules_autonomous_mechanism_derivative_gain_trap.png
paperbanana plot --data outputs/thermodynamic_cost/phase_diagram_energy_deficit_for_plot.csv --x L --y chi_kappa --color R_deficit --output research/figures/jules_autonomous_thermodynamic_phase_diagram.png --intent 'Phase Diagram Energy Deficit'
paperbanana generate --input jules_visual_abstract_metabolic_buckling.txt --caption 'Visual Abstract: Metabolic Buckling' --output research/figures/jules_autonomous_visual_abstract_metabolic_buckling.png
