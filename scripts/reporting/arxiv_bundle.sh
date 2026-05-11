#!/usr/bin/env bash
set -euo pipefail

# Define output bundle name
OUT="dist/arxiv_bundle_$(date +%Y%m%d).tar.gz"
mkdir -p dist

# Create a temporary directory for bundling
BUNDLE_DIR="dist/bundle_tmp"
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"

echo "Preparing bundle in $BUNDLE_DIR..."

# 1. Copy Manuscript Source
# -------------------------
echo "Copying manuscript source..."
cp manuscript/main.tex "$BUNDLE_DIR/"
cp manuscript/references.bib "$BUNDLE_DIR/"
cp -r manuscript/sections "$BUNDLE_DIR/"

# 2. Copy Figures
# ---------------
echo "Copying figures..."
# Create figures directory in bundle
mkdir -p "$BUNDLE_DIR/figures"

# Copy figures referenced in manuscript/figures/
# (e.g., fig_gene_to_geometry.pdf, fig_scoliosis_emergence.png)
if [ -d "manuscript/figures" ]; then
    cp -r manuscript/figures/* "$BUNDLE_DIR/figures/"
fi

# Copy figures located in manuscript root
# (e.g., fig_countercurvature_panelA.pdf)
# We copy them to root of bundle to match current location,
# or to figures/ if we want to consolidate?
# LaTeX graphicspath is set to {figures/}.
# If we put them in root, LaTeX usually finds them in ./ as well.
# To be safe and clean, let's keep them in root as they are in the source repo relative to main.tex,
# UNLESS main.tex expects them in figures/.
# main.tex has \graphicspath{{figures/}}. It does NOT explicitly exclude ./
# However, `fig_countercurvature_panelA.pdf` is currently in `manuscript/` (root relative to main.tex).
# If the build works now, it's because they are in ./
# So we should copy them to ./ in the bundle.
cp manuscript/*.pdf "$BUNDLE_DIR/" 2>/dev/null || true

# 3. Copy Root README
# -------------------
echo "Copying root README..."
cp README.md "$BUNDLE_DIR/"

# 4. Cleanups / Exclusions
# ------------------------
# Ensure no READMEs in subdirectories (e.g. if we copied a dir that has one)
# manuscript/sections contains only .tex (verified)
# manuscript/figures contains only images (verified)
# Just in case:
find "$BUNDLE_DIR" -name "README.md" -not -path "$BUNDLE_DIR/README.md" -delete

# Ensure no Makefiles
find "$BUNDLE_DIR" -name "Makefile" -delete

# Ensure no Python scripts
find "$BUNDLE_DIR" -name "*.py" -delete

# 5. Create Archive
# -----------------
echo "Creating archive $OUT..."
tar -C "$BUNDLE_DIR" -czf "$OUT" .

# Cleanup
rm -rf "$BUNDLE_DIR"

echo "Done. Bundle ready at $OUT"
