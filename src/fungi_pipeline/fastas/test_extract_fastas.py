"""
test_extract_fastas.py

Sample commands:
----------------
# Fetch UniProt proteomes
python test_extract_fastas.py --uniprot

# Fetch UniParc proteomes
python test_extract_fastas.py --uniparc

# Fetch Ensembl Fungi proteomes
python test_extract_fastas.py --ensembl

# Fetch NCBI proteomes (requires valid email)
python test_extract_fastas.py --ncbi --email your_email@example.com

# Fetch from multiple sources at once
python test_extract_fastas.py --uniprot --ensembl --ncbi --email your_email@example.com
"""

import argparse
from pathlib import Path
from src.fungi_pipeline.fastas.extract_fastas import (
    ExtractionConfig,
    UniProtFetcher,
    EnsemblFungiFetcher,
    NCBIFetcher,
)


def main():
    parser = argparse.ArgumentParser(description="Test fungal FASTA extraction from multiple sources")

    parser.add_argument(
        "--output_dir", type=Path, default=Path("extracted_fastas"),
        help="Output directory for extracted FASTAs"
    )
    parser.add_argument(
        "--reviewed-only", action="store_true",
        help="Only download reviewed (Swiss-Prot) entries for UniProt"
    )
    parser.add_argument(
        "--email", type=str, default=None,
        help="Valid email for NCBI Entrez (required for NCBI fetcher)"
    )
    parser.add_argument("--uniprot", action="store_true", help="Fetch UniProt proteomes")
    parser.add_argument("--uniparc", action="store_true", help="Fetch UniParc proteomes")
    parser.add_argument("--ensembl", action="store_true", help="Fetch Ensembl Fungi proteomes")
    parser.add_argument("--ncbi", action="store_true", help="Fetch NCBI proteomes")

    args = parser.parse_args()

    cfg = ExtractionConfig(
        output_dir=args.output_dir,
        reviewed_only=args.reviewed_only,
        email=args.email,
    )

    # --- UniProt ---
    if args.uniprot:
        fetcher = UniProtFetcher(cfg)
        organisms = ["Candida albicans", "Aspergillus fumigatus", "UP000002311"]
        print("\n[TEST] Fetching UniProt proteomes...")
        fetcher.fetch_proteomes(organisms)

    # --- UniParc ---
    if args.uniparc:
        fetcher = UniProtFetcher(cfg)
        proteome_ids = ["UP000002311", "UP000001940"]
        organism_names = ["Candida albicans", "Aspergillus fumigatus"]
        print("\n[TEST] Fetching UniParc proteomes...")
        fetcher.fetch_uniparc_proteomes(proteome_ids, organism_names)

    # --- Ensembl Fungi ---
    if args.ensembl:
        fetcher = EnsemblFungiFetcher(cfg)
        species = ["candida_albicans", "aspergillus_fumigatus"]
        print("\n[TEST] Fetching Ensembl Fungi proteomes...")
        fetcher.fetch_proteomes(species)

    # --- NCBI ---
    if args.ncbi:
        if not args.email:
            parser.error("--email is required for NCBI fetcher.")
        fetcher = NCBIFetcher(cfg)
        species = ["Nectria haematococca", "Candida albicans"]
        print("\n[TEST] Fetching NCBI proteomes...")
        fetcher.fetch_proteomes(species)


if __name__ == "__main__":
    main()
