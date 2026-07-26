# Part 2 Changes (After Part 1)

This document summarizes all changes made **after the updates described in Part 1** (`tmp/part-1/README.md`).

The primary objective of Part 2 is to **identify and remove duplicate organisms** from the curated dataset.

> **Note:** Please read the Part 1 README before reading this document, as several decisions made in Part 2 depend on the changes introduced in Part 1.

---

## 1. Identification of Duplicate Organisms

The organisms to **keep** and **remove** were determined according to the instructions in **Part 2(a)** of `DATA_QUALITY_PUNCHLIST.md`.

Where the instruction was to keep the organism with the **latest taxonomic name** (`keep == taxonomy`), an LLM was used to identify the currently accepted taxonomic name.

---

## 2. Duplicate Organisms Removed

The following duplicate organisms were removed from the dataset:

```python
REMOVE = [
    "Acidomyces_sp",
    "Arthroderma_benhamiae",
    "Bipolaris_sorokiniana",
    "Bipolaris_zeicola",
    "Botryosphaeria_parva",
    "Botrytis_cinerea",
    "Candida_auris",
    "Cryptococcus_laurentii",
    "Dekkera_bruxellensis",
    "Emmonsia_sp",
    "Fusarium_verticillioides",
    "Gibberella_fujikuroi",
    "Kluyveromyces_polysporus",
    "Leucosporidium_scottii",
    "Mycosphaerella_eumusae",
    "Neosartorya_fischeri",
    "Nosema_apis",
    "Nosema_ceranae",
    "Paecilomyces_lilacinus",
    "Paraconiothyrium_sporulosum",
    "Phialocephala_scopiformis",
    "Rhodosporidium_toruloides",
    "Saccharomyces_pastorianus",
    "Scedosporium_apiospermum",
    "Sporothrix_insectorum",
    "Trametes_cinnabarina",
    "Tremellales_sp",
    "Trichosporon_oleaginosus",
]
```

### Note

Although **31 organisms** were listed for review in Part 2(a), only **28 organisms** appear in the removal list above.

The remaining three cases were already addressed during **Part 1(b)**:

* `Saccharomyces_bayanus` was removed because no proteome could be found (see Part 1).
* `Millerozyma farinosa CBS 7064` (from OrthoDB) was removed, while `Millerozyma farinosa` was retained. The correct proteome had already been assigned in Part 1(b), replacing the incorrect association with `Pichia_sorbitophila`.
* Neither `Pneumocystis_murina` nor `Pneumocystis_carinii` was removed. During Part 1(b), the proteome for `Pneumocystis_carinii` was corrected, and these represent **two distinct species**, not duplicates.

---

## 3. Updated Organism List

The updated spreadsheet after duplicate removal is available at:

```text
tmp/part-2/fungi_organisms_and_proteins_revised_part2a.xlsx
```

The curated dataset now contains **1,553 organisms**.

---

## 4. Updated Plots

All plots were regenerated using the updated dataset.

Location:

```text
tmp/part-2/paper_plots_part2
```

These plots correspond to the final dataset of **1,553 organisms**.

---

## 5. Updated Proteome FASTA Files

The FASTA archive containing proteomes for all **1,553 organisms** is available at:

```text
https://drive.google.com/file/d/1qoUnjwKEnKdnvfXBeavwgTYfeIKzgM-X/view?usp=share_link
```

---

## 6. Updated `fungi_organisms_with_sequences_part2.csv`

A new version of:

```text
fungi_organisms_with_sequences_part2.csv
```

containing sequence data for **1,553 organisms × 25 query proteins** is available at:

```text
https://drive.google.com/file/d/1VCb1gp_tvKp9C1epiAP5yUm2y_4q85vn/view?usp=share_link
```

---

## 7. Part 2(b)

The following two organisms are **not the same species** and therefore should **not** be treated as duplicates:

* `Trichophyton equinum CBS 127.97`
* `Trichophyton tonsurans CBS 112818`

---

## 8. Note on Part 2(c)

Part 2(c) has not been explicitly verified.

However, if a **partial proteome** exists for an organism, it is likely because a complete proteome is unavailable. These partial proteomes can still produce valid BLAST matches and may therefore be important to retain rather than discard.
