#!/bin/bash
set -e

# Setup environment for AlphaFold Counter-Curvature Pipeline

echo "🧬 Setting up AlphaFold Counter-Curvature Pipeline..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required."
    exit 1
fi

# Create venv if not exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 Installing dependencies..."

# Create requirements.txt if not exists
REQ_FILE="research/alphafold_countercurvature/requirements.txt"
if [ ! -f "$REQ_FILE" ]; then
    echo "Creating $REQ_FILE..."
    cat <<EOF > "$REQ_FILE"
numpy>=1.24.0
pandas>=2.0.0
biopython>=1.85
pyyaml>=6.0
matplotlib>=3.7.0
seaborn>=0.13.0
EOF
fi

pip install -r "$REQ_FILE"

echo "✅ Setup complete. To activate: source .venv/bin/activate"
