#!/bin/bash
# Autonomous generation of high-impact visuals for Biological Countercurvature theory

echo "=== Running Autonomous Paperbanana Generation ==="

# 1. Mechanism Diagram (Information-Elasticity Coupling)
paperbanana generate --input research/figures/jules_autonomous_iec_mechanism.txt --caption 'Information-Elasticity Coupling Mechanism' --output research/figures/jules_autonomous_iec_mechanism.png

# 2. Key Result Plot (Thermodynamic Phase Diagram)
paperbanana plot --data outputs/thermodynamic_cost/phase_diagram_energy_deficit_for_plot.csv --intent "Plot a heatmap mapping L (Spinal Length) to the X-axis, chi_kappa (Coupling Strength) to the Y-axis, and R_deficit (Energy Deficit Ratio) as the color intensity. Use the viridis colormap. Add appropriate scientific labels and a title. Use default fonts." --output research/figures/jules_autonomous_phase_diagram.png

# 3. Visual Abstract (Biological Countercurvature of Spacetime)
paperbanana generate --input research/figures/jules_autonomous_bcs_abstract.txt --caption 'Visual Abstract: Biological Countercurvature' --output research/figures/jules_autonomous_bcs_abstract.png

echo "Generation complete."
