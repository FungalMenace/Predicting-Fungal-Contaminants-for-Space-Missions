"""
make_summary_excel.py
---------------------
Generates a color-coded Excel summary of BLAST identity results.

Input:
    A folder containing one CSV per organism (e.g., "Candida_albicans.csv").
    Each CSV must contain two columns: [Protein, Identity].

Output:
    Excel workbook summarizing all organisms × proteins,
    color-coded by thresholds and including per-organism A-scores
    and Phylum information.

Usage:
    python make_summary_excel.py --i ./blast_results --o fungal_summary.xlsx
"""

import os
import glob
import json
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Alignment, Font
from openpyxl.utils import get_column_letter
import argparse
from pathlib import Path
from src.fungi_pipeline.excel.phyla import get_phylum 


FEATURES = [
    "AMR",
    "Bio",
    "Hpat",
    "TH",
    "RAD",
    "SF",
]

PROTEIN_CATEGORY = {
    "AMR": ["ERG11", "CDR1", "MDR1", "UPC2", "TAC1", "MRR1"],
    "Bio": [
        "BCR1",
        "EFG1",
        "TEC1",
        "HWP1",
        "ALS3",
        "NDT80",
        "ERG251",
        "CZF1",
        "FLO8",
    ],
    "Hpat": ["SAP5", "PLB1", "LAC1", "RIM101"],
    "TH": ["HSP90"],
    "RAD": ["RAD51"],
    "SF": ["brlA", "abaA", "wetA", "srr1"],
}



RED_FILL = PatternFill("solid", fgColor="FF6347")     # >75
YELLOW_FILL = PatternFill("solid", fgColor="FFD700")  # >35
BLUE_FILL = PatternFill("solid", fgColor="87CEFA")    # ≤35



def read_blast_results(folder):
    """Return (data, organisms, proteins)."""
    csvs = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not csvs:
        raise FileNotFoundError(f"No CSV files found in {folder}")

    data = {}
    all_proteins = set()
    organisms = []

    for path in csvs:
        organism = os.path.basename(path).replace(".csv", "")
        organism = organism.split("_blast")[0].replace("_", " ")
        if organism == "all results":
            continue
        organisms.append(organism)

        df = pd.read_csv(path)
        protein_col, pident_col = "protein", "pident"
        for _, row in df.iterrows():
            prot = str(row[protein_col]).strip()
            try:
                val = float(row[pident_col])
            except Exception:
                continue
            data[(organism, prot)] = val
            all_proteins.add(prot)

    return data, sorted(set(organisms)), sorted(all_proteins)



def build_category_mapping(all_proteins):
    prot_to_cat = {}
    for cat, prots in PROTEIN_CATEGORY.items():
        for p_abbr in prots:
            for prot in all_proteins:
                if p_abbr.lower() in prot.lower():
                    prot_to_cat[prot] = cat
                    break

    for prot in all_proteins:
        if prot not in prot_to_cat:
            prot_to_cat[prot] = "Uncategorized"

    grouped = []
    for cat in FEATURES + ["Uncategorized"]:
        grouped.extend([p for p, c in prot_to_cat.items() if c == cat])
    ordered = [p for p in grouped if p in all_proteins]
    return prot_to_cat, ordered



