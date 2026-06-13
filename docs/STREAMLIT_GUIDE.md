# Fungal Contamination Checker (Streamlit App)

<!-- [⬅ Back to Main README](../README.md) -->

Welcome to the **Fungal Contamination Checker**. This interactive Streamlit application allows researchers, astrobiologists, and microbiologists to compare Fungi sequencing data against a curated list of organisms with specific stress-resistance and pathogenicity properties. 

Users can adjust contamination weights, set custom thresholds, and filter Fungi data based on environmental location counts and other adaptive properties.

👉 **Access the Live App:** [Fungal Contamination Checker](https://fungalcontaminants.streamlit.app)

---

## ✨ Key Features

- **Upload Your Own CSV**: Easily upload your own Fungi dataset in CSV format for direct comparison against our curated database.
- **Adjust Contamination Weights**: Fine-tune weights for various Fungi properties (e.g., radiation resistance, biofilm formation) to customize the risk filtering process.
- **Set Custom Thresholds**: Use interface controls to set specific contamination score and location count thresholds.
- **Dynamic Output Display**: Choose to recompute results automatically or manually based on user inputs.
- **Visualize Filtered Results**: View filtered fungi lists, summary statistics, and dynamic tables based on your configurations.
- **Venn Diagram Visualization**: Generate and download Venn diagrams to visualize the distribution of contributing traits among the filtered fungal species.

---

## 📁 Input File Format

To use this app effectively, please ensure your input CSV file adheres to the following format:

### Example Input CSV Format

| Species                      | loc1 | loc2 | loc3  | ...   |
|------------------------------|------|------|-------|-------|
| Aaosphaeria arxii CBS 175.79 | 200  | 1240 | 0     | ...   |
| Absidia caerulea NRRL1315    | 300  | 4240 | 0     | ...   |
| Absidia repens NRRL 1336     | 2200 | 1240 | 10000 | ...   |
| ...                          | ...  | ...  | ...   | ...   |

#### Input File Requirements
1. **`Species` Column**: The first column must contain the names of the fungi species (e.g., `#Datasets` or `Species`).
2. **Location Columns**: Subsequent columns (e.g., `loc1`, `loc2`, `loc3`, etc.) should represent different sampling locations. Each cell under these columns must contain numeric values representing the number of measurements (reads) for the corresponding fungi found at that location.

---

## ⚙️ What the App Does

1. **Data Comparison**: Compares the input fungi species against our curated list (`curated_fungi.csv`), which includes properties such as radiation resistance, biofilm formation, spore formation, and pathogenicity.
2. **Adjust Weights for Contamination Properties**: Users can adjust the mathematical weights for different properties used to calculate the final A-score/S-score. A default weights file (`score_weights.txt`) is provided, and users can upload their own JSON file with custom weights.
3. **Set Thresholds for Filtering**:
   - **Score Threshold**: Determines which fungi species are flagged based on their stress-resistance properties.
   - **Reads Threshold**: A threshold for the minimum number of measurements in a location column that a species must exceed to be included in the output.
4. **Dynamic Recalculation**: Users can select whether to automatically recompute results when settings are changed or manually trigger the computation to save processing time.

---

## 📊 Outputs Explained

### 1. Statistics Table
This table provides a high-level summary of the comparison and filtering results:
- **Num**: The total number of fungi in the uploaded list.
- **Matched**: The number of fungi whose names match those in the curated database.
- **Above Threshold**: The number of fungi that meet the selected thresholds for both the contamination score and location read count.

### 2. Filtered Fungi List
Displays a detailed table with fungi that pass both the score and reads thresholds. This table contains:
- **Species**: Name of the fungi species.
- **Score**: The weighted contamination score based on their ortholog properties.
- **Num loc**: The number of locations where the reads (measurements) exceed the selected threshold.
- **Locations**: A dictionary showing the location names and their corresponding counts that exceed the threshold.

---

## 🚀 How to Use the App

1. **Navigate to the “Input Data” Tab**
   The app begins in the **“Input Data”** tab, organized into three subtabs for better control:
   * 📂 **Input File**
   * ⚖️ **Weights**
   * 🎚️ **Thresholds**

2. **Select Identity Threshold (Curated List)**
   In the **Input File** subtab, choose the ortholog identity threshold for the curated database:
   * **ID thresh = 35** (less strict match, captures distant orthologs)
   * **ID thresh = 75** (more conservative match, requires high sequence identity)

3. **Upload or Use Sample Data**
   * Check the box to use the built-in **sample-infile.csv** or upload your own CSV file.
   * The app automatically matches your organisms against the curated list. If no read counts are provided, a default of 100 reads will be assumed.

4. **Adjust Contamination Weights**
   In the **Weights** subtab:
   * Use sliders to adjust the importance of factors such as **biofilm formation**, **pathogenicity**, and **radiation resistance**.
   * Click **“Restore Default Weights”** to revert changes.
   * Optionally upload a **custom weights JSON file** to override all values.

5. **Set Contamination Thresholds**
   In the **Thresholds** subtab:
   * **Score Threshold**: Organisms with a contamination score above this are flagged.
   * **Reads Threshold**: Minimum read count required for an organism to be considered valid.

6. **Run Analysis**
   * Click **“Run Contamination Analysis”** to compute results.
   * *Note: This manual run replaces the old “Recompute Automatically” toggle, ensuring consistent and reproducible results.*

7. **Explore Your Results**
   After running the analysis, switch to the other main tabs:
   * **Summary Results**: Shows contamination metrics and the interactive Venn diagram.
   * **Detailed Table**: Filtered fungi list with scores and status (available for CSV download).
   * **BLAST Analysis**: Shows unmatched organisms and provides an interface to re-analyze them using the underlying BLAST pipeline.

---

## 💡 Tips
- **Formatting:** Ensure your input CSV file is correctly formatted for accurate matching. Typographical errors in species names will result in unmatched queries.
- **Weight Adjustments:** Adjust weights thoughtfully to filter fungi based on the environmental pressures most relevant to your specific mission or sampling site.
- **Thresholds:** Experiment with different threshold values to explore how varying stringencies affect your contamination risk profile.

## 📞 Feedback and Support
If you have any questions, encounter any issues, or have suggestions for improvement, please reach out via the credits section on the Streamlit app or open an Issue directly on our GitHub repository.