# src/fungi_pipeline/pipeline.py
"""
Unified pipeline for fungal proteome analysis.
"""

import argparse
import os
from pathlib import Path
import pandas as pd

from src.fungi_pipeline.fastas.extract_fastas import ExtractionConfig, UniProtFetcher
from src.fungi_pipeline.blast.runner import FungalBlastPipeline
from src.fungi_pipeline.excel.make_excel import read_blast_results, generate_excel
from src.fungi_pipeline.excel.phyla import get_phylum
from src.fungi_pipeline.plots.plots_old import (
    flatten_multilevel_columns,
    plot_category,
    plot_a_scores,
    plot_s_scores,
    plot_category_counts,
    PROTEIN_CATEGORY,
)
from src.fungi_pipeline.plots.plots import ( 
    ensure_plots_dir,
    prepare_plot_data,
    compute_s_scores,
    _combined_counts,
    plot_a_score_color, plot_s_scores_color, plot_category_counts_color,
    plot_combined_counts_color, plot_combined_counts_color_log,
    plot_a_score_bw, plot_s_scores_bw,
    plot_combined_counts_bw_log, plot_combined_counts_bw,
)

from src.fungi_pipeline.config import ROOT_DIR, PIPELINE_RESULTS_DIR, PIPELINE_QUERIES_DIR, SUMMARY_EXCEL_PATH, PLOTS_EXPORT_DIR


class PipelineManager:
    def __init__(self, args):
        self.args = args
        self.base_dir = Path(args.base_dir) if args.base_dir else ROOT_DIR
        
        # Route directory configurations dynamically through the central architecture layout
        self.results_dir = PIPELINE_RESULTS_DIR
        self.fastas_dir = self.base_dir / "src" / "fastas" / f"{args.proteomes_dir}"
        self.excel_file = Path(args.excel or SUMMARY_EXCEL_PATH)
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
        query_dir = PIPELINE_QUERIES_DIR
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
        print("\n[Step 4] Generating plots from existing Excel summary...")

        # Read Excel using row 2 as the column names
        df = pd.read_excel(self.excel_file, header=1)

        # Remove the two metadata rows (Genus and Species)
        df = df.iloc[2:].copy()

        # Find where "Summary Statistics" begins
        summary_idx = df[df.iloc[:, 0] == "Summary Statistics"].index

        if len(summary_idx) > 0:
            df = df.loc[:summary_idx[0] - 1]

        # Rename first two columns
        df.rename(
            columns={
                df.columns[0]: "Organism",
                df.columns[1]: "A-score",
            },
            inplace=True,
        )

        df.reset_index(drop=True, inplace=True)
        df["A-score"] = pd.to_numeric(df["A-score"], errors="coerce")

        # --- output sub-folders ---
        plots_root = Path(PLOTS_EXPORT_DIR)
        color_dir = plots_root / "color"
        bw_dir = plots_root / "black and white"
        ensure_plots_dir(color_dir)
        ensure_plots_dir(bw_dir)

        # --- compute shared structures once ---
        protein_cols, colors_df, protein_category, red_rows, yellow_rows = \
            prepare_plot_data(df)
        print(df.shape)
        print(df.columns.tolist())
        print(protein_cols)
        s35, s75 = compute_s_scores(df, colors_df, protein_category)
        categories = sorted(set(protein_category.values()))
        red_counts, yellow_counts = _combined_counts(
            colors_df, protein_category, red_rows, yellow_rows, categories)

        # --- COLOR ---
        plot_a_score_color(df, color_dir)
        plot_s_scores_color(s35, s75, color_dir)
        plot_category_counts_color(df, protein_cols, protein_category, color_dir)
        plot_combined_counts_color(red_counts, yellow_counts, categories, color_dir)
        plot_combined_counts_color_log(red_counts, yellow_counts, categories, color_dir)

        # --- BLACK & WHITE ---
        plot_a_score_bw(df, bw_dir)
        plot_s_scores_bw(s35, s75, bw_dir)
        plot_combined_counts_bw_log(red_counts, yellow_counts, categories, bw_dir)
        plot_combined_counts_bw(red_counts, yellow_counts, categories, bw_dir)

        print(f"All plots generated and saved to:\n  {color_dir}\n  {bw_dir}\n")




def main():
    parser = argparse.ArgumentParser(description="Full modular fungal analysis pipeline.")
    parser.add_argument("--base_dir", default=str(ROOT_DIR), help="Base directory for inputs/outputs.")
    parser.add_argument("--orgs", default="sample_data.txt", help="File with list of organisms to process.")
    parser.add_argument("--excel", default=None, help="Existing Excel file to use (if skipping earlier steps).")
    parser.add_argument("--steps", default="1,4", help="Comma-separated range of steps to run, e.g. 1,3 or 2,4.")
    parser.add_argument("--proteomes_dir", default="extracted_fastas", help="Directory for proteome FASTA files.")

    args = parser.parse_args()

    try:
        start, end = map(int, args.steps.split(","))
    except ValueError:
        raise ValueError("Invalid format for --steps. Use comma-separated integers, e.g. 1,3")

    pm = PipelineManager(args)

    print("\nStarting Fungal Proteome Analysis Pipeline")
    print(f"Running steps {start} → {end}")
    print("------------------------------------------------------------")
    existing_excel = False
    if args.excel and Path(args.excel).exists():
        existing_excel = True
        print(f"Using existing Excel file: {args.excel}")

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