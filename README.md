# MTB-subset-
MTB subset Genomic Data Integration Pipeline

MTB Genomic Data Integration Pipeline
Python-based ETL pipeline designed to harmonize heterogeneous clinical genomic data (JSON) from multiple medical centers (BW, Germany) into standardized, analysis-ready formats.
Key Features
* Auto-Detection: Automatically identifies JSON schemas from different hospital formats.
* Data Harmonization: Standardizes patient metadata, SNVs, Indels, CNVs, and RNA fusions.
* Clinical Actionability: Extracts therapy recommendations and levels of evidence linked to specific variants.
* Automated Validation: Generates QC reports for data completeness and integrity.
Project Structure
* convert_mtb_json_v2.py: The main converter script for format normalization.
* validate_genomic_json.py: Validator and extractor that generates combined TSV tables.
* final_results/: Directory containing standardized tables and validation reports.
Quick Start
To process multiple JSON files and generate integrated tables:
Bash

python3 validate_genomic_json.py data/*.json -o final_results/
Outputs
* combined_patient_info.tsv: Unified patient demographics.
* combined_variants.tsv: Consolidated SNV/Indel list.
* combined_actionable.tsv: Mapped clinical recommendations/therapies.
* validation_summary.tsv: High-level QC status of the dataset

