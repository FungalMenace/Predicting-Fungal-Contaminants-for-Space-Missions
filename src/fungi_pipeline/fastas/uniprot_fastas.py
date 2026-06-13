"""
generate_default_uniprot_fastas.py
----------------------------------
Script to:
  - Derive a default list of fungal organisms from UniProt taxonomy TSV and Excel matrix.
  - Fetch FASTAs from UniProt (using custom requests-based logic).
  - Fetch missing/failed ones from UniParc using `not_found` list.
  - Rename UniParc outputs to organism names.
  - Delete empty or invalid FASTAs at the end.
"""

import os
import requests
import pandas as pd
from pathlib import Path
from src.fungi_pipeline.fastas.extract_fastas import (
    ExtractionConfig, BaseExtractor, dedupe_fasta_by_sequence
)


# ---------- Step 1: Generate new_org_list ----------

def build_new_org_list(uniprot_tsv: Path, matrix_xlsx: Path) -> list[str]:
    """
    Create a list of new fungal organisms not already present in the existing matrix.
    """
    df2 = pd.read_csv(uniprot_tsv, sep="\t")
    df2 = df2.drop_duplicates(subset=["Organism"])
    org_name2 = df2["Organism"].tolist()
    unique_orgs = {f"{x.split()[0]} {x.split()[1]}" for x in org_name2 if len(x.split()) >= 2}

    df3 = pd.read_excel(matrix_xlsx)
    df3.columns = df3.iloc[0]
    df3 = df3.iloc[1:-10]
    organism_list3 = df3["Organism"]

    reduced_org2 = []
    for org2 in unique_orgs:
        for org3 in organism_list3:
            if org2.lower() in str(org3).lower():
                reduced_org2.append(org2)
                break

    new_org_list = list(unique_orgs - set(reduced_org2))
    print(f"[INFO] Derived {len(new_org_list)} unique new organisms.")
    return sorted(new_org_list)


# ---------- Step 2: UniProt Fetching (custom logic) ----------

def fetch_from_uniprot_custom(org_list: list[str], output_dir: Path) -> tuple[pd.DataFrame, list[tuple[str, str | None]]]:
    """
    Fetch proteomes directly from UniProt using REST API endpoints.
    Returns both:
        - DataFrame summary
        - not_found list of tuples (organism, proteome_id)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    proteome_search_url = "https://rest.uniprot.org/proteomes/search"
    proteome_stream_url = "https://rest.uniprot.org/uniprotkb/stream"

    results = []
    count_success = 0
    not_found = []

    for org in org_list:
        print(f"\n[INFO] Searching proteome for: {org}")
        filename = f"{org.replace(' ', '_')}_.fasta"
        filepath = output_dir / filename

        if filepath.exists():
            print(f"  [SKIP] {filename} already exists.")
            continue

        # Step 1: Search for proteome
        params = {"query": org}
        try:
            response = requests.get(proteome_search_url, params=params, timeout=60)
        except Exception as e:
            print(f"  [ERROR] Network error for {org}: {e}")
            not_found.append((org, None))
            results.append({
                "Input organism": org,
                "Matched organism": None,
                "Proteome ID": None,
                "FASTA file": None,
                "Status": f"Network error: {e}"
            })
            continue

        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                proteome = data["results"][0]
                proteome_id = proteome["id"]
                sci_name = proteome["taxonomy"]["scientificName"]
                print(f"  [FOUND] {sci_name} ({proteome_id})")


                # Step 2: Download FASTA
                fasta_url = f"{proteome_stream_url}?format=fasta&query=proteome:{proteome_id}"
                fasta_resp = requests.get(fasta_url, timeout=120)

                if fasta_resp.status_code == 200 and fasta_resp.text.strip():
                    count_success += 1
                    with open(filepath, "w") as f:
                        f.write(fasta_resp.text)
                    print(f"  [OK] Saved {filename}")
                    results.append({
                        "Input organism": org,
                        "Matched organism": sci_name,
                        "Proteome ID": proteome_id,
                        "FASTA file": str(filepath),
                        "Status": "Downloaded"
                    })
                else:
                    print(f"  [WARN] Empty or failed FASTA for {org}")
                    not_found.append((org, proteome_id))
                    results.append({
                        "Input organism": org,
                        "Matched organism": sci_name,
                        "Proteome ID": proteome_id,
                        "FASTA file": None,
                        "Status": f"Download error {fasta_resp.status_code}"
                    })
            else:
                print(f"  [WARN] No proteome found for {org}")
                not_found.append((org, None))
                results.append({
                    "Input organism": org,
                    "Matched organism": None,
                    "Proteome ID": None,
                    "FASTA file": None,
                    "Status": "Not found"
                })
        else:
            print(f"  [ERROR] Search error {response.status_code} for {org}")
            not_found.append((org, None))
            results.append({
                "Input organism": org,
                "Matched organism": None,
                "Proteome ID": None,
                "FASTA file": None,
                "Status": f"Search error {response.status_code}"
            })

    # Save summary
    df = pd.DataFrame(results)
    summary_path = output_dir / "proteome_summary.csv"
    df.to_csv(summary_path, index=False)
    print(f"\n[INFO] Saved UniProt summary to {summary_path}")
    print(f"[INFO] Successfully downloaded {count_success}/{len(org_list)} organisms.")
    print(f"[INFO] {len(not_found)} organisms to try fetching from UniParc.")
    return df, not_found


# ---------- Step 3: UniParc Fetching (using not_found list) ----------

class UniParcFetcher(BaseExtractor):
    """
    Fetch missing proteomes from UniParc using (org_name, proteome_id) pairs from not_found list.
    Uses the tested standalone UniParc download logic.
    """
    BASE_URL = "https://rest.uniprot.org/uniparc/proteome/{proteome_id}/stream?compressed=False&format=fasta"

    def fetch(self, not_found: list[tuple[str, str | None]], output_dir: Path) -> None:
        """
        Download proteomes from UniParc for all valid proteome IDs in not_found list.

        Args:
            not_found: List of (organism_name, proteome_id) tuples
            output_dir: Directory where downloaded .fasta.gz files are saved
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Starting UniParc fetch for {len(not_found)} entries ...")

        # Extract just proteome IDs that are valid (not None)
        proteome_ids = [pid for _, pid in not_found if pid]

        base_url = self.BASE_URL

        for proteome_id in proteome_ids:
            out_filename = f"{proteome_id}.fasta.gz"
            out_filepath = output_dir / out_filename

            if out_filename in os.listdir(output_dir):
                print(f"[SKIP] {out_filename} already exists.")
                continue

            try:
                print(f"[INFO] Downloading {proteome_id} ...")
                url = base_url.format(proteome_id=proteome_id)
                response = requests.get(url, timeout=120)

                if response.status_code == 200:
                    with open(out_filepath, "wb") as f:
                        f.write(response.content)
                    print(f"[OK] Saved: {out_filepath}")
                else:
                    print(f"[WARN] Failed to download {proteome_id}: HTTP {response.status_code}")

            except Exception as e:
                print(f"[ERROR] Error for {proteome_id}: {e}")

        print("[INFO] UniParc downloads finished.")



