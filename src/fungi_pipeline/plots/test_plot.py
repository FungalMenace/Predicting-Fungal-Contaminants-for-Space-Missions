"""
Test script for generating visual plots from the Excel summary
created by `make_summary_excel.py`.
"""

import argparse
import pandas as pd
from src.fungi_pipeline.plots.plots_old import (
    PROTEIN_CATEGORY,
    flatten_multilevel_columns,
    plot_category,
    plot_a_scores,
    plot_s_scores,
    plot_category_counts,
)

from src.fungi_pipeline.config import SUMMARY_EXCEL_PATH


def main():
    parser = argparse.ArgumentParser(description="Generate visual plots from BLAST Excel summary.")
    # Expose the central configuration file path cleanly stringified for argument validation
    parser.add_argument("--input_excel", default=str(SUMMARY_EXCEL_PATH), help="Path to Excel file")
    parser.add_argument("--plot", default="all",
                        help="Plot type: AMR | a_score | s_score | category_counts | all")
    args = parser.parse_args()

    # Load Excel
    df = pd.read_excel(args.input_excel, sheet_name="BLAST Summary", header=[0, 1, 2, 3])
    df = flatten_multilevel_columns(df)
    df.rename(columns={df.columns[0]: 'Organism', df.columns[1]: 'A-score'}, inplace=True)

    # Determine which plot(s) to generate (plots.py defaults handle PLOTS_EXPORT_DIR)
    if args.plot.lower() == "all":
        for cat in PROTEIN_CATEGORY.keys():
            plot_category(df, cat)
        plot_a_scores(df)
        plot_s_scores(df)
        plot_category_counts(df)
    elif args.plot.upper() in PROTEIN_CATEGORY:
        plot_category(df, args.plot.upper())
    elif args.plot.lower() == "a_score":
        plot_a_scores(df)
    elif args.plot.lower() == "s_score":
        plot_s_scores(df)
    elif args.plot.lower() == "category_counts":
        plot_category_counts(df)
    else:
        print(f"Unknown plot type: {args.plot}")


if __name__ == "__main__":
    main()