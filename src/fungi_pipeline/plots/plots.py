"""
Notebook-faithful plotting for the fungi pipeline.

Drop the functions below into your existing `plots.py`. They reproduce EVERY
figure saved by testing_copy.ipynb, splitting them into two sub-folders:

    <plots>/color
    <plots>/black and white

Your existing `plots.py` already defines `cell_color`, `ensure_plots_dir`,
and imports `PROTEIN_CATEGORY`. Those are reused here (do NOT redefine them);
only the `CATEGORY_ABBR`, `build_protein_category`, `_abbr_labels`,
`prepare_plot_data`, `compute_s_scores`, `_combined_counts`, the `plot_*`
functions, and the new `generate_existing_excel_plots` body are new.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

from src.fungi_pipeline.excel.make_excel import PROTEIN_CATEGORY
from src.fungi_pipeline.config import PLOTS_EXPORT_DIR
# NOTE: `cell_color` and `ensure_plots_dir` come from your existing plots.py.


# Category name -> short label used on the combined plots (cells 17-20).
# The notebook hard-codes ["AMR","BF","HP","RAD","SF","TH"] assuming a fixed
# sort order; this mapping keeps labels aligned to whatever order the
# categories actually appear in. Covers both the short keys used in this
# workbook / make_excel AND the notebook's long-form keys, so it works
# regardless of how PROTEIN_CATEGORY names its categories. Anything missing
# falls back to the full category name (never silently mislabelled).
CATEGORY_ABBR = {
    # short-form keys (as they appear in the Excel group-header row / make_excel)
    "AMR": "AMR",
    "Biofilm": "BF",
    "H-pat": "HP",
    "Rad-res": "RAD",
    "Spore": "SF",
    "Thermophile": "TH",
    # long-form keys (notebook mapping)
    "antimicrobial-resistance": "AMR",
    "Biofilm-formation": "BF",
    "Human-pathogenicity": "HP",
    "Radiation-resistance": "RAD",
    "Spore-formation": "SF",
}

def ensure_plots_dir(save_path):
    """Create the output directory (and parents) if it doesn't exist."""
    Path(save_path).mkdir(parents=True, exist_ok=True)


def cell_color(val):
    """Return the colour category for a single identity value."""
    if val is None or pd.isna(val) or ',' in str(val):
        return 'blue'
    val = float(val)
    if val > 75:
        return 'red'
    elif val > 35:
        return 'yellow'
    else:
        return 'blue'

# --------------------------------------------------------------------------- #
# shared helpers
# --------------------------------------------------------------------------- #
def build_protein_category(protein_cols):
    """Map each protein column -> its category using PROTEIN_CATEGORY."""
    protein_category = {}
    for col in protein_cols:
        abbr = str(col).split("-")[0]
        for cat, prots in PROTEIN_CATEGORY.items():
            if abbr in prots:
                protein_category[col] = cat
                break
    return protein_category


def _abbr_labels(categories):
    return [CATEGORY_ABBR.get(c, c) for c in categories]


def prepare_plot_data(df):
    """Derive the shared structures every plot below needs (matches notebook).

    Protein columns are selected by PROTEIN_CATEGORY membership rather than a
    positional slice. This workbook has THREE trailing non-protein columns
    ('r,y,r+y', 'Source', 'Phyla'), so the old `df.columns[2:-2]` wrongly
    swept 'r,y,r+y' in; membership selection picks exactly the 25 proteins.
    """
    protein_category = build_protein_category(df.columns)
    protein_cols = list(protein_category.keys())
    colors_df = df[protein_cols].map(cell_color)  # noqa: F821 (from your plots.py)
    red_rows = colors_df.apply(lambda r: any(c == 'red' for c in r), axis=1)
    yellow_rows = colors_df.apply(
        lambda r: (not any(c == 'red' for c in r)) and any(c == 'yellow' for c in r),
        axis=1,
    )
    return protein_cols, colors_df, protein_category, red_rows, yellow_rows


def compute_s_scores(df, colors_df, protein_category):
    """S-score = number of categories with >=1 protein above the threshold (cell 6)."""
    cats = set(protein_category.values())
    s_scores_35, s_scores_75 = [], []
    for idx in df.index:
        s35 = s75 = 0
        for cat in cats:
            cat_cols = [col for col, c in protein_category.items() if c == cat]
            subset = colors_df.loc[idx, cat_cols]
            if any(c in ('red', 'yellow') for c in subset):
                s35 += 1
            if any(c == 'red' for c in subset):
                s75 += 1
        s_scores_35.append(s35)
        s_scores_75.append(s75)
    return s_scores_35, s_scores_75


