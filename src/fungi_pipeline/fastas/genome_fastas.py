"""
Script to:
  1. Build JGI portal and name mappings (using metadata CSV)
  2. Log into JGI
  3. Download GeneCatalog protein FASTA files
  4. Decompress each .fasta.gz into organism_name.fasta

"""

import os
import time
import json
import gzip
import pandas as pd
import requests
from xml.etree import ElementTree



DATA_PATH = "/docs/csvs/gold_20250607_211424.csv"
PROJECT_METADATA_CSV = "/docs/csvs/genome-projects.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "genome_fastas")
MAPPINGS_JSON = os.path.join(BASE_DIR, "jgi_portal_mappings.json")

USERNAME = os.environ.get("JGI_USERNAME")
PASSWORD = os.environ.get("JGI_PASSWORD")



def load_organisms(csv_path: str):
    """Load organism names from GOLD export CSV."""
    df = pd.read_csv(csv_path)
    organisms = df["Organism.Organism Name"].dropna().tolist()
    unique_orgs = sorted({f"{o.split()[0]} {o.split()[1]}" for o in organisms if len(o.split()) >= 2})
    print(f"Loaded {len(organisms)} organisms ({len(unique_orgs)} unique species).")
    return unique_orgs


def extract_portal_id_from_formula(formula: str):
    """Extract portal ID from Excel HYPERLINK formula."""
    if not isinstance(formula, str) or "HYPERLINK" not in formula:
        return None
    try:
        return formula.split('","')[-1].replace('")', '').strip()
    except Exception:
        return None


def normalize_org_name(org_name: str):
    """Return lowercase organism name without strain or extra words."""
    parts = org_name.split()
    if len(parts) >= 2:
        return " ".join(parts[:2]).lower()  # only Genus + species
    return org_name.lower()


def build_mappings(gold_csv, metadata_csv):
    """Build portal and complete name mappings using metadata CSV."""
    print("\n=== Building portal and name mappings from metadata ===")
    organisms = load_organisms(gold_csv)
    df_meta = pd.read_csv(metadata_csv)

    print(organisms[:5], len(organisms))

    portal_id_mappings = {}
    complete_name_mappings = {}

    for org in organisms:
        org_clean = normalize_org_name(org)
        match_found = False

        for _, row in df_meta.iterrows():
            project_name = str(row.get("Project Name", "")).lower()
            portal_formula = str(row.get("Portal ID", "")).strip()

            if org_clean in project_name:
                portal_id = extract_portal_id_from_formula(portal_formula)
                if portal_id:
                    hyperlink = f'=HYPERLINK("http://genome.jgi.doe.gov/{portal_id}","{portal_id}")'
                    portal_id_mappings[org] = hyperlink
                    complete_name_mappings[org] = str(row.get("Project Name", "")).strip()
                    match_found = True
                    print(f"[MATCH] {org} → {portal_id}")
                    break  # stop at first match

        if not match_found:
            print(f"[MISS] No portal match found in metadata for {org}")

    with open(MAPPINGS_JSON, "w") as f:
        json.dump({
            "portal_id_mappings": portal_id_mappings,
            "complete_name_mappings": complete_name_mappings
        }, f, indent=2)

    print(f"\nBuilt {len(portal_id_mappings)} portal mappings and saved to {MAPPINGS_JSON}")
    return portal_id_mappings, complete_name_mappings


def load_mappings():
    """Load from JSON if exists, otherwise rebuild mappings."""
    if os.path.exists(MAPPINGS_JSON):
        print(f"Loading mappings from {MAPPINGS_JSON} ...")
        with open(MAPPINGS_JSON) as f:
            data = json.load(f)
        return data["portal_id_mappings"], data["complete_name_mappings"]
    else:
        return build_mappings(DATA_PATH, PROJECT_METADATA_CSV)


