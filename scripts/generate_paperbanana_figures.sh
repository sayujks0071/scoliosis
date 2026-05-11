#!/usr/bin/env bash

# generate_paperbanana_figures.sh
#
# Helper script to generate conceptual and methodology diagrams using paperbanana.
# Note: Ensure you have your Gemini API key set and paperbanana installed.
#
# Usage:
#   export GEMINI_API_KEY="your-api-key"
#   ./scripts/generate_paperbanana_figures.sh

set -e

echo "=== Generating High-Impact Visual Artifacts with PaperBanana ==="

if [[ -z "${GEMINI_API_KEY}" ]]; then
    echo "Error: GEMINI_API_KEY is not set."
    echo "Please set it via: export GEMINI_API_KEY='your-api-key'"
    exit 1
fi

# Generate: The Anisotropic Supply Hypothesis Mechanism
echo "[1/2] Generating Anisotropic Supply Mechanism diagram..."
paperbanana generate \
    --input research/figures/anisotropic_supply_mechanism.txt \
    --caption "Anisotropic Supply Hypothesis Mechanism" \
    --output research/figures/anisotropic_supply_mechanism.png

# Generate: Visual Abstract (Rindler-Cosserat Framework)
echo "[2/2] Generating Rindler-Cosserat Visual Abstract..."
paperbanana generate \
    --input research/figures/rindler_cosserat_abstract.txt \
    --caption "Visual Abstract: Rindler-Cosserat framework" \
    --output research/figures/rindler_cosserat_abstract.png

echo "Done! The new figures have been saved to research/figures/"
