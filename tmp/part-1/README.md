# Part 1 Changes

This document summarizes all changes made after the initial list of **1,583 fungal organisms**, corresponding to **Part 1** of `DATA_QUALITY_PUNCHLIST.md`.

## 1. Refetched Proteomes

All **30 proteomes** listed in **Part 1(a)** of `DATA_QUALITY_PUNCHLIST.md` were refetched from the best available source. Depending on availability, the proteomes were obtained from:

* NCBI
* UniProt
* UniParc (UPUP)

---

## 2. Updated BLAST Results

The refetched proteomes were reprocessed by running **BLASTP** against the **25 query proteins**.

The resulting identity scores have been updated in:

```text
tmp/part-1/fungi_organisms_and_proteins_revised_part_1.xlsx
```

---

## 3. Updated Plots

All plots were regenerated using the updated BLAST results.

Location:

```text
tmp/part-1/paper_plots_part1
```

---

## 4. Part 1(b) Organism Corrections

The following organism-specific corrections were made.

### 4.1 *Millerozyma farinosa*

* No issue was found with `Pichia_sorbitophila`.
* The proteome for `Millerozyma_farinosa` was refetched.

Additionally:

* The original list of 1,583 organisms contained **two entries**:

  * `Millerozyma farinosa`
  * `Millerozyma farinosa CBS 7064`
* These produce slightly different identity scores.
* `Millerozyma farinosa CBS 7064` originated from **OrthoDB**.
* This duplicate is **not removed in Part 1**.
* It is removed in **Part 2**, reducing the OrthoDB contribution from **169 → 168** organisms.

### 4.2 *Pneumocystis carinii*

* No issue was found with `Pneumocystis_murina`.
* The proteome for `Pneumocystis_carinii` was refetched.

### 4.3 *Saccharomyces bayanus*

* No issue was found with `Saccharomyces_uvarum`.
* A proteome for `Saccharomyces_bayanus` could not be found in any supported source.
* Therefore, `Saccharomyces_bayanus` has been removed from the dataset.

After this change, the organism count becomes **1,582** (before duplicate removal performed in Part 2).

---

## 5. Updated Proteome FASTA Files

The updated FASTA files (reflecting the refetched proteomes and updated sources) for the **1,582 organisms** are available at:

```text
https://drive.google.com/file/d/1L1xl-l6_Dsde8SoEGljtNBqvHiV_G5ic/view?usp=share_link
```

---

## 6. Updated `fungi_organisms_with_sequences_part1.csv`

Since several proteomes changed, the sequence extraction step was rerun and a new version of:

```text
fungi_organisms_with_sequences_part1.csv
```

was generated.

This file contains sequence data for **1,582 organisms × 25 query proteins**.

Google Drive link:

```text
https://drive.google.com/file/d/1aiRK8Y6yfYHd6jFLtkJ3Yw3Dwk-1aci5/view?usp=share_link
```

Please checkout part-2 readme next: `tmp/part-2/README.md`.