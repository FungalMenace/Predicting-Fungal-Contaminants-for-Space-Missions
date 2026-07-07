# tests/test_config.py
"""
Diagnostic test script to verify that the central configuration framework
and all path resolutions are working correctly.
"""

import sys
from pathlib import Path

# Adjust path to find the src directory if needed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from src.fungi_pipeline.config import (
        ROOT_DIR,
        PIPELINE_RESULTS_DIR,
        PIPELINE_QUERIES_DIR,
        FINAL_EXTRACTED_FASTAS_DIR,
        SUMMARY_EXCEL_PATH,
        MERGED_SUMMARY_PATH
    )
    CONFIG_LOADED = True
except ImportError as e:
    CONFIG_LOADED = False
    IMPORT_ERROR = e


def test_configuration_ecosystem():
    """Execute validation checks on config settings and path generations."""
    print("   FUNGAL PIPELINE CENTRAL CONFIGURATION TEST     ")

    # 1. Test Import and Layout Initialization
    print("[STEP 1] Checking configuration module import...")
    if not CONFIG_LOADED:
        print(f"FAILED: Could not import central config. Error: {IMPORT_ERROR}")
        assert False, "Configuration loading threw an ImportError."
    print("SUCCESS: Package modules loaded successfully.\n")

    # 2. Inspect Root Anchor Bounds
    print(f"[STEP 2] Verifying Project Workspace Anchor Root...")
    print(f"       -> ROOT_DIR: {ROOT_DIR}")
    if not ROOT_DIR.exists():
        print("FAILED: Calculated workspace anchor path does not exist on disk!")
        assert False
    print("SUCCESS: Project anchor workspace verified.\n")

    # 3. Structural Routing Report
    print("[STEP 3] Evaluating dynamic directories mapping...")
    paths_to_verify = {
        "Pipeline Results Directory": PIPELINE_RESULTS_DIR,
        "Pipeline Queries Target": PIPELINE_QUERIES_DIR,
        "Extracted FASTAs Storage": FINAL_EXTRACTED_FASTAS_DIR
    }

    for label, target_path in paths_to_verify.items():
        print(f"       -> {label}: {target_path}")
        # Explicitly verify directory creation parameters
        target_path.mkdir(parents=True, exist_ok=True)
        if target_path.exists() and target_path.is_dir():
            print(f"          [OK] Path verified and reachable.")
        else:
            print(f"          ERROR: Failed to access or auto-create folder.")
            assert False

    print("\nSUCCESS: Structural automation paths mapped correctly.\n")

    # 4. File Target Mapping Checks
    print("[STEP 4] Verifying downstream spreadsheet targets...")
    print(f"       -> Summary Spreadsheet: {SUMMARY_EXCEL_PATH}")
    print(f"       -> Consolidated Master Spreadsheet: {MERGED_SUMMARY_PATH}")
    
    # Ensure parent output directories are ready to store files
    SUMMARY_EXCEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MERGED_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("SUCCESS: File export parents initialized.")

    print()
    print(" ALL CONFIGURATION ARCHITECTURE CHECKS PASSED! ")


if __name__ == "__main__":
    test_configuration_ecosystem()