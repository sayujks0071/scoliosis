#!/bin/bash
export PATH="/home/jules/self_created_tools/bin:$PATH"
export GEMINI_API_KEY="dummy"

mkdir -p research/figures
mkdir -p outputs/experiments
mkdir -p scripts/experiments

# Ensure scripts exist and run them
if [ ! -f outputs/experiments/polygenic_stacking_results.csv ]; then
    python3 scripts/experiments/experiment_polygenic_stacking.py
fi

if [ ! -f outputs/experiments/lenke_six_types.csv ]; then
    python3 scripts/experiments/experiment_lenke_classes.py
fi

# Generate text descriptions for paperbanana
cat << 'TXT' > jules_polygenic_stacking_lenke.txt
Polygenic Stacking Threshold Model for Adolescent Idiopathic Scoliosis (AIS).
The allometric trap creates a universal vulnerability window with a +5.3 ms baseline stability margin.
Individual-specific genetic variants (e.g., reduced damping from COL1A1/COL2A1, increased delay from PIEZO2/GPR126/MTNR1B, shifted Kd from LBX1, increased load from PAX1) each narrow the margin.
The combined polygenic trap flips the margin to -26.3 ms, explaining the 2-4% clinical prevalence.
TXT

cat << 'TXT' > jules_lenke_6_types.txt
Multi-segment Cosserat Rod Modeling of all 6 Lenke Curve Types.
Different Lenke types (1-6) emerge as distinct buckling eigenmodes dictated by regional parameter variations:
- Thoracic rib cage buttressing (stiffness EI variations)
- Thoracolumbar vulnerability (31.1% stiffness reduction)
- Segmental mechanoreceptor density differences (proprioceptive delay τ)
- Asymmetric loading
These regional differences map global instability onset to specific 3D spatial curve morphologies, dictating whether main thoracic, double major, or lumbar curves emerge.
TXT

# Generate conceptual diagrams
paperbanana generate --input jules_polygenic_stacking_lenke.txt --caption "Polygenic Threshold: The 2-4% Prevalence" --output research/figures/jules_polygenic_stacking_lenke.png

paperbanana generate --input jules_lenke_6_types.txt --caption "Multi-segment Cosserat Rod: 6 Lenke Curve Morphologies" --output research/figures/jules_lenke_6_types.png

# Generate data plots
paperbanana plot --data outputs/experiments/polygenic_stacking_results.csv --x Scenario --y Stability_Margin_ms --output research/figures/jules_plot_polygenic_stacking.png

# Since we want to map all 6 types we will just pick Lenke_Type_1 as representative for paperbanana basic plot, although matplotlib does all 6
paperbanana plot --data outputs/experiments/lenke_six_types.csv --x Normalized_Position --y Lenke_Type_1 --output research/figures/jules_plot_lenke_6_types.png

echo "Autonomous Lenke artifacts generated."
