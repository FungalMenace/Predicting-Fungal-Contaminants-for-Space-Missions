import os
import subprocess
import shutil
from Bio import Entrez
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning, module="Bio.Entrez")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = "/docs/files/fastas_ncbi.txt"
TEMP_DIR = os.path.join(BASE_DIR, "ncbi_temp")
FINAL_DIR = os.path.join(BASE_DIR, "ncbi_fastas")

# NCBI requires a valid email
Entrez.email = os.environ.get("JGI_USERNAME", "your_email@example.com")



def safe_mkdir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def run_cmd(cmd):
    """Run a subprocess command with error handling."""
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"{e}")
        return False
    return True



def read_species_list(file_path):
    """Read species names from text file, ignoring blanks and comments."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    with open(file_path, "r") as f:
        species = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"Loaded {len(species)} species from {file_path}")
    return species


def get_taxid(species_name):
    """Return NCBI TaxID for a species name using Entrez."""
    try:
        handle = Entrez.esearch(db="taxonomy", term=species_name)
        record = Entrez.read(handle)
        handle.close()
        if record["IdList"]:
            return record["IdList"][0]
    except Exception as e:
        print(f"TaxID lookup failed for {species_name}: {e}")
    return None


def download_proteome(taxid, species_name, output_dir):
    """
    Download protein FASTA from NCBI Datasets for a given TaxID.

    Returns:
        str | None: Path to extracted folder, or None if failed.
    """
    species_safe = species_name.replace(" ", "_")
    zip_filename = os.path.join(output_dir, f"{species_safe}_proteins.zip")
    extract_dir = os.path.join(output_dir, species_safe)

    if os.path.exists(extract_dir):
        print(f"{species_name} already downloaded, skipping.")
        return extract_dir

    print(f"⬇Downloading proteome for {species_name} (TaxID: {taxid}) ...")
    cmd = [
        "datasets", "download", "genome",
        "taxon", str(taxid),
        "--include", "protein",
        "--filename", zip_filename
    ]

    if not run_cmd(cmd):
        print(f"Failed to download {species_name}")
        return None

    # Unzip
    safe_mkdir(extract_dir)
    if not run_cmd(["unzip", "-o", zip_filename, "-d", extract_dir]):
        print(f"Failed to extract {zip_filename}")
        return None

    print(f"✔️  Finished downloading {species_name}")
    return extract_dir


def collect_fastas(root_dir, final_dir):
    """
    Walk through all downloaded folders, extract `protein.faa` files,
    rename to <Organism>.fasta, and copy to final_dir.
    """
    safe_mkdir(final_dir)
    count = 0

    for dirpath, _, filenames in os.walk(root_dir):
        if "protein.faa" in filenames:
            protein_path = os.path.join(dirpath, "protein.faa")
            rel_path = os.path.relpath(protein_path, root_dir)
            top_folder = rel_path.split(os.sep)[0]
            new_filename = top_folder.rstrip("_") + ".fasta"
            out_path = os.path.join(final_dir, new_filename)

            shutil.copy2(protein_path, out_path)
            count += 1
            print(f"Copied: {protein_path} → {out_path}")

    print(f"\nCollected {count} FASTA files into {final_dir}")
    return count


def clean_filenames(folder):
    """Remove trailing underscores from filenames like 'Candida_albicans_.fasta'."""
    renamed = 0
    for file in os.listdir(folder):
        if file.endswith("_.fasta"):
            new_name = file.replace("_.fasta", ".fasta")
            os.rename(os.path.join(folder, file), os.path.join(folder, new_name))
            renamed += 1
            print(f"✏️  Renamed: {file} → {new_name}")
    print(f"Cleaned {renamed} filenames in {folder}")



def main():
    print("\n=== NCBI FASTA Downloader ===\n")

    safe_mkdir(TEMP_DIR)
    safe_mkdir(FINAL_DIR)

    species_list = read_species_list(INPUT_FILE)
    total = len(species_list)
    success = 0

    for sp in species_list:
        taxid = get_taxid(sp)
        if not taxid:
            print(f"Could not find TaxID for {sp}")
            continue

        extract_path = download_proteome(taxid, sp, TEMP_DIR)
        if extract_path:
            success += 1

    print(f"\nDownloaded {success}/{total} species.\n")

    # Collect and clean FASTAs
    collect_fastas(TEMP_DIR, FINAL_DIR)
    clean_filenames(FINAL_DIR)

    print(f"\nAll FASTAs are ready in: {FINAL_DIR}")

    # delete temp dir
    shutil.rmtree(TEMP_DIR)
    print(f"Removed temporary directory: {TEMP_DIR}")



if __name__ == "__main__":
    main()
