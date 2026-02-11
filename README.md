# MTB Genomic Data Integration Pipeline

Python ETL pipeline for harmonizing clinical genomic data (JSON) from multiple medical centers in Baden-Württemberg, Germany into standardized, analysis-ready formats.

## Features

- **Auto-detection** of hospital-specific JSON schemas
- **Data harmonization** for patient metadata, SNVs, Indels, CNVs, and RNA fusions
- **Clinical actionability** extraction with therapy recommendations and evidence levels
- **Automated validation** and QC reporting

## Structure

- `convert_mtb_json_v2.py` – Main format normalization script
- `validate_genomic_json.py` – Validator and TSV table generator
- `final_results/` – Standardized output tables and validation reports

## Quick Start
```bash
python3 validate_genomic_json.py data/*.json -o final_results/
```

## Outputs

- `combined_patient_info.tsv` – Patient demographics
- `combined_variants.tsv` – SNV/Indel variants
- `combined_actionable.tsv` – Clinical recommendations
- `validation_summary.tsv` – QC metrics

## Misc:
## JSON Repair Utilities (Only applicable to Tuebinegn subset (n=2584) NGS only JSONs)

- `fix_double_commas.sh` – Removes double commas (`,,`) from malformed JSON files
- `fix_trailing_commas.sh` – Removes trailing commas before closing braces/brackets