def _combined_counts(colors_df, protein_category, red_rows, yellow_rows, categories):
    """Per-category counts of red rows / yellow rows (cells 17-20)."""
    red_counts, yellow_counts = {}, {}
    for cat in categories:
        cat_cols = [col for col, c in protein_category.items() if c == cat]
        red_counts[cat] = colors_df.loc[red_rows, cat_cols].apply(
            lambda r: any(c == 'red' for c in r), axis=1).sum()
        yellow_counts[cat] = colors_df.loc[yellow_rows, cat_cols].apply(
            lambda r: any(c == 'yellow' for c in r), axis=1).sum()
    return red_counts, yellow_counts


# --------------------------------------------------------------------------- #
# COLOR plots
# --------------------------------------------------------------------------- #
def plot_a_score_color(df, save_path):                       # cell 2 (colour variant)
    ensure_plots_dir(save_path)  # noqa: F821
    plt.figure(figsize=(10, 6))
    bins = np.arange(0, 14, 1)
    a_scores = pd.to_numeric(df['A-score'], errors='coerce')  # column is object dtype
    _, bin_edges, _ = plt.hist(a_scores, bins=bins,
                               color='blue', alpha=0.7, edgecolor='black')
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    plt.xlabel("A-score", fontsize=20)
    plt.ylabel("Number of Organisms", fontsize=20)
    plt.xticks(bin_centers, [str(int(x)) for x in bin_centers], fontsize=20)
    plt.yticks(fontsize=20)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(Path(save_path) / "A_score_histogram.png", dpi=300)
    plt.close()


def plot_s_scores_color(s_scores_35, s_scores_75, save_path):  # cell 7
    ensure_plots_dir(save_path)  # noqa: F821
    plt.figure(figsize=(10, 6))
    plt.hist(s_scores_35, bins=np.arange(0, 9) - 0.5,
             color='orange', alpha=0.7, edgecolor='black')
    plt.xlabel("S-score (threshold \u2265 35)", fontsize=20)
    plt.ylabel("Number of Organisms", fontsize=20)
    plt.xticks(range(0, 7), fontsize=20)
    plt.yticks(fontsize=20)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(Path(save_path) / "S_score_35_histogram.png", dpi=300)
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.hist(s_scores_75, bins=np.arange(0, 9) - 0.5,
             color='red', alpha=0.7, edgecolor='black')
    plt.xlabel("S-score (threshold \u2265 75)", fontsize=20)
    plt.ylabel("Number of Organisms", fontsize=20)
    plt.xticks(range(0, 7), fontsize=20)
    plt.yticks(fontsize=20)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(Path(save_path) / "S_score_75_histogram.png", dpi=300)
    plt.close()


def plot_category_counts_color(df, protein_cols, protein_category, save_path):  # cells 12-13
    ensure_plots_dir(save_path)  # noqa: F821
    # numeric coercion so comma / blank cells don't break the `>=` comparison
    num_df = df[protein_cols].apply(pd.to_numeric, errors='coerce')

    category_counts_75 = defaultdict(int)
    category_counts_35 = defaultdict(int)
    for cat in set(protein_category.values()):
        cat_cols = [col for col, c in protein_category.items() if c == cat]
        category_counts_75[cat] = (num_df[cat_cols] >= 75).any(axis=1).sum()
        category_counts_35[cat] = (num_df[cat_cols] >= 35).any(axis=1).sum()

    categories = sorted(category_counts_75.keys())

    plt.figure(figsize=(12, 6))
    plt.bar(categories, [category_counts_75[c] for c in categories],
            color='red', alpha=0.7)
    plt.ylabel('Number of Organisms with at least one protein > 75% identity')
    plt.title('Organisms with at least one protein > 75% identity per Category')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(Path(save_path) / "Category_counts_75.png")
    plt.close()

    plt.figure(figsize=(12, 6))
    plt.bar(categories, [category_counts_35[c] for c in categories],
            color='orange', alpha=0.7)
    plt.ylabel('Number of Organisms with at least one protein > 35% identity')
    plt.title('Organisms with at least one protein > 35% identity per Category')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(Path(save_path) / "Category_counts_35.png")
    plt.close()