def load_phylum_cache(cache_path="phylum_cache.json"):
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_phylum_cache(cache, cache_path="phylum_cache.json"):
    try:
        with open(cache_path, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save phylum cache: {e}")



def generate_excel(data, organisms, all_proteins, output_path, cache_path="phylum_cache.json"):
    prot_to_cat, ordered_proteins = build_category_mapping(all_proteins)
    wb = Workbook()
    ws = wb.active
    ws.title = "BLAST Summary"

    # Category headers
    ws.cell(row=1, column=1, value="")
    ws.cell(row=1, column=2, value="")
    col = 3
    cat_to_prots = {cat: [p for p, c in prot_to_cat.items() if c == cat]
                    for cat in FEATURES + ["Uncategorized"]}
    for cat in FEATURES + ["Uncategorized"]:
        for _ in cat_to_prots[cat]:
            cell = ws.cell(row=1, column=col, value=cat)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
            col += 1

    # Header row
    ws.cell(row=2, column=1, value="Organism").font = Font(bold=True)
    ws.cell(row=2, column=2, value="A-score").font = Font(bold=True)
    for j, prot in enumerate(ordered_proteins, start=3):
        cell = ws.cell(row=2, column=j, value=prot)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    summary_col = len(ordered_proteins) + 3
    ws.cell(row=2, column=summary_col, value="r,y,r+y").font = Font(bold=True)

    # 🧬 Add Phylum column
    phylum_col = summary_col + 1
    ws.cell(row=2, column=phylum_col, value="Phylum").font = Font(bold=True)

    # Load cache
    phylum_cache = load_phylum_cache(cache_path)

    red_rows = 0
    yellow_rows = 0
    blue_rows = 0


    for i, org in enumerate(organisms, start=3):
        ws.cell(row=i, column=1, value=org)

        cat_red = {cat: 0 for cat in FEATURES}
        cat_yellow = {cat: 0 for cat in FEATURES}
        row_red = 0
        row_yellow = 0

        for j, prot in enumerate(ordered_proteins, start=3):
            val = data.get((org, prot))
            if val is None:
                continue
            c = ws.cell(row=i, column=j, value=round(val, 1))
            c.alignment = Alignment(horizontal="center")

            cat = prot_to_cat.get(prot, "Uncategorized")
            if cat in FEATURES:
                if val > 75:
                    cat_red[cat] += 1
                elif val > 35:
                    cat_yellow[cat] += 1

            if val > 75:
                c.fill = RED_FILL
                row_red += 1
            elif val > 35:
                c.fill = YELLOW_FILL
                row_yellow += 1
            else:
                c.fill = BLUE_FILL

        # A-score
        a_score = sum(2 if cat_red[c] > 0 else 1 if cat_yellow[c] > 0 else 0 for c in FEATURES)
        a_cell = ws.cell(row=i, column=2, value=a_score)
        a_cell.alignment = Alignment(horizontal="center")

        # Row color and classification
        hdr = ws.cell(row=i, column=1)
        if row_red > 0:
            hdr.fill = RED_FILL
            red_rows += 1
        elif row_yellow > 0:
            hdr.fill = YELLOW_FILL
            yellow_rows += 1
        else:
            hdr.fill = BLUE_FILL
            blue_rows += 1

        ws.cell(row=i, column=summary_col, value=f"{row_red},{row_yellow},{row_red + row_yellow}")

        # --- Identify Phylum ---
        org_clean = org.strip()
        if org_clean in phylum_cache:
            phylum = phylum_cache[org_clean]
        else:
            phylum = get_phylum(org_clean)
            phylum_cache[org_clean] = phylum
            save_phylum_cache(phylum_cache, cache_path)  # Save incrementally
        ws.cell(row=i, column=phylum_col, value=phylum)


    ws.column_dimensions[get_column_letter(1)].width = 28
    ws.column_dimensions[get_column_letter(2)].width = 12
    for j in range(3, phylum_col + 1):
        ws.column_dimensions[get_column_letter(j)].width = 16
    ws.freeze_panes = "C3"


    total_rows = len(organisms)
    last_row = len(organisms) + 5
    ws.cell(row=last_row, column=1, value="Summary Statistics").font = Font(bold=True, underline="single")

    ws.cell(row=last_row + 1, column=1, value="Total organisms")
    ws.cell(row=last_row + 1, column=2, value=total_rows)

    ws.cell(row=last_row + 2, column=1, value="Rows with ≥1 red cell")
    ws.cell(row=last_row + 2, column=2, value=red_rows)

    ws.cell(row=last_row + 3, column=1, value="Rows with ≥1 yellow (no red)")
    ws.cell(row=last_row + 3, column=2, value=yellow_rows)

    ws.cell(row=last_row + 4, column=1, value="Completely blue rows")
    ws.cell(row=last_row + 4, column=2, value=blue_rows)

    # Percentages
    ws.cell(row=last_row + 6, column=1, value="% with red")
    ws.cell(row=last_row + 6, column=2, value=round((red_rows / total_rows) * 100, 1))

    ws.cell(row=last_row + 7, column=1, value="% with yellow")
    ws.cell(row=last_row + 7, column=2, value=round((yellow_rows / total_rows) * 100, 1))

    ws.cell(row=last_row + 8, column=1, value="% completely blue")
    ws.cell(row=last_row + 8, column=2, value=round((blue_rows / total_rows) * 100, 1))


    wb.save(output_path)
    print(f"Excel saved with Phylum and statistics: {output_path}")
    print(f"Cache updated at: {cache_path}")



def main():
    parser = argparse.ArgumentParser(description="Create Excel summary from BLAST result CSVs.")
    parser.add_argument("--i", default="src/results", help="Folder with organism CSV files.")
    parser.add_argument("--o", default="fungal_summary.xlsx", help="Output Excel file path.")
    args = parser.parse_args()

    data, organisms, prots = read_blast_results(args.i)
    generate_excel(data, organisms, prots, args.o)


if __name__ == "__main__":
    main()
