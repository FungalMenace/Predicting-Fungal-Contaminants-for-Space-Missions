"""
extract_fastas.py
Reusable module for fetching fungal FASTAs from UniProt, UniParc, Ensembl Fungi, and NCBI.
"""

from __future__ import annotations
import gzip, io, os, re, time, hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Dict
import requests
import pandas as pd
import subprocess
import shutil

try:
    from Bio import Entrez, SeqIO
except Exception:
    Entrez = None
    SeqIO = None


# ---------- Utility Functions ----------

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def sanitize_name(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]+', '_', name).strip('_')

def chunked(iterable: Iterable[str], n: int) -> Iterable[List[str]]:
    batch = []
    for x in iterable:
        batch.append(x)
        if len(batch) == n:
            yield batch
            batch = []
    if batch:
        yield batch

def write_fasta_text(text: str, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    with open(out_path, "w") as f:
        f.write(text)

def ungzip_to_path(content: bytes, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    with gzip.open(io.BytesIO(content), "rb") as gz:
        data = gz.read()
    with open(out_path, "wb") as f:
        f.write(data)

def dedupe_fasta_by_sequence(in_path: Path, out_path: Optional[Path] = None) -> Path:
    out_path = out_path or in_path
    if SeqIO is None:
        return in_path
    seen = set()
    records = []
    for rec in SeqIO.parse(str(in_path), "fasta"):
        seq = str(rec.seq)
        h = hashlib.md5(seq.encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            records.append(rec)
    with open(out_path, "w") as handle:
        SeqIO.write(records, handle, "fasta")
    return out_path


# ---------- Config and Base Class ----------

@dataclass
class ExtractionConfig:
    output_dir: Path = Path("extracted_fastas")
    reviewed_only: bool = False
    email: Optional[str] = None
    dedupe_sequences: bool = True
    max_retries: int = 3
    sleep_between: float = 0.34


class BaseExtractor:
    def __init__(self, cfg: ExtractionConfig):
        self.cfg = cfg

    def _request(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, stream=False) -> requests.Response:
        tries = 0
        last = None
        while tries < self.cfg.max_retries:
            try:
                r = requests.get(url, params=params, headers=headers, timeout=60, stream=stream)
                if r.status_code == 200:
                    return r
                last = r
            except Exception as e:
                last = e
            time.sleep(self.cfg.sleep_between * (tries + 1))
            tries += 1
        if isinstance(last, requests.Response):
            last.raise_for_status()
        raise RuntimeError(f"Failed GET {url}: {last}")


# ---------- UniProt Fetcher ----------

class UniProtFetcher(BaseExtractor):
    SEARCH_URL = "https://rest.uniprot.org/proteomes/search"
    STREAM_URL = "https://rest.uniprot.org/uniprotkb/stream"
    UNIPARC_URL = "https://rest.uniprot.org/uniparc/proteome/{proteome_id}/stream"

    def fetch_proteomes(self, inputs: Iterable[str]) -> List[Dict]:
        """
        Fetch proteomes from UniProt by organism name or proteome ID.
        - Does NOT save any summary CSV.
        - Renames files to the matched organism name, even for proteome IDs.
        """
        ensure_dir(self.cfg.output_dir)
        results = []

        for org in inputs:
            org = org.strip()
            if not org:
                continue

            # --- Step 1: Resolve organism and proteome ID ---
            if re.match(r"UP\d{9}", org):
                proteome_id = org
                sci_name = None
                # try fetching metadata for this proteome ID
                try:
                    meta_resp = self._request(self.SEARCH_URL, params={"query": proteome_id})
                    data = meta_resp.json()
                    if data.get("results"):
                        first = data["results"][0]
                        sci_name = first["taxonomy"]["scientificName"]
                    else:
                        sci_name = proteome_id
                except Exception:
                    sci_name = proteome_id
            else:
                # search by organism name
                try:
                    resp = self._request(self.SEARCH_URL, params={"query": org})
                    data = resp.json()
                    if not data.get("results"):
                        print(f"[WARN] No proteome found for {org}")
                        results.append({"Input": org, "Status": "Not found"})
                        continue
                    first = data["results"][0]
                    proteome_id = first["id"]
                    sci_name = first["taxonomy"]["scientificName"]
                except Exception as e:
                    print(f"[ERROR] Search error for {org}: {e}")
                    results.append({"Input": org, "Status": f"Search error: {e}"})
                    continue

            # --- Step 2: Build file name (always use organism) ---
            file_basename = sanitize_name(sci_name or proteome_id)
            out_path = self.cfg.output_dir / f"{file_basename}.fasta"

            if out_path.exists():
                print(f"[INFO] Skipping existing {out_path.name}")
                continue

            # --- Step 3: Fetch proteome FASTA ---
            params = {"query": f"proteome:{proteome_id}", "format": "fasta"}
            if self.cfg.reviewed_only:
                params["query"] += " AND (reviewed:true)"

            try:
                fasta_resp = self._request(self.STREAM_URL, params=params)
                if not fasta_resp.text.strip():
                    print(f"[WARN] Empty FASTA for {org}")
                    results.append({"Input": org, "Status": "Empty file"})
                    
                write_fasta_text(fasta_resp.text, out_path)

                if self.cfg.dedupe_sequences:
                    dedupe_fasta_by_sequence(out_path, out_path)

                results.append({
                    "Input": org,
                    "Matched Organism": sci_name,
                    "Proteome ID": proteome_id,
                    "FASTA File": str(out_path),
                    "Status": "Downloaded",
                })
                print(f"[OK] Saved {out_path.name}")

            except Exception as e:
                print(f"[ERROR] Failed for {org}: {e}")
                results.append({"Input": org, "Status": f"Error: {e}"})

        return results

    def fetch_uniparc_proteomes(self, proteome_ids: Iterable[str], organism_names: Optional[Iterable[str]] = None) -> pd.DataFrame:
        ensure_dir(self.cfg.output_dir)
        results = []
        proteome_ids = list(proteome_ids)
        organism_names = list(organism_names) if organism_names else [None] * len(proteome_ids)

        for idx, pid in enumerate(proteome_ids):
            pid = pid.strip()
            if not pid:
                continue
            fname_gz = f"{pid}.fasta.gz"
            gz_path = self.cfg.output_dir / fname_gz
            if gz_path.exists():
                continue

            url = self.UNIPARC_URL.format(proteome_id=pid)
            params = {"compressed": "False", "format": "fasta"}
            try:
                r = self._request(url, params=params)
                if not r.content or len(r.content) == 0:
                    results.append({"Proteome ID": pid, "Status": "Empty file"})
                    continue
                with open(gz_path, "wb") as f:
                    f.write(r.content)
                if gz_path.stat().st_size == 0:
                    gz_path.unlink(missing_ok=True)
                    continue

                fasta_path = gz_path.with_suffix("")
                gz_path.rename(fasta_path)
                organism = organism_names[idx]
                if organism:
                    new_name = sanitize_name(organism) + ".fasta"
                    new_path = self.cfg.output_dir / new_name
                    fasta_path.rename(new_path)
                    fasta_path = new_path
                if self.cfg.dedupe_sequences:
                    dedupe_fasta_by_sequence(fasta_path, fasta_path)
                results.append({
                    "Proteome ID": pid,
                    "Organism": organism,
                    "FASTA File": str(fasta_path),
                    "Status": "Downloaded"
                })
                print(f"[OK] Saved {fasta_path.name}")
            except Exception as e:
                results.append({"Proteome ID": pid, "Status": f"Error: {e}"})

        return results




class EnsemblFungiFetcher(BaseExtractor):
    """
    Fetch proteomes from Ensembl Fungi (via rsync).
    Requires rsync installed and network access to Ensembl FTP.
    """

    ENSEMBL_REST = "https://rest.ensembl.org"
    ENSEMBL_FTP_BASE = "rsync://ftp.ensemblgenomes.org/pub/current_fasta/fungi"

    def _get_species_list(self) -> List[str]:
        """Fetch all available species in Ensembl Fungi division."""
        url = f"{self.ENSEMBL_REST}/info/species"
        params = {"division": "EnsemblFungi"}
        r = self._request(url, params=params, headers={"Content-Type": "application/json"})
        data = r.json()
        return [s["name"] for s in data.get("species", [])]

    def fetch_proteomes(self, species_list: Iterable[str]) -> List[Dict]:
        ensure_dir(self.cfg.output_dir)
        available_species = set(self._get_species_list())
        results = []

        for species in species_list:
            species = species.strip().lower().replace(" ", "_")
            if not species:
                continue

            if species not in available_species:
                print(f"[WARN] {species} not found in Ensembl Fungi.")
                results.append({"Species": species, "Status": "Not found"})
                continue

            remote_path = f"{self.ENSEMBL_FTP_BASE}/{species}/pep/"
            local_path = self.cfg.output_dir / species
            ensure_dir(local_path)

            print(f"[INFO] Downloading Ensembl Fungi proteome for {species}...")
            try:
                subprocess.run(["rsync", "-av", remote_path, str(local_path)], check=True)
                print(f"[OK] Finished {species}")

                # Find .pep.all.fa.gz or .fa.gz file
                fasta_files = list(local_path.glob("*.fa.gz"))
                if not fasta_files:
                    results.append({"Species": species, "Status": "No FASTA found"})
                    continue

                # Unzip and rename to species.fasta
                for gz in fasta_files:
                    out_path = self.cfg.output_dir / f"{sanitize_name(species)}.fasta"
                    ungzip_to_path(gz.read_bytes(), out_path)
                    if self.cfg.dedupe_sequences:
                        dedupe_fasta_by_sequence(out_path, out_path)
                    results.append({
                        "Species": species,
                        "FASTA File": str(out_path),
                        "Status": "Downloaded"
                    })
                    print(f"[OK] Saved {out_path.name}")

            except subprocess.CalledProcessError as e:
                print(f"[ERROR] rsync failed for {species}: {e}")
                results.append({"Species": species, "Status": f"rsync error: {e}"})

        return results




class NCBIFetcher(BaseExtractor):
    """
    Fetch proteomes from NCBI using NCBI Datasets CLI.
    Requires: 'datasets' and 'unzip' installed, and valid Entrez email.
    """

    def __init__(self, cfg: ExtractionConfig):
        super().__init__(cfg)
        if Entrez is None:
            raise ImportError("Biopython (Bio.Entrez) is required for NCBI fetching.")
        if not cfg.email:
            raise ValueError("NCBI requires a valid email in ExtractionConfig.email.")
        Entrez.email = cfg.email

    def _get_taxid(self, species_name: str) -> Optional[str]:
        """Fetch NCBI taxonomy ID for a species name."""
        handle = Entrez.esearch(db="taxonomy", term=species_name)
        record = Entrez.read(handle)
        handle.close()
        return record["IdList"][0] if record["IdList"] else None

    def fetch_proteomes(self, species_list: Iterable[str]) -> List[Dict]:
        ensure_dir(self.cfg.output_dir)
        results = []

        for species in species_list:
            species = species.strip()
            if not species:
                continue

            taxid = self._get_taxid(species)
            if not taxid:
                print(f"[WARN] No TaxID found for {species}")
                results.append({"Species": species, "Status": "TaxID not found"})
                continue

            species_safe = sanitize_name(species)
            zip_path = self.cfg.output_dir / f"{species_safe}_proteins.zip"
            extract_dir = self.cfg.output_dir / species_safe

            if extract_dir.exists():
                print(f"[INFO] Skipping {species} (already downloaded)")
                continue

            cmd = [
                "datasets", "download", "genome",
                "taxon", str(taxid),
                "--include", "protein",
                "--filename", str(zip_path),
            ]

            try:
                print(f"[INFO] Downloading NCBI proteome for {species} (TaxID {taxid})...")
                subprocess.run(cmd, check=True)

                ensure_dir(extract_dir)
                subprocess.run(["unzip", "-o", str(zip_path), "-d", str(extract_dir)], check=True)

                # Locate and copy protein.faa
                protein_path = None
                for dirpath, _, filenames in os.walk(extract_dir):
                    if "protein.faa" in filenames:
                        protein_path = Path(dirpath) / "protein.faa"
                        break

                if protein_path:
                    out_path = self.cfg.output_dir / f"{species_safe}.fasta"
                    shutil.copy2(protein_path, out_path)
                    if self.cfg.dedupe_sequences:
                        dedupe_fasta_by_sequence(out_path, out_path)
                    results.append({
                        "Species": species,
                        "TaxID": taxid,
                        "FASTA File": str(out_path),
                        "Status": "Downloaded"
                    })
                    print(f"[OK] Saved {out_path.name}")
                else:
                    print(f"[WARN] No protein.faa found for {species}")
                    results.append({"Species": species, "Status": "No protein.faa"})

            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to download {species}: {e}")
                results.append({"Species": species, "Status": f"datasets error: {e}"})

        return results
