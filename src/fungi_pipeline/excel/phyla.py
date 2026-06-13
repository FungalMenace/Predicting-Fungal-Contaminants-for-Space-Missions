"""
Identify the phylum of a fungal species using multiple taxonomy APIs,
with fallback to a curated genus→phylum dictionary.

Usage:
    from identify_phyla import get_phylum
    phylum = get_phylum("Aspergillus fumigatus")
"""

import re
import requests


GENUS_TO_PHYLUM = {
    "Aspergillus": "Ascomycota",
    "Ceratocystis": "Ascomycota",
    "Australozyma": "Ascomycota",
    "Candidozyma": "Ascomycota",
    "Cercophora": "Ascomycota",
    "Clavulina": "Basidiomycota",
    "Cryoendolithus": "Ascomycota",
    "Dothideomycetidae": "Ascomycota",
    "Gibberella": "Ascomycota",
    "Henningerozyma": "Ascomycota",
    "Huiozyma": "Ascomycota",
    "Maudiozyma": "Ascomycota",
    "Metschnikowia": "Ascomycota",
    "Mycena": "Basidiomycota",
    "Nematocida": "Microsporidia",  # once grouped with fungi
    "Paramarasmius": "Basidiomycota",
    "Podospora": "Ascomycota",
    "Rozella": "Rozellomycota",
    "Siphonaria": "Mollusca",
    "Sungouiella": "Ascomycota",
    "Taxawa": "Ascomycota",
    "Trichoderma": "Ascomycota",
    "Coemansia": "Zoopagomycota",
    "Rhizophagus": "Glomeromycota",
}



def clean_name(species_name: str) -> str:
    """Simplify organism name for API searches."""
    name = re.sub(r"\b(sp\.|aff\.)\b.*", "", species_name)
    name = re.sub(r"\bCBS\s*\d+.*", "", name)
    name = re.sub(r"\bNRRL\s*\d+.*", "", name)
    return name.strip()



def get_phylum(species_name: str) -> str:
    """
    Identify phylum for a given species name.

    Lookup order:
    1. GBIF
    2. Catalogue of Life
    3. NCBI Taxonomy
    4. Local curated dictionary
    """
    cleaned = clean_name(species_name)

    # --- 1. GBIF API ---
    try:
        gbif_url = "https://api.gbif.org/v1/species/match"
        r = requests.get(gbif_url, params={"name": cleaned}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "phylum" in data and data["phylum"]:
                return data["phylum"]
    except Exception:
        pass

    # --- 2. Catalogue of Life ---
    try:
        col_url = "https://api.catalogueoflife.org/name/search"
        r = requests.get(col_url, params={"q": cleaned, "limit": 1}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"]:
                classification = data["result"][0].get("classification", [])
                for rank in classification:
                    if rank.get("rank", "").lower() == "phylum":
                        return rank.get("name")
    except Exception:
        pass

    # --- 3. NCBI Taxonomy ---
    try:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        r = requests.get(search_url, params={"db": "taxonomy", "term": cleaned, "retmode": "json"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            ids = data.get("esearchresult", {}).get("idlist", [])
            if ids:
                tax_id = ids[0]
                summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                r2 = requests.get(summary_url, params={"db": "taxonomy", "id": tax_id, "retmode": "json"}, timeout=10)
                if r2.status_code == 200:
                    tax_data = r2.json()
                    for _, record in tax_data["result"].items():
                        if isinstance(record, dict):
                            lineage = record.get("lineage", "")
                            for part in lineage.split("; "):
                                if "phylum" in part.lower():
                                    return part.split(":")[-1].strip()
    except Exception:
        pass

    # --- 4. Local fallback ---
    genus = cleaned.split()[0]
    if genus in GENUS_TO_PHYLUM:
        return GENUS_TO_PHYLUM[genus]

    # --- Not found ---
    return "Not found"
