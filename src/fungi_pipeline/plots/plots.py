"""
Generates summary visualizations for BLAST Excel output from make_summary_excel.py.

Includes:
  1. Category bar plots (e.g., AMR)
  2. A-score histogram + yellow/red fractions
  3. S-score histograms
  4. Organisms-per-category plot
"""

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
from src.fungi_pipeline.excel.make_excel import PROTEIN_CATEGORY

from src.fungi_pipeline.config import PLOTS_EXPORT_DIR


def ensure_plots_dir(save_path):
    Path(save_path).mkdir(parents=True, exist_ok=True)


def flatten_multilevel_columns(df):
    """Flatten multi-index Excel columns into single names."""
    new_cols = []
    for col in df.columns:
        if isinstance(col, tuple):
            parts = [str(c) for c in col if pd.notna(c)]
            new_cols.append("_".join(parts))
        else:
            new_cols.append(str(col))
    df.columns = new_cols
    return df


def cell_color(val):
    """Return color category for identity value."""
    if val is None or pd.isna(val) or ',' in str(val):
        return 'blue'
    val = float(val)
    if val > 75:
        return 'red'
    elif val > 35:
        return 'yellow'
    else:
        return 'blue'


def plot_category(df, category, threshold_high=75, threshold_low=35, save_path=PLOTS_EXPORT_DIR):
    """Bar plot showing how many organisms exceed thresholds per protein."""
    save_path = Path(save_path)
    ensure_plots_dir(save_path)

    if category not in PROTEIN_CATEGORY:
        print(f"Unknown category: {category}")
        return

    proteins_category = PROTEIN_CATEGORY[category]

    # Collect relevant protein columns
    protein_columns = df.columns[2:-2]
    cols_to_keep = ["Organism"]
    for col in protein_columns:
        abbr = col.split("-")[0]
        if abbr in proteins_category:
            cols_to_keep.append(col)

    if len(cols_to_keep) <= 1:
        print(f"No matching protein columns found for category '{category}'. Skipping plot.")
        return

    df_filtered = df[cols_to_keep].copy()
    protein_counts = {}

    # Count organisms with identities above thresholds
    for col in df_filtered.columns:
        if col == "Organism":
            continue
        try:
            high_count = (df_filtered[col].astype(float) >= threshold_high).sum()
            low_count = ((df_filtered[col].astype(float) >= threshold_low) &
                         (df_filtered[col].astype(float) < threshold_high)).sum()
            protein_counts[col.split("-")[0]] = (high_count, low_count)
        except Exception:
            protein_counts[col.split("-")[0]] = (0, 0)

    proteins = list(protein_counts.keys())
    high_counts = [protein_counts[p][0] for p in proteins]
    low_counts = [protein_counts[p][1] for p in proteins]

    # --- Plotting ---
    x = range(len(proteins))
    bar_width = 0.4
    plt.figure(figsize=(10, 6))

    bars_low = plt.bar([i - bar_width/2 for i in x], low_counts, width=bar_width,
                       label='35 ≤ I < 75', color='orange')
    bars_high = plt.bar([i + bar_width/2 for i in x], high_counts, width=bar_width,
                        label='I ≥ 75', color='red')

    plt.xticks(x, proteins, fontsize=13, rotation=45, ha='right')
    plt.yticks(fontsize=13)
    plt.xlabel('Proteins', fontsize=16)
    plt.ylabel('Number of Organisms', fontsize=16)
    plt.title(f"{category} Proteins", fontsize=18, fontweight='bold')
    plt.legend(loc="best")

    # --- Safe log scaling ---
    if any(v > 0 for v in high_counts + low_counts):
        plt.yscale('log')
    else:
        print(f"Skipping log scale for '{category}' — all counts are zero or missing data.")

    plt.tight_layout()

    # Add text labels on bars
    for bar in bars_low + bars_high:
        height = bar.get_height()
        if height > 0:
            plt.text(bar.get_x() + bar.get_width() / 2, height, str(int(height)),
                     ha='center', va='bottom', fontsize=11)

    out_file = save_path / f"{category}_barplot.png"
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    print(f"Saved {out_file}")
    plt.close()


def plot_a_scores(df, save_path=PLOTS_EXPORT_DIR):
    save_path = Path(save_path)
    ensure_plots_dir(save_path)
    print("Generating A-score and red/yellow fraction plots...")

    # Identify color per cell
    protein_cols = df.columns[2:-2].tolist()
    colors_df = df[protein_cols].map(cell_color)

    red_rows = colors_df.apply(lambda r: any(c == 'red' for c in r), axis=1)
    yellow_rows = colors_df.apply(lambda r: (not any(c == 'red' for c in r)) and any(c == 'yellow' for c in r), axis=1)

    # --- Histogram of A-scores ---
    plt.figure(figsize=(10, 6))
    plt.hist(df['A-score'], bins=range(0, 14), color='blue', alpha=0.7, edgecolor='black')
    plt.xlabel("A-score", fontsize=20)
    plt.ylabel("Number of Organisms", fontsize=20)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.grid(True, axis='y')
    plt.tight_layout()
    plt.savefig(save_path / "A-score.png", dpi=300)
    plt.close()

    # --- Red/yellow fraction per category ---
    protein_category = {}
    for col in protein_cols:
        abbr = col.split("-")[0]
        cat = None
        for c, prots in PROTEIN_CATEGORY.items():
            if abbr in prots:
                cat = c
                break
        if cat:
            protein_category[col] = cat

    red_frac = {}
    num_red_rows = red_rows.sum()
    for cat in set(protein_category.values()):
        cat_cols = [col for col, c in protein_category.items() if c == cat]
        subset = colors_df.loc[red_rows, cat_cols]
        count_with_red = subset.apply(lambda r: any(c == 'red' for c in r), axis=1).sum()
        red_frac[cat] = (count_with_red / num_red_rows) * 100 if num_red_rows > 0 else 0

    yellow_frac = {}
    num_yellow_rows = yellow_rows.sum()
    for cat in set(protein_category.values()):
        cat_cols = [col for col, c in protein_category.items() if c == cat]
        subset = colors_df.loc[yellow_rows, cat_cols]
        count_with_yellow = subset.apply(lambda r: any(c == 'yellow' for c in r), axis=1).sum()
        yellow_frac[cat] = (count_with_yellow / num_yellow_rows) * 100 if num_yellow_rows > 0 else 0

    categories = sorted(red_frac.keys())
    plt.figure(figsize=(12, 6))
    plt.bar(categories, [red_frac[c] for c in categories], color='red', alpha=0.7)
    plt.ylabel('% of Red Rows')
    plt.title('Percentage of Red Rows with ≥1 Red Protein in Category')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(save_path / "Red_rows_category_fraction.png", dpi=300)
    plt.close()

    plt.figure(figsize=(12, 6))
    plt.bar(categories, [yellow_frac[c] for c in categories], color='orange', alpha=0.7)
    plt.ylabel('% of Yellow Rows')
    plt.title('Percentage of Yellow Rows with ≥1 Yellow Protein in Category')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(save_path / "Yellow_rows_category_fraction.png", dpi=300)
    plt.close()


