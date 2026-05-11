#!/bin/bash
# Documentation of exact paperbanana CLI commands for final artifacts
# 1. Complex Mechanism Diagram: The Mechanogenetic Demand-Supply Gap
paperbanana generate --input research/figures/new_mechanism_demand_supply.txt --caption 'Mechanogenetic Demand-Supply Gap' --output research/figures/new_mechanism_demand_supply.png

# 2. Key Result Plot: Thermodynamic Stability Phase Diagram
paperbanana plot --data outputs/thermodynamic_cost/phase_diagram_energy_deficit_for_plot.csv --intent 'Plot a heatmap mapping L (Spinal Length) to the X-axis, chi_kappa (Coupling Strength) to the Y-axis, and R_deficit (Energy Deficit Ratio) as the color intensity. Use the viridis colormap and draw a red dashed line at the R=1 instability limit. Use default fonts.' --output research/figures/new_thermodynamic_phase_diagram.png

# 3. Visual Abstract Diagram: Biological Countercurvature of Spacetime
paperbanana generate --input research/figures/new_visual_abstract.txt --caption 'Visual Abstract: Biological Countercurvature' --output research/figures/new_visual_abstract.png
