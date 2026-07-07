# tests/test_runner.py
"""
test_runner.py

Test file for the fungal BLAST pipeline.
This runs the same logic as the CLI `main()` from runner.py
but allows easier programmatic testing.
"""

import argparse
from pathlib import Path
from src.fungi_pipeline.blast.runner import FungalBlastPipeline

from src.fungi_pipeline.config import PIPELINE_RESULTS_DIR, PIPELINE_QUERIES_DIR, FINAL_EXTRACTED_FASTAS_DIR


def main():
    parser = argparse.ArgumentParser(description="Run fungal BLAST pipeline.")
    parser.add_argument("--query_fasta_dir", default=str(PIPELINE_QUERIES_DIR), help="Directory containing query FASTA files.")
    parser.add_argument("--proteome_dir", default=str(FINAL_EXTRACTED_FASTAS_DIR), help="Directory containing fungal proteome FASTA files.")
    parser.add_argument("--output_dir", default=str(PIPELINE_RESULTS_DIR / "test_run"), help="Directory to store outputs.")
    parser.add_argument("--identity_threshold", type=float, default=35.0, help="Minimum identity % to include result.")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads for BLASTp.")
    # BUG FIX: Swapped action="store_false" to action="store_true" to align with execution engine defaults
    parser.add_argument("--duplicates", action="store_true", help="Keep duplicates (default: keep best hit only)")
    parser.add_argument("--csv_out", type=str, default="blast_results.csv", help="Output CSV file name.")
    args = parser.parse_args()

    pipeline = FungalBlastPipeline(
        query_fasta_dir=args.query_fasta_dir,
        proteome_dir=args.proteome_dir,
        output_dir=args.output_dir,
        identity_threshold=args.identity_threshold,
        threads=args.threads,
    )
    pipeline.run(duplicates=args.duplicates)


if __name__ == "__main__":
    main()