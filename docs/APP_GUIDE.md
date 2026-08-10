# Fungal Contamination Checker (Web App)

[⬅ Back to Main README](../README.md)

Welcome to the **Fungal Contamination Checker**. This dashboard is designed to flag likely fungal contaminants in sequencing or microbiome datasets. It evaluates observed species against a curated database of risk-relevant properties.

This application is built on top of the upstream [CheckFungalContam](https://github.com/FungalMenace/CheckFungalContam) tool used at Caltech, TRISH, and the NASA-CSIF.

`link to github repository of application`: https://github.com/FungalMenace/CheckFungalContam

`link to the web application`: https://sites.astro.caltech.edu/checkfungalcontam/

---

## ✨ Key Features

- **Tri-Valued Scoring System**: Employs a sophisticated scoring matrix based on sequence identity thresholds (0 for none, 1 for weak evidence, 2 for strong evidence).
- **Six Critical Risk Properties**: Evaluates organisms based on antimicrobial resistance, biofilm formation, human pathogenicity, thermophily, radiation resistance, and spore formation.
- **Dynamic Genus Aggregation**: Automatically expands group entries (e.g., `Aspergillus sp.`) against the database and aggregates scores across the genus (via mean, max, or sum).
- **Customizable Weights & Thresholds**: Fine-tune the mathematical weights for specific properties directly in the sidebar, and set filtering thresholds for both contamination scores and read counts.
- **Interactive Visualizations**: Explore your results through a scored, sortable table, a species-by-location reads heatmap, a reads-per-property breakdown, and an UpSet plot showing which risk properties co-occur.

---

## ⚙️ What the App Does (The Scoring Logic)

1. **Database Matching**: The app matches each species from your input CSV against our curated database of ~1,500 fungi annotated with the six contamination-relevant properties.
2. **Evidence Scoring**: Each match is scored using tri-valued evidence per property based on ortholog presence:
   - `0` — Property not observed.
   - `1` — Observed at $\ge35\%$ sequence identity (weak evidence).
   - `2` — Observed at $\ge75\%$ sequence identity (strong evidence).
3. **Weight Calculation**: The final contamination score is a weighted sum: 
   `score = Σ weight[prop] × evidence[prop]`
   *(By default, all weights are set to 1. In the sidebar, you can set a weight to 0 to ignore a property, or 2 to double-weight it).*
4. **Filtering**: The app filters the final list by two user-defined thresholds: the minimum weighted score, and the minimum read count in at least one location.

---

## 📁 Input File Format

To use the app, upload a CSV containing the species name in the first column and the read counts (measurements) in the remaining location-based columns. 

### Example Input CSV
```csv
#Datasets,loc1,loc2,loc3
Candida albicans,200,1240,0
Aspergillus sp.,300,4240,0

```

### Input File Rules

1. **First Column**: Must contain the organism names.
2. **Location Columns**: Subsequent columns represent different sampling sites or experimental locations, populated with numeric read counts.
3. **Group Entries**: You may use group formatting like `Genus sp.` (e.g., `Aspergillus sp.`). The app will intelligently expand this against all known species within that genus in the curated database and aggregate their scores based on your chosen method (mean, max, or sum).

---

## 🚀 Running Locally

If you prefer to run the application locally on your machine rather than using the web version, the README there indicates how.


---


## 🏆 Credits

* **Concept & Direction**: Ashish Mahabal (Caltech), Nitin K. Singh
* **Domain Expertise**: Swati Bijlani

*For issues, bug reports, or feature requests regarding the dashboard, please open an issue on the upstream GitHub repository.*
