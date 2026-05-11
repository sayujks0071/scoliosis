"""
AlphaFold EBI API Client CLI

Usage:
    python -m src.alphafold.main prediction <uniprot_id>
    python -m src.alphafold.main summary <uniprot_id>
    python -m src.alphafold.main annotations <uniprot_id> [--type MUTAGEN]
"""

import argparse
import sys

from .ebi_client import AlphaFoldEbiClient


def main():
    parser = argparse.ArgumentParser(description="AlphaFold EBI API Client CLI")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Prediction command
    pred_parser = subparsers.add_parser("prediction", help="Get predictions for a UniProt ID")
    pred_parser.add_argument("uniprot_id", help="UniProt Accession (e.g., P04637)")

    # Summary command
    sum_parser = subparsers.add_parser("summary", help="Get summary for a UniProt ID")
    sum_parser.add_argument("uniprot_id", help="UniProt Accession (e.g., P04637)")

    # Annotation command
    ann_parser = subparsers.add_parser("annotations", help="Get annotations for a UniProt ID")
    ann_parser.add_argument("uniprot_id", help="UniProt Accession (e.g., P04637)")
    ann_parser.add_argument("--type", default="MUTAGEN", help="Annotation type (default: MUTAGEN)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = AlphaFoldEbiClient()

    try:
        if args.command == "prediction":
            print(f"Fetching predictions for {args.uniprot_id}...")
            results = client.get_predictions(args.uniprot_id)
            if not results:
                print("No predictions found.")
            else:
                print(f"Found {len(results)} predictions.")
                for i, pred in enumerate(results):
                    print(f"\n--- Prediction {i+1} ---")
                    # Dump model to json for pretty printing
                    print(pred.model_dump_json(indent=2))

        elif args.command == "summary":
            print(f"Fetching summary for {args.uniprot_id}...")
            result = client.get_summary(args.uniprot_id)
            if not result:
                print("No summary found.")
            else:
                print(result.model_dump_json(indent=2))

        elif args.command == "annotations":
            print(f"Fetching annotations for {args.uniprot_id} (type={args.type})...")
            result = client.get_annotations(args.uniprot_id, type_param=args.type)
            if not result:
                print("No annotations found (404).")
            else:
                print(result.model_dump_json(indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
