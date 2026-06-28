# Reproducing the Paper Results

This guide provides step-by-step instructions to completely reproduce the results, matrices, and plots presented in the paper *"Predicting Fungal Contaminants for Space Missions Using Proteome-Wide Screening for Protein Orthologs"*.

## Prerequisites
Before starting, ensure you have completed the installation steps in the [Main README](../README.md).
* **Credentials:** To extract data from the JGI Genome Portal, you must have a valid JGI account. Export your credentials as environment variables:
  ```bash
  export JGI_USERNAME="your_username"
  export JGI_PASSWORD="your_password"
    ```

* **Query Proteins:** Ensure the FASTA files for the 25 target stress-resistance proteins are placed in the appropriate query directory (contact the authors for the exact reference query set if needed).

---

## Step 1: Extract and Merge FASTAs

The 1583 fungal organisms in our dataset are distributed across multiple databases. We must extract them sequentially.
*(Note: If you downloaded the pre-compiled FASTA files via the Caltech Library DOI linked in the main README, you can skip to Step 2).*

**1a. Extract from JGI Genome Portal (GOLD species list):**

```bash
python -m src.fungi_pipeline.fastas.genome_fastas

```

*(Outputs to: `src/fungi_pipeline/fastas/genome_fastas`)*

**1b. Extract from NCBI Portal:**

```bash
python -m src.fungi_pipeline.fastas.ncbi_fastas

```

*(Outputs to: `src/fungi_pipeline/fastas/ncbi_fastas`)*

**1c. Extract from UniProt (Proteomes and UniParc):**

```bash
python -m src.fungi_pipeline.fastas.uniprot_fastas

```

*(Outputs to: `src/fungi_pipeline/fastas/uniprot_fastas`)*

**1d. Merge all FASTAs into a single directory:**
Use the utility script to combine the output directories.

```bash
python -m src.fungi_pipeline.utils \
  --fastas src/fungi_pipeline/fastas/genome_fastas \
           src/fungi_pipeline/fastas/ncbi_fastas \
           src/fungi_pipeline/fastas/uniprot_fastas

```

This will generate a unified folder named `final_extracted_fastas/`.

`Google drive link containing fasta files`: https://drive.google.com/file/d/10jYxRd_zEn0Un9JdEQmP9L_zIFwuP0sy/view?usp=share_link

### 📝 Note on FASTA Retrieval and Database Mapping

The structure of our retrieved FASTA files differs depending on the database source, which dictates how the organisms map to the files.

* **Organism-Based Retrieval (1:1 Mapping):** For the majority of our sources (except OrthoDB), data was retrieved using **organism names**. This results in a straightforward 1:1 mapping where each organism has a single, dedicated `.fasta` file containing its complete proteome. 
* **Protein-Based Retrieval (OrthoDB):** Conversely, data from OrthoDB was retrieved using our **25 query proteins**. Instead of one file per organism, OrthoDB generated 25 FASTA files (one for each query protein). Each of these query-specific files contains orthologous protein sequences from *multiple* organisms.

**Example:**
Consider the organism *Aaosphaeria arxii CBS 175.79*, which was sourced via OrthoDB. It does not have a single dedicated proteome file. Instead, its sequences are distributed across the query protein files based on what it possesses:
* It shares 45% sequence identity with **CZF1**, so its orthologous protein sequence is located inside the `CZF1` OrthoDB FASTA file.
* It shares 86.5% sequence identity with **HSP90**, so it also has a sequence in the `HSP90` OrthoDB FASTA file.
* It lacks an **ERG11** ortholog (0% identity), so it has no corresponding sequence in the `ERG11` file.

---

## Step 2: BLASTp Automation and Initial Scoring

Run the core pipeline to perform BLASTp comparisons between the merged proteomes and the 25 query proteins. This step also generates the initial S-score and A-score summary.

```bash
python -m src.fungi_pipeline.pipeline --steps 2,3 --proteomes_dir final_extracted_fastas

```

* **What this does:** * Identifies orthologs based on identity and coverage thresholds.
* Creates an initial Excel matrix named `fungal_summary.xlsx` in the results directory.



---

## Step 3: Integrate OrthoDB Fungi

To include the additional fungal species retrieved via OrthoDB annotations, run the dedicated OrthoDB extraction script:

```bash
python -m src.fungi_pipeline.orthodb.get_orthologs

```

* **What this does:** Automatically queries OrthoDB and generates a secondary Excel file named `fungi_from_orthologs.xlsx` in the `orthodb_results` directory.

---

## Step 4: Combine Results into the Final Matrix

Merge the initial BLAST summary with the OrthoDB results to create the final, comprehensive scoring table used in the paper.

```bash
python -m src.fungi_pipeline.utils \
  --excels path_to_fungal_summary.xlsx path_to_fungi_from_orthologs.xlsx \
  --output final.xlsx

```

*(Replace the paths with the actual locations of your generated Excel files from Steps 2 and 3).* This generates the `final.xlsx` matrix containing the complete S-score and A-score data for all 1583 organisms.

---

## Step 5: Generate Final Plots

To generate the distribution plots, stacked bar charts, and category breakdowns presented in the paper, pass the final merged Excel file back into the plotting step of the pipeline.

```bash
python -m src.fungi_pipeline.pipeline --steps 3,4 --excel final.xlsx

```

* **What this does:** Parses the final matrix and saves all high-resolution figures (e.g., A-score distributions, S-score boxplots, phyla breakdowns) into the `plots/` directory.

---

**Troubleshooting:** Make sure you execute all commands from the root directory of the repository (`Fungi-Space-Contamination-Pipeline/`) so that all relative paths resolve correctly.
