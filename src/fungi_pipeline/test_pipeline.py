"""
Unit tests for pipeline.py (fungal analysis pipeline).

These tests mock external dependencies so that:
- No real downloads, API calls, or BLASTs occur.
- File operations run safely in temp directories.

Run with:
    pytest -v test_pipeline.py
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd
import tempfile
import os

from src.fungi_pipeline.pipeline import PipelineManager, main



@pytest.fixture
def temp_base_dir(tmp_path):
    """Temporary directory for pipeline I/O."""
    (tmp_path / "results").mkdir()
    (tmp_path / "fastas").mkdir()
    return tmp_path


@pytest.fixture
def mock_excel_file(tmp_path):
    """Create a fake Excel file with expected structure."""
    df = pd.DataFrame({
        ("Organism", "", "", ""): ["Candida albicans", "Aspergillus fumigatus"],
        ("A-score", "", "", ""): [4, 6]
    })
    excel_path = tmp_path / "fungal_summary.xlsx"
    with pd.ExcelWriter(excel_path) as writer:
        df.to_excel(writer, sheet_name="BLAST Summary", index=False)
    return excel_path




@patch("pipeline.UniProtFetcher")
def test_extract_fastas(mock_fetcher, temp_base_dir):
    args = MagicMock(base_dir=temp_base_dir, excel=None)
    pm = PipelineManager(args)
    pm.extract_fastas()
    mock_fetcher.assert_called_once()
    print("FASTA extraction test passed.")


@patch("pipeline.FungalBlastPipeline")
def test_run_blast(mock_blast, temp_base_dir):
    args = MagicMock(base_dir=temp_base_dir, excel=None)
    pm = PipelineManager(args)
    mock_blast.return_value.run.return_value = {"dummy": "result"}
    pm.run_blast()
    mock_blast.assert_called_once()
    print("BLAST run test passed.")


@patch("pipeline.generate_excel")
@patch("pipeline.read_blast_results", return_value=(None, None, None))
def test_create_excel(mock_read, mock_gen, temp_base_dir):
    args = MagicMock(base_dir=temp_base_dir, excel=None)
    pm = PipelineManager(args)
    pm.create_excel()
    mock_read.assert_called_once()
    mock_gen.assert_called_once()
    print("Excel creation test passed.")


@patch("pipeline.get_phylum", side_effect=["Ascomycota", "Basidiomycota"])
@patch("pandas.read_excel")
def test_identify_phyla(mock_read_excel, mock_get_phylum, mock_excel_file, temp_base_dir):
    df = pd.DataFrame({
        "Organism": ["Candida albicans", "Aspergillus fumigatus"],
        "A-score": [4, 6]
    })
    mock_read_excel.return_value = df

    args = MagicMock(base_dir=temp_base_dir, excel=mock_excel_file)
    pm = PipelineManager(args)
    pm.identify_phyla()

    mock_get_phylum.assert_any_call("Candida albicans")
    mock_get_phylum.assert_any_call("Aspergillus fumigatus")

    out_path = mock_excel_file.with_name("fungal_summary_with_phyla.xlsx")
    assert out_path.exists()
    df_out = pd.read_excel(out_path)
    assert "Phylum" in df_out.columns
    print("Phyla identification test passed.")


@patch("pipeline.plot_category")
@patch("pipeline.plot_a_scores")
@patch("pipeline.plot_s_scores")
@patch("pipeline.plot_category_counts")
@patch("pandas.read_excel")
def test_generate_plots(mock_read_excel, mock_cat, mock_a, mock_s, mock_counts, mock_excel_file, temp_base_dir):
    df = pd.DataFrame({"Organism": ["Candida albicans"], "A-score": [5]})
    mock_read_excel.return_value = df

    args = MagicMock(base_dir=temp_base_dir, excel=mock_excel_file)
    pm = PipelineManager(args)
    pm.generate_plots()

    mock_cat.assert_called()
    mock_a.assert_called_once()
    mock_s.assert_called_once()
    mock_counts.assert_called_once()
    print("Plot generation test passed.")



@patch("pipeline.PipelineManager.extract_fastas")
@patch("pipeline.PipelineManager.run_blast")
@patch("pipeline.PipelineManager.create_excel")
@patch("pipeline.PipelineManager.identify_phyla")
@patch("pipeline.PipelineManager.generate_plots")
def test_main_cli(mock_p5, mock_p4, mock_p3, mock_p2, mock_p1, tmp_path):
    """Test CLI flow end-to-end with patched methods."""
    test_args = ["pipeline.py", "--base_dir", str(tmp_path), "--from", "1", "--to", "5"]

    with patch("sys.argv", test_args):
        main()

    mock_p1.assert_called_once()
    mock_p2.assert_called_once()
    mock_p3.assert_called_once()
    mock_p4.assert_called_once()
    mock_p5.assert_called_once()
    print("CLI full-run test passed.")
