# src/fungi_pipeline/config.py
import yaml
from pathlib import Path

# Traverse upwards to automatically find the project root directory
_current_path = Path(__file__).resolve()
ROOT_DIR = None
for parent in _current_path.parents:
    if (parent / "config.yml").exists():
        ROOT_DIR = parent
        break

if not ROOT_DIR:
    raise FileNotFoundError("Could not locate the project root containing 'config.yml'.")

# Load YAML configuration
with open(ROOT_DIR / "config.yml", "r") as file:
    _config = yaml.safe_load(file)

# --- JGI Pipeline Paths ---
DATA_PATH = ROOT_DIR / _config['paths']['gold_csv']
PROJECT_METADATA_CSV = ROOT_DIR / _config['paths']['genome-projects.csv']
OUTPUT_DIR = ROOT_DIR / _config['paths']['genome_fastas_out']
MAPPINGS_JSON = ROOT_DIR / _config['paths']['jgi_portal_mappings.json']

# --- NCBI Pipeline Paths ---
NCBI_INPUT_FILE = ROOT_DIR / _config['paths']['ncbi_input_txt']
NCBI_TEMP_DIR = ROOT_DIR / _config['paths']['ncbi_temp_dir']
NCBI_FINAL_DIR = ROOT_DIR / _config['paths']['ncbi_final_dir']

# --- UniProt Pipeline Paths ---
UNIPROT_TSV = ROOT_DIR / _config['paths']['uniprot_tsv']
MATRIX_XLSX = ROOT_DIR / _config['paths']['matrix_xlsx']
UNIPROT_FASTAS_DIR = ROOT_DIR / _config['paths']['uniprot_fastas_out']
UNIPARC_FASTAS_DIR = ROOT_DIR / _config['paths']['uniparc_fastas_out']

# --- OrthoDB & BLAST Pipeline Paths ---
ORTHODB_BASE_DIR = ROOT_DIR / _config['paths']['orthodb_base_dir']
ORTHODB_FASTAS_DIR = ROOT_DIR / _config['paths']['orthodb_fastas_dir']
ORTHODB_CSVS_DIR = ROOT_DIR / _config['paths']['orthodb_csvs_dir']
ORTHODB_TSVS_DIR = ROOT_DIR / _config['paths']['orthodb_tsvs_dir']
ORTHODB_BLAST_DB = ROOT_DIR / _config['paths']['orthodb_blast_db']
ORTHODB_EXCEL_PATH = ROOT_DIR / _config['paths']['orthodb_excel_out']

# --- Plotting & Reporting Pipeline Paths ---
SUMMARY_EXCEL_PATH = ROOT_DIR / _config['paths']['summary_excel']
PLOTS_EXPORT_DIR = ROOT_DIR / _config['paths']['plots_export_dir']

# --- Pipeline Framework Paths ---
PIPELINE_RESULTS_DIR = ROOT_DIR / _config['paths'].get('pipeline_results_dir', 'src/results')
PIPELINE_QUERIES_DIR = ROOT_DIR / _config['paths'].get('pipeline_queries_dir', 'data/proteomes/queries')
MERGED_SUMMARY_PATH = ROOT_DIR / _config['paths'].get('merged_summary_excel', 'src/results/merged_summary.xlsx')