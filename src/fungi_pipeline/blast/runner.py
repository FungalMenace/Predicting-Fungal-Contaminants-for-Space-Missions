"""
Usage:
    python runner.py \
        --query_fasta_dir ./queries \
        --proteome_dir ./proteomes \
        --output_dir ./results \
        --identity_threshold 35 \
        --threads 8
"""

import argparse
import subprocess
from pathlib import Path
from typing import List
from dataclasses import dataclass, asdict
import csv
from Bio import SeqIO
import re
import pandas as pd
from io import StringIO


@dataclass 
class BlastResult:
    protein: str           # query file name (without _query.fasta)
    subject_id: str
    pident: float
    evalue: float
    bitscore: float
    organism: str
    subject_protein: str = None
    query_seq: str = None
    subject_seq: str = None
    alignment: str = None


class FungalBlastPipeline:
    """
    Fungal BLAST pipeline:
      1. Build BLAST databases
      2. Run BLASTp in memory (no intermediate files)
      3. Annotate with subject protein names
      4. Include full query and subject sequences
      5. Save per-organism and combined CSVs
    """

    def __init__(
        self,
        query_fasta_dir: str,
        proteome_dir: str,
        output_dir: str,
        identity_threshold: float = 35.0,
        threads: int = 4,
    ):
        self.query_fasta_dir = Path(query_fasta_dir)
        self.proteome_dir = Path(proteome_dir)
        self.output_dir = Path(output_dir)
        self.identity_threshold = identity_threshold
        self.threads = threads

        self.output_dir.mkdir(parents=True, exist_ok=True)

    # --- Create BLAST database ---
    def make_blast_db(self, proteome_path: Path) -> Path:
        db_path = proteome_path.with_suffix("")
        cmd = [
            "makeblastdb",
            "-in", str(proteome_path),
            "-dbtype", "prot",
            "-out", str(db_path),
        ]
        subprocess.run(cmd, check=True)
        return db_path

    # --- Run BLASTp (with matched subsequences) ---
    def run_blastp(self, query_fasta: Path, db_path: Path) -> str:
        # Include matched sequence fragments (qseq and sseq)
        cmd = [
            "blastp",
            "-query", str(query_fasta),
            "-db", str(db_path),
            "-outfmt", "6 qseqid sseqid pident evalue bitscore qseq sseq",
            "-num_threads", str(self.threads),
            "-max_target_seqs", "5",
        ]
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True)
        return result.stdout

    # --- Parse BLAST results ---
    def parse_blast_results(
        self,
        blast_output_text: str,
        organism_name: str,
        proteome_fasta: Path,
        query_name: str,
        duplicates: bool = False,
    ) -> List[BlastResult]:
        if not blast_output_text.strip():
            return []

        df = pd.read_csv(
            StringIO(blast_output_text),
            sep="\t",
            names=[
                "qseqid", "subject_id", "pident",
                "evalue", "bitscore", "matched_query", "matched_subject"
            ],
        )

        # --- Load query and subject sequences (complete) ---
        query_fasta_path = self.query_fasta_dir / f"{query_name}_query.fasta"
        query_seq_map = {rec.id: str(rec.seq) for rec in SeqIO.parse(query_fasta_path, "fasta")}
        subject_seq_map = {rec.id: str(rec.seq) for rec in SeqIO.parse(proteome_fasta, "fasta")}

        # --- Build subject protein name mapping ---
        protein_map = {}
        for record in SeqIO.parse(proteome_fasta, "fasta"):
            header = record.description
            match = re.search(r'^[^\s]+\s+(.*?)\s+OS=', header)
            if match:
                protein_name = match.group(1)
            else:
                protein_name = header.split(" ", 1)[1] if " " in header else header
            protein_map[record.id] = protein_name

        def get_protein_name(id_value):
            if id_value in protein_map:
                return protein_map[id_value]
            for key, prot in protein_map.items():
                if id_value in key or id_value in prot:
                    return prot
            return None

        df["subject_protein"] = df["subject_id"].apply(get_protein_name)

        # --- Filter duplicates (keep best per query) ---
        if not duplicates:
            df = (
                df.sort_values(by="pident", ascending=False)
                .drop_duplicates(subset="qseqid", keep="first")
                .reset_index(drop=True)
            )

        # --- Construct result objects ---
        results = []
        for _, row in df.iterrows():
            qid = row["qseqid"]
            sid = row["subject_id"]
            full_query = query_seq_map.get(qid, "")
            full_subject = subject_seq_map.get(sid, "")
            alignment = (
                f"Query match: {row['matched_query']}\n"
                f"Subject match: {row['matched_subject']}"
            )

            results.append(
                BlastResult(
                    protein=query_name,
                    subject_id=sid,
                    pident=row["pident"],
                    evalue=row["evalue"],
                    bitscore=row["bitscore"],
                    organism=organism_name,
                    subject_protein=row["subject_protein"],
                    query_seq=full_query,
                    subject_seq=full_subject,
                    alignment=alignment,
                )
            )

        return results

    # --- Save results to CSV ---
    def save_results(self, results: List[BlastResult], output_csv: Path) -> None:
        if not results:
            print(f"[WARN] No BLAST results to save for {output_csv.stem}")
            return

        output_csv.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "protein", "subject_id", "pident", "evalue", "bitscore",
            "organism", "subject_protein", "query_seq", "subject_seq", "alignment"
        ]
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(asdict(r))

        print(f"[INFO] Results saved to {output_csv}")

    # --- Directory sanity checks ---
    def run_path_tests(self) -> None:
        if not self.query_fasta_dir.exists() or not self.query_fasta_dir.is_dir():
            raise FileNotFoundError(f"Query FASTA directory not found: {self.query_fasta_dir}")
        if not self.proteome_dir.exists() or not self.proteome_dir.is_dir():
            raise FileNotFoundError(f"Proteome directory not found: {self.proteome_dir}")
        if not any(self.query_fasta_dir.glob("*.fasta")):
            raise FileNotFoundError(f"No FASTA files found in query directory: {self.query_fasta_dir}")
        if not any(self.proteome_dir.glob("*.fasta")):
            raise FileNotFoundError(f"No FASTA files found in proteome directory: {self.proteome_dir}")

    # --- Run full pipeline ---
    def run(self, duplicates: bool = False) -> None:
        self.run_path_tests()
        all_combined = []

        for proteome_fasta in self.proteome_dir.glob("*.fasta"):
            organism = proteome_fasta.stem
            db_path = self.make_blast_db(proteome_fasta)
            combined_results = []

            for query_fasta in self.query_fasta_dir.glob("*.fasta"):
                query_name = query_fasta.stem.replace("_query", "")
                blast_output_text = self.run_blastp(query_fasta, db_path)
                parsed = self.parse_blast_results(
                    blast_output_text,
                    organism,
                    proteome_fasta,
                    query_name=query_name,
                    duplicates=duplicates,
                )
                combined_results.extend(parsed)
                all_combined.extend(parsed)

            # Save organism-specific CSV
            output_csv = self.output_dir / f"{organism}_blast_results.csv"
            self.save_results(combined_results, output_csv)

        # Save combined CSV across all organisms
        all_csv = self.output_dir / "all_results.csv"
        self.save_results(all_combined, all_csv)
        print(f"[INFO] Combined CSV saved to {all_csv}")
        print(f"[INFO] Pipeline completed. Final results are in: {self.output_dir}")


# --- Command line entry point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run fungal BLAST pipeline")
    parser.add_argument("--query_fasta_dir", required=True, help="Path to query FASTA directory")
    parser.add_argument("--proteome_dir", required=True, help="Path to proteome FASTA directory")
    parser.add_argument("--output_dir", required=True, help="Directory to save results")
    parser.add_argument("--identity_threshold", type=float, default=35.0, help="Minimum percent identity")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads for BLAST")
    parser.add_argument("--duplicates", action="store_true", help="Keep duplicate hits per query")

    args = parser.parse_args()
    pipeline = FungalBlastPipeline(
        args.query_fasta_dir,
        args.proteome_dir,
        args.output_dir,
        identity_threshold=args.identity_threshold,
        threads=args.threads,
    )
    pipeline.run(duplicates=args.duplicates)
