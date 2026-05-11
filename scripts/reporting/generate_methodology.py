"""
Generate methodology diagram and description for the Spinal Modes project.
"""

import asyncio
import os
from pathlib import Path

from paperbanana import DiagramType, GenerationInput, PaperBananaPipeline
from paperbanana.core.config import Settings


async def main():
    # Load source context
    repo_root = Path(__file__).parent.parent.parent
    readme_path = repo_root / "README.md"
    iec_path = repo_root / "src/spinalmodes/iec.py"

    source_context = ""
    if readme_path.exists():
        source_context += f"# README\n\n{readme_path.read_text()}\n\n"
    if iec_path.exists():
        source_context += f"# src/spinalmodes/iec.py\n\n{iec_path.read_text()}\n\n"

    if not source_context:
        print("Error: Could not find README.md or src/spinalmodes/iec.py")
        return

    print(f"Loaded source context ({len(source_context)} chars)")

    # Configure settings
    # Ensure GOOGLE_API_KEY is set in environment (from gemini_api_key)
    api_key = os.environ.get("gemini_api_key")
    if not api_key:
        print("Error: gemini_api_key environment variable not set")
        return

    os.environ["GOOGLE_API_KEY"] = api_key

    # Initialize pipeline
    print("Initializing PaperBanana pipeline...")
    settings = Settings(
        google_api_key=api_key,
        output_dir="outputs/methodology",
        save_iterations=True
    )
    pipeline = PaperBananaPipeline(settings=settings)

    # Define generation input
    input_data = GenerationInput(
        source_context=source_context,
        communicative_intent="Illustrate the Information-Elasticity Coupling (IEC) framework for spinal geometry, showing how developmental information modifies mechanical properties (stiffness, target curvature) to counter gravity.",
        diagram_type=DiagramType.METHODOLOGY
    )

    # Run generation
    print("Starting generation...")
    output = await pipeline.generate(input_data)

    # Save results to target locations
    figures_dir = repo_root / "figures"
    figures_dir.mkdir(exist_ok=True)

    manuscript_dir = repo_root / "manuscript"
    manuscript_dir.mkdir(exist_ok=True)

    # Copy image
    output_image_path = Path(output.image_path)
    target_image_path = figures_dir / "generated_methodology.png"
    if output_image_path.exists():
        import shutil
        shutil.copy2(output_image_path, target_image_path)
        print(f"Saved methodology diagram to {target_image_path}")

    # Save description
    target_desc_path = manuscript_dir / "generated_methodology.txt"
    target_desc_path.write_text(output.description)
    print(f"Saved methodology description to {target_desc_path}")

if __name__ == "__main__":
    asyncio.run(main())