def plot_s_scores(df, save_path=PLOTS_EXPORT_DIR):
    save_path = Path(save_path)
    ensure_plots_dir(save_path)
    print("Generating S-score histograms...")

    protein_cols = df.columns[2:-2].tolist()
    colors_df = df[protein_cols].map(cell_color)
    protein_category = {}
    for col in protein_cols:
        abbr = col.split("-")[0]
        cat = None
        for c, prots in PROTEIN_CATEGORY.items():
            if abbr in prots:
                cat = c
                break
        if cat:
            protein_category[col] = cat

    s_scores_35, s_scores_75 = [], []
    for _, row in df.iterrows():
        s35 = 0
        s75 = 0
        for cat in set(protein_category.values()):
            cat_cols = [col for col, c in protein_category.items() if c == cat]
            subset = colors_df.loc[row.name, cat_cols]
            if any(c in ['red', 'yellow'] for c in subset):
                s35 += 1
            if any(c == 'red' for c in subset):
                s75 += 1
        s_scores_35.append(s35)
        s_scores_75.append(s75)

    plt.figure(figsize=(10, 6))
    plt.hist(s_scores_35, bins=np.arange(0, 9)-0.5, color='orange', edgecolor='black')
    plt.xlabel("S-score (≥35)", fontsize=18)
    plt.ylabel("Number of Organisms", fontsize=18)
    plt.grid(axis='y', alpha=0.7)
    plt.tight_layout()
    plt.savefig(save_path / "s-35.png", dpi=300)
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.hist(s_scores_75, bins=np.arange(0, 9)-0.5, color='red', edgecolor='black')
    plt.xlabel("S-score (≥75)", fontsize=18)
    plt.ylabel("Number of Organisms", fontsize=18)
    plt.grid(axis='y', alpha=0.7)
    plt.tight_layout()
    plt.savefig(save_path / "s-75.png", dpi=300)
    plt.close()


def plot_category_counts(df, save_path=PLOTS_EXPORT_DIR):
    save_path = Path(save_path)
    ensure_plots_dir(save_path)
    print("Generating combined orange/red organism count plot...")

    protein_cols = df.columns[2:-2].tolist()
    colors_df = df[protein_cols].map(cell_color)
    protein_category = {}
    for col in protein_cols:
        abbr = col.split("-")[0]
        cat = None
        for c, prots in PROTEIN_CATEGORY.items():
            if abbr in prots:
                cat = c
                break
        if cat:
            protein_category[col] = cat

    red_rows = colors_df.apply(lambda r: any(c == 'red' for c in r), axis=1)
    yellow_rows = colors_df.apply(lambda r: (not any(c == 'red' for c in r)) and any(c == 'yellow' for c in r), axis=1)

    categories = sorted(set(protein_category.values()))
    red_counts, orange_counts = {}, {}

    for cat in categories:
        cat_cols = [col for col, c in protein_category.items() if c == cat]
        subset_red = colors_df.loc[red_rows, cat_cols]
        subset_orange = colors_df.loc[yellow_rows, cat_cols]
        red_counts[cat] = subset_red.apply(lambda r: any(c == 'red' for c in r), axis=1).sum()
        orange_counts[cat] = subset_orange.apply(lambda r: any(c == 'yellow' for c in r), axis=1).sum()

    x = range(len(categories))
    width = 0.4
    bars_orange = plt.bar([i - width/2 for i in x], [orange_counts[c] for c in categories],
                          width=width, color='orange', label='35 ≤ I < 75')
    bars_red = plt.bar([i + width/2 for i in x], [red_counts[c] for c in categories],
                       width=width, color='red', label='I ≥ 75')
    plt.xticks(x, categories, rotation=0, ha='right', fontsize=14)
    plt.yticks(fontsize=14)
    plt.ylabel("Number of Organisms", fontsize=16)
    plt.xlabel("Categories", fontsize=16)
    plt.legend(fontsize=18)
    plt.tight_layout()

    for bar in bars_orange + bars_red:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height, str(int(height)),
                 ha='center', va='bottom', fontsize=11)

    plt.savefig(save_path / "category_counts_combined.png", dpi=300, bbox_inches='tight')
    plt.close()