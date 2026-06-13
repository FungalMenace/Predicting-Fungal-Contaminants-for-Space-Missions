# Extending the Pipeline (General Use)

This pipeline is highly modular and designed to be easily extensible. You can use it to evaluate your own lists of fungal organisms, or screen for entirely different sets of target proteins (e.g., proteins associated with different extreme environments or novel pathogenicity factors).

## 1. Adding Custom Fungal Proteomes

To analyze a new set of fungi, you just need their `.fasta` proteome files.

1. **Prepare your FASTAs:** Ensure your proteome files are in standard FASTA format (`.fasta` or `.faa`).
2. **Create a target directory:** Place all your custom FASTA files into a single directory. For example: `custom_fastas/`
3. **Run the pipeline:** Run the master pipeline script, pointing it to your custom directory using the `--proteomes_dir` argument.
   ```bash
   python -m src.fungi_pipeline.pipeline --steps 2,4 --proteomes_dir custom_fastas

    ```

*(Note: Skipping step 1 bypasses the JGI/UniProt extraction scripts, moving straight to BLAST and scoring).*

## 2. Using Custom Query Proteins

Our study screened against 25 specific stress-resistance proteins. To screen for your own proteins of interest:

1. **Locate the query directory:** The pipeline expects query proteins to be located in `data/proteomes/queries/`.
2. **Add your sequences:** Save your target proteins in standard FASTA format and place them in this directory.
3. **Update scoring (optional):** If you add new categories of proteins, you may want to update the `PROTEIN_CATEGORY` mappings in `src/fungi_pipeline/plots/plots.py` so the visualizations reflect your custom categories.
4. **Execute:** Run the pipeline normally. The BLAST automation (`runner.py`) will automatically align against any `.fasta` files present in the queries folder.

## 3. Changing Scoring Thresholds

By default, our identity threshold ($I$) for ortholog consideration is 35%, and high-scoring hits require $\ge 75\%$. If you need to make the pipeline more or less stringent for your specific use case, you can adjust the `identity_threshold` parameter passed to the `FungalBlastPipeline` class inside `src/pipeline.py`.