def plot_combined_counts_color(red_counts, yellow_counts, categories, save_path):  # cell 17
    ensure_plots_dir(save_path)  # noqa: F821
    red_values = [red_counts[c] for c in categories]
    yellow_values = [yellow_counts[c] for c in categories]
    x = range(len(categories))
    width = 0.4

    plt.figure(figsize=(12, 6))
    bars_red = plt.bar([i - width / 2 for i in x], red_values, width=width,
                       label='I \u2265 75', color='red', alpha=0.7)
    bars_yellow = plt.bar([i + width / 2 for i in x], yellow_values, width=width,
                          label='35 \u2264 I < 75', color='orange', alpha=0.7)
    plt.ylabel('Number of Organisms', fontsize=14)
    plt.xticks(x, _abbr_labels(categories), rotation=45, ha='right', fontsize=14)
    plt.legend()
    plt.tight_layout()
    for bar in list(bars_red) + list(bars_yellow):
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, h, str(int(h)),
                 ha='center', va='bottom', fontsize=12)
    plt.savefig(Path(save_path) / "Red_Yellow_rows_category_counts_combined.png")
    plt.close()


def plot_combined_counts_color_log(red_counts, yellow_counts, categories, save_path):  # cell 18
    ensure_plots_dir(save_path)  # noqa: F821
    red_values = [red_counts[c] for c in categories]
    orange_values = [yellow_counts[c] for c in categories]
    x = range(len(categories))
    bar_width = 0.4

    plt.figure()  # notebook cell 18 used the default figure size
    bars_orange = plt.bar([i - bar_width / 2 for i in x], orange_values, width=bar_width,
                          label='35 \u2264 I < 75', color='orange')
    bars_red = plt.bar([i + bar_width / 2 for i in x], red_values, width=bar_width,
                       label='I \u2265 75', color='red')
    plt.xticks(x, _abbr_labels(categories), rotation=0, ha='center', fontsize=14)
    plt.yticks(fontsize=14)
    plt.ylabel('Number of Organisms', fontsize=16)
    plt.xlabel('Categories', fontsize=16)
    plt.legend(fontsize=12, loc='best')
    plt.tight_layout()
    plt.yscale('log')
    for bar in list(bars_orange) + list(bars_red):
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, h, str(int(h)),
                 ha='center', va='bottom', fontsize=11)
    plt.savefig(Path(save_path) / "Orange_Red_rows_category_counts_combined_modified.png",
                dpi=300, bbox_inches='tight')
    plt.close()


# --------------------------------------------------------------------------- #
# BLACK & WHITE plots
# --------------------------------------------------------------------------- #
def plot_a_score_bw(df, save_path):                          # cell 2
    ensure_plots_dir(save_path)  # noqa: F821
    plt.figure(figsize=(10, 6))
    bins = np.arange(0, 14, 1)
    a_scores = pd.to_numeric(df['A-score'], errors='coerce')  # column is object dtype
    _, bin_edges, _ = plt.hist(a_scores, bins=bins, color='white',
                               edgecolor='black', hatch='///',
                               label='A-score distribution')
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    plt.xlabel("A-score", fontsize=25)
    plt.ylabel("Number of Organisms", fontsize=25)
    plt.xticks(bin_centers, [str(int(x)) for x in bin_centers], fontsize=30)
    plt.yticks(fontsize=30)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(Path(save_path) / "A_score_histogram_bw.png", dpi=300)
    plt.close()


def plot_s_scores_bw(s_scores_35, s_scores_75, save_path):   # cell 8
    ensure_plots_dir(save_path)  # noqa: F821
    plt.figure(figsize=(10, 6))
    plt.hist(s_scores_35, bins=np.arange(0, 9) - 0.5, color='white',
             edgecolor='black', hatch='///', label='Threshold \u2265 35')
    plt.xlabel("S-score", fontsize=25)
    plt.ylabel("Number of Organisms", fontsize=25)
    plt.xticks(range(0, 7), fontsize=30)
    plt.yticks(fontsize=30)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(Path(save_path) / "S_score_35_histogram_bw.png", dpi=300)
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.hist(s_scores_75, bins=np.arange(0, 9) - 0.5, color='white',
             edgecolor='black', hatch='\\\\\\', label='Threshold \u2265 75')
    plt.xlabel("S-score (threshold > 75)", fontsize=20)
    plt.ylabel("Number of Organisms", fontsize=20)
    plt.xticks(range(0, 7), fontsize=20)
    plt.yticks(fontsize=20)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.legend(fontsize=14)
    plt.tight_layout()
    plt.savefig(Path(save_path) / "S_score_75_histogram_bw.png", dpi=300)
    plt.close()