# ---------- Step 4: Postprocessing (rename & dedupe) ----------

def postprocess_uniparc(output_dir: Path, not_found: list[tuple[str, str | None]]) -> None:
    """
    Postprocess UniParc FASTA files:
      1. Rename all .fasta.gz files to .fasta
      2. Rename files from proteome_id-based names to organism-based names
    """
    print("[INFO] Starting UniParc postprocessing...")

    # Build lookup lists
    organism_names = [org for org, pid in not_found if pid]
    proteome_ids = [pid for org, pid in not_found if pid]

    # Step 1: Rename .fasta.gz -> .fasta
    for file in os.listdir(output_dir):
        if file.endswith(".fasta.gz"):
            old_path = output_dir / file
            new_path = output_dir / file.replace(".gz", "")
            os.rename(old_path, new_path)
            print(f"Renamed: {file} -> {new_path.name}")

    # Step 2: Rename .fasta files to organism-based names
    for filename in os.listdir(output_dir):
        if filename.endswith(".fasta"):
            prot_id = filename.split(".")[0]
            if prot_id in proteome_ids:
                index = proteome_ids.index(prot_id)
                new_name = organism_names[index].replace("_.fasta", "")
                new_filename = f"{new_name}.fasta"

                src = output_dir / filename
                dst = output_dir / new_filename

                os.rename(src, dst)
                print(f"Renamed {filename} to {new_filename}")

    print("[INFO] UniParc postprocessing completed.")



# ---------- Step 5: Final Cleanup ----------

def delete_empty_fastas(folder: Path) -> None:
    deleted = 0
    for f in folder.glob("*.fasta"):
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                lines = [ln.strip() for ln in fh if ln.strip()]
            if not lines:
                f.unlink()
                deleted += 1
                print(f"[CLEANUP] Deleted empty file: {f.name}")
                continue
            seq_lines = [ln for ln in lines if not ln.startswith(">")]
            total_seq_len = sum(len(ln) for ln in seq_lines)
            if len(seq_lines) == 0 or total_seq_len < 10:
                f.unlink()
                deleted += 1
                print(f"[CLEANUP] Deleted header-only file: {f.name}")
        except Exception as e:
            print(f"[WARN] Could not read {f.name}: {e}")
    print(f"[INFO] Deleted {deleted} empty/invalid FASTA files from {folder}")


# ---------- Step 6: Main Pipeline ----------

def main():
    BASE_DIR = Path(__file__).resolve().parent

    uniprot_tsv = Path("/Users/vannshjani/Downloads/FungalMenaceToo/other_files/proteomes_taxonomy_id_4751_2025_09_17.tsv")
    matrix_xlsx = Path("/Users/vannshjani/Downloads/FungalMenaceToo/Excel_files/organism_protein_matrix_combined_with_phyla.xlsx")

    output_uniprot = BASE_DIR / "uniprot_fastas"
    output_uniparc = BASE_DIR / "uniparc_fastas"

    # Step 1: Build organism list
    new_org_list = build_new_org_list(uniprot_tsv, matrix_xlsx)

    # Step 2: Fetch UniProt proteomes
    df_uniprot, not_found = fetch_from_uniprot_custom(new_org_list, output_uniprot)

    # Step 3: Fetch missing ones from UniParc
    cfg = ExtractionConfig(output_dir=output_uniparc)
    uniparc_fetcher = UniParcFetcher(cfg)
    uniparc_fetcher.fetch(not_found, output_uniparc)

    # Step 4: Postprocess UniParc files
    postprocess_uniparc(output_uniparc, not_found)

    # Step 5: Cleanup
    print("\n[INFO] Performing final cleanup ...")
    delete_empty_fastas(output_uniprot)
    delete_empty_fastas(output_uniparc)

    print("\n[ALL DONE] Default UniProt + UniParc FASTA extraction completed.")


if __name__ == "__main__":
    main()