def clean_portal_id(hyperlink_formula: str):
    """Extract portal ID from Excel HYPERLINK formula string."""
    if not hyperlink_formula or "HYPERLINK" not in hyperlink_formula:
        return None
    try:
        return hyperlink_formula.split('","')[-1].replace('")', '')
    except Exception:
        return None


def jgi_login(username: str, password: str):
    """Log in to JGI portal and return a session with credentials."""
    login_url = "https://signon.jgi.doe.gov/signon/create"
    session = requests.Session()
    print(f"Logging in to JGI as {username} ...")
    resp = session.post(login_url, data={"login": username, "password": password})
    if not resp.ok:
        raise ConnectionError("Login failed. Check your JGI credentials.")
    return session


def decompress_fasta_gz(file_path: str, organism_name: str):
    """Decompress .fasta.gz to organism_name.fasta and delete the gz file."""
    try:
        out_file = os.path.join(os.path.dirname(file_path), f"{organism_name.replace(' ', '_')}.fasta")
        with gzip.open(file_path, "rt") as f_in, open(out_file, "w") as f_out:
            for line in f_in:
                f_out.write(line)
        os.remove(file_path)
        print(f"Decompressed to {out_file}")
        return out_file
    except Exception as e:
        print(f"Decompression failed for {file_path}: {e}")
        return None


def download_proteomes(session, portal_dict, name_mappings):
    """Download and decompress GeneCatalog protein FASTA files."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    success_count = 0
    not_found = []
    id_name_mappings = {}

    for org, portal_formula in portal_dict.items():
        portal_id = clean_portal_id(portal_formula)
        if not portal_id:
            print(f"[WARN] Could not parse portal ID for {org}")
            not_found.append(org)
            continue

        print(f"\nProcessing {org} ({portal_id})")
        files_url = f"https://genome-downloads.jgi.doe.gov/portal/ext-api/downloads/get-directory?organism={portal_id}"
        resp = session.get(files_url)
        try:
            root = ElementTree.fromstring(resp.content)
        except Exception:
            print(f"[ERROR] Failed to parse XML for {org}")
            not_found.append(org)
            continue

        found = False
        for file in root.findall(".//file"):
            filename = file.attrib["filename"]
            if "GeneCatalog_proteins" in filename and filename.endswith(".aa.fasta.gz"):
                download_url = "https://genome-downloads.jgi.doe.gov" + file.attrib["url"].replace("&amp;", "&")
                out_path = os.path.join(OUTPUT_DIR, f"{portal_id}_{filename}")
                print(f"  Downloading {filename} -> {out_path}")
                file_resp = session.get(download_url)
                with open(out_path, "wb") as out_file:
                    out_file.write(file_resp.content)
                success_count += 1
                project_name = name_mappings.get(org, org)
                id_name_mappings[portal_id] = (org, project_name)

                # Post-process: decompress and rename
                decompress_fasta_gz(out_path, org)
                found = True
                break

        if not found:
            print(f"[INFO] No GeneCatalog FASTA found for {org}")
            not_found.append(org)

    print(f"\nDownload complete. {success_count} files saved in '{OUTPUT_DIR}'.")
    if not_found:
        print(f"{len(not_found)} organisms missing: {', '.join(not_found[:5])}...")
    return id_name_mappings




def main():
    if not USERNAME or not PASSWORD:
        raise EnvironmentError("Please set JGI_USERNAME and JGI_PASSWORD environment variables.")

    portal_id_mappings, complete_name_mappings = load_mappings()
    # print(portal_id_mappings)
    # print(complete_name_mappings)
    session = jgi_login(USERNAME, PASSWORD)
    id_name_mappings = download_proteomes(session, portal_id_mappings, complete_name_mappings)

    # print("\nPortal ID → Name Mapping:")
    # for pid, (org, proj) in id_name_mappings.items():
    #     print(f"  {pid}: {org} ({proj})")


if __name__ == "__main__":
    main()