def plot_combined_counts_bw_log(red_counts, yellow_counts, categories, save_path):  # cell 19
    ensure_plots_dir(save_path)  # noqa: F821
    red_values = [red_counts[c] for c in categories]
    yellow_values = [yellow_counts[c] for c in categories]
    x = range(len(categories))
    bar_width = 0.4

    plt.figure()  # notebook cell 19 used the default figure size
    bars_high = plt.bar([i - bar_width / 2 for i in x], red_values, width=bar_width,
                        label='I \u2265 75', color='white', edgecolor='black',
                        hatch='///', align='center')
    bars_low = plt.bar([i + bar_width / 2 for i in x], yellow_values, width=bar_width,
                       label='35 \u2264 I < 75', color='white', edgecolor='black',
                       hatch='-----', align='center')
    plt.xticks(x, _abbr_labels(categories), fontsize=14)
    plt.xlabel('Categories', fontsize=16)
    plt.ylabel('Number of Organisms', fontsize=16)
    plt.legend(loc='best', fontsize=12)
    plt.tight_layout()
    plt.yscale('log')
    plt.yticks(fontsize=14)
    for bar in list(bars_high) + list(bars_low):
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, h, str(int(h)),
                 ha='center', va='bottom', fontsize=11)
    plt.savefig(Path(save_path) / "Red_Yellow_rows_category_counts_combined_bw_modified.png",
                dpi=300, bbox_inches='tight')
    plt.close()


def plot_combined_counts_bw(red_counts, yellow_counts, categories, save_path):  # cell 20
    ensure_plots_dir(save_path)  # noqa: F821
    red_values = [red_counts[c] for c in categories]
    moderate_values = [yellow_counts[c] for c in categories]
    x = range(len(categories))
    width = 0.4

    plt.figure(figsize=(14, 8))
    bars_moderate = plt.bar([i - width / 2 for i in x], moderate_values, width=width,
                            label='35 \u2264 I < 75', color='white', edgecolor='black',
                            hatch='----', alpha=1.0)
    bars_high = plt.bar([i + width / 2 for i in x], red_values, width=width,
                        label='I \u2265 75', color='white', edgecolor='black',
                        hatch='///', alpha=1.0)
    plt.xticks(x, _abbr_labels(categories), rotation=45, ha='right', fontsize=28)
    plt.yticks(fontsize=24)
    plt.ylabel('Number of Organisms', fontsize=24)
    plt.legend(fontsize=20, loc='best', frameon=False)
    plt.tight_layout()
    for bar in list(bars_moderate) + list(bars_high):
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, h, str(int(h)),
                 ha='center', va='bottom', fontsize=24)
    plt.savefig(Path(save_path) / "BW_rows_category_counts_combined.png",
                dpi=300, bbox_inches='tight')
    plt.close()


# =========================================================================== #
# Rewritten pipeline method — paste this into your pipeline class.
# =========================================================================== #
def generate_existing_excel_plots(self):
    print("\n[Step 4] Generating plots from existing Excel summary...")

    # --- load exactly as before ---
    df = pd.read_excel(self.excel_file)
    df.columns = df.iloc[0]
    df.drop([1, 2], inplace=True)
    df = df.iloc[1:-10]
    df.rename(columns={df.columns[0]: "Organism", df.columns[1]: "A-score"},
              inplace=True)

    # --- output sub-folders ---
    plots_root = Path(PLOTS_EXPORT_DIR)
    color_dir = plots_root / "color"
    bw_dir = plots_root / "black and white"
    ensure_plots_dir(color_dir)   # noqa: F821
    ensure_plots_dir(bw_dir)      # noqa: F821

    # --- compute shared structures once ---
    protein_cols, colors_df, protein_category, red_rows, yellow_rows = \
        prepare_plot_data(df)
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