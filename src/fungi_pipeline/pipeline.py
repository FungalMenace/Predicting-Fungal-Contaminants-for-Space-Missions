"""
Unified pipeline for fungal proteome analysis.

Modules integrated:
  1. FASTA Extraction (extract_fastas.py)
  2. BLAST Execution (blast.runner)
  3. Excel Summary Creation (make_excel.py)
  4. Plot Generation (plot_summary.py)
"""

import argparse
import os
from pathlib import Path
from src.fungi_pipeline.fastas.extract_fastas import ExtractionConfig, UniProtFetcher
from src.fungi_pipeline.blast.runner import FungalBlastPipeline
from src.fungi_pipeline.excel.make_excel import read_blast_results, generate_excel
from src.fungi_pipeline.excel.phyla import get_phylum
from src.fungi_pipeline.plots.plots import (
    flatten_multilevel_columns,
    plot_category,
    plot_a_scores,
    plot_s_scores,
    plot_category_counts,
    PROTEIN_CATEGORY,
)
import pandas as pd


class PipelineManager:
    def __init__(self, args):
        self.args = args
        self.base_dir = Path(args.base_dir)
        self.results_dir = self.base_dir / "src" / "results"
        self.fastas_dir = self.base_dir / "src" / "fastas" / f"{args.proteomes_dir}"
        self.excel_file = Path(args.excel or (self.results_dir / "fungal_summary.xlsx"))
        self.proteomes_dir = self.base_dir / "proteomes"

        self.results_dir.mkdir(exist_ok=True, parents=True)
        self.fastas_dir.mkdir(exist_ok=True, parents=True)

    def extract_fastas(self, orgs_file):
        print("\n[Step 1] Extracting FASTAs from UniProt...")
        species_file = self.base_dir / "src" / orgs_file
        if not species_file.exists():
            raise FileNotFoundError(f"Species list not found: {species_file}")
        with open(species_file, "r") as f:
            organisms = [line.strip() for line in f if line.strip()]

        print(f"  Found {len(organisms)} organisms to process.")
        cfg = ExtractionConfig(output_dir=self.fastas_dir, reviewed_only=False)
        fetcher = UniProtFetcher(cfg)
        fetcher.fetch_proteomes(organisms)
        print("FASTA extraction complete.\n")

    def run_blast(self):
        print("\n[Step 2] Running BLAST pipeline...")
        query_dir = self.base_dir / "data" / "proteomes" / "queries"
        output_dir = self.results_dir
        pipeline = FungalBlastPipeline(
            query_fasta_dir=query_dir,
            proteome_dir=self.fastas_dir,
            output_dir=output_dir,
            identity_threshold=35.0,
            threads=4,
        )
        results = pipeline.run(duplicates=False)
        pipeline.save_results(results, output_dir / "blast_results.csv")
        print("BLAST completed. Results saved to:", output_dir / "blast_results.csv")

    def create_excel(self):
        print("\n[Step 3] Creating Excel summary from BLAST results...")
        data, organisms, prots = read_blast_results(self.results_dir)
        generate_excel(data, organisms, prots, self.excel_file)
        print(f"Excel summary created at: {self.excel_file}")

    def generate_plots(self):
        print("\n[Step 4] Generating plots from Excel summary...")
        df = pd.read_excel(self.excel_file)
        df.columns = df.iloc[0]
        df = df.iloc[1:-11]
        df.rename(columns={df.columns[0]: "Organism", df.columns[1]: "A-score"}, inplace=True)

        for cat in PROTEIN_CATEGORY.keys():
            plot_category(df, cat)
        plot_a_scores(df)
        plot_s_scores(df)
        plot_category_counts(df)
        print("All plots generated and saved to the /plots folder.\n")


def main():
    parser = argparse.ArgumentParser(description="Full modular fungal analysis pipeline.")
    parser.add_argument("--base_dir", default=f"{os.getcwd()}", help="Base directory for inputs/outputs.")
    parser.add_argument("--orgs", default="sample_data.txt", help="File with list of organisms to process.")
    parser.add_argument("--excel", default=None, help="Existing Excel file to use (if skipping earlier steps).")
    parser.add_argument("--steps", default="1,4", help="Comma-separated range of steps to run, e.g. 1,3 or 2,4.")
    parser.add_argument("--proteomes_dir", default="extracted_fastas", help="Directory for proteome FASTA files.")

    args = parser.parse_args()

    # Parse steps argument into integers
    try:
        start, end = map(int, args.steps.split(","))
    except ValueError:
        raise ValueError("Invalid format for --steps. Use comma-separated integers, e.g. 1,3")

    pm = PipelineManager(args)

    print("\nStarting Fungal Proteome Analysis Pipeline")
    print(f"Running steps {start} → {end}")
    print("------------------------------------------------------------")

    if start <= 1 <= end:
        pm.extract_fastas(args.orgs)
    if start <= 2 <= end:
        pm.run_blast()
    if start <= 3 <= end:
        pm.create_excel()
    if start <= 4 <= end:
        pm.generate_plots()

    print("Pipeline execution complete! All selected steps finished successfully.\n")


if __name__ == "__main__":
    main()
