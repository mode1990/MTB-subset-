#!/usr/bin/env python3
"""
Universal converter for MTB JSON formats (Ulm and Freiburg)
Auto-detects format and converts to pipeline-compatible format
"""

import json
import sys
from pathlib import Path

def detect_format(data):
    """Detect if JSON is Ulm or Freiburg format"""
    if "data" in data and "ngsReports" in data.get("data", {}):
        return "freiburg"
    elif "ngsReports" in data:
        return "ulm"
    else:
        return "unknown"

def convert_ulm_format(data):
    """Convert Ulm MTB format"""
    patient_id = data.get('episode', {}).get('patient', 'unknown')
    specimen = data.get('specimens', [{}])[0]
    diagnosis = data.get('diagnoses', [{}])[0]
    ngs_report = data.get('ngsReports', [{}])[0]
    metadata = ngs_report.get('metadata', [{}])[0]
    
    converted = {
        "patient_info": {
            "patient_id": patient_id,
            "sample_id": specimen.get('id', ''),
            "sample_type": specimen.get('type', ''),
            "tumor_type": diagnosis.get('icd10', {}).get('display', ''),
            "collection_date": specimen.get('collection', {}).get('date', ''),
            "clinical_stage": diagnosis.get('statusHistory', [{}])[0].get('status', '') if diagnosis.get('statusHistory') else ''
        },
        "sequencing": {
            "platform": metadata.get('sequencer', ''),
            "kit_manufacturer": metadata.get('kitManufacturer', ''),
            "kit_type": metadata.get('kitType', ''),
            "gene_panel": ngs_report.get('sequencingType', ''),
            "coverage_depth": "Not specified"
        },
        "pipeline": {
            "software": metadata.get('pipeline', '').replace('%20', ' '),
            "version": "",
            "reference_genome": metadata.get('referenceGenome', ''),
            "variant_caller": "Not specified",
            "filter_criteria": "Not specified"
        },
        "qc_metrics": {
            "total_reads": "Not specified",
            "mapped_reads_pct": "Not specified",
            "mean_coverage": "Not specified",
            "targets_min_depth_pct": "Not specified",
            "tumor_purity": "Not specified",
            "qc_status": "Not specified"
        },
        "snv_indel": [],
        "cnv": [],
        "fusion_sv": [],
        "additional_biomarkers": {
            "tmb": ngs_report.get('tmb', None),
            "tmb_unit": "mutations/Mb",
            "msi_status": "Not specified"
        },
        "clinical_interpretation": {
            "actionable_mutations": [],
            "resistance_mutations": [],
            "vus": []
        }
    }
    
    # Convert variants
    for variant in ngs_report.get('simpleVariants', []):
        gene_id = variant.get('gene', {}).get('hgncId', '').replace('HGNC:', '')
        converted_variant = {
            "gene": gene_id,
            "chr": f"chr{variant.get('chromosome', '')}",
            "pos": variant.get('startEnd', {}).get('start', ''),
            "ref": variant.get('refAllele', ''),
            "alt": variant.get('altAllele', ''),
            "consequence": "Not specified",
            "aa_change": variant.get('aminoAcidChange', {}).get('code', ''),
            "dna_change": variant.get('dnaChange', {}).get('code', ''),
            "vaf": variant.get('allelicFrequency', 0) / 100.0,
            "depth": variant.get('readDepth', ''),
            "transcript_id": "Not specified",
            "clinical_sig": variant.get('interpretation', {}).get('code', ''),
            "dbsnp_id": variant.get('dbSNPId', ''),
            "variant_id": variant.get('id', '')
        }
        converted["snv_indel"].append(converted_variant)
    
    # Convert CNVs
    for cnv in ngs_report.get('copyNumberVariants', []):
        converted_cnv = {
            "gene": cnv.get('gene', {}).get('hgncId', '').replace('HGNC:', ''),
            "chr": f"chr{cnv.get('chromosome', '')}",
            "start": cnv.get('startRange', {}).get('start', ''),
            "end": cnv.get('startRange', {}).get('end', ''),
            "copy_number": cnv.get('copyNumber', ''),
            "status": cnv.get('type', ''),
            "confidence": "Not specified",
            "method": "Not specified"
        }
        converted["cnv"].append(converted_cnv)
    
    # Convert fusions
    for fusion in ngs_report.get('rnaFusions', []):
        converted_fusion = {
            "gene_5prime": fusion.get('fusionPartner5prime', {}).get('gene', {}).get('hgncId', '').replace('HGNC:', ''),
            "gene_3prime": fusion.get('fusionPartner3prime', {}).get('gene', {}).get('hgncId', '').replace('HGNC:', ''),
            "supporting_reads": "Not specified",
            "frame_status": "Not specified",
            "fusion_type": "Not specified"
        }
        converted["fusion_sv"].append(converted_fusion)
    
    # Extract recommendations
    for rec in data.get('recommendations', []):
        for med in rec.get('medication', []):
            actionable = {
                "variant_ids": rec.get('supportingVariants', []),
                "therapy": med.get('display', ''),
                "evidence_level": rec.get('levelOfEvidence', {}).get('grading', {}).get('code', ''),
                "priority": rec.get('priority', ''),
                "issued_date": rec.get('issuedOn', '')
            }
            converted["clinical_interpretation"]["actionable_mutations"].append(actionable)
    
    return converted

def convert_freiburg_format(data):
    """Convert Freiburg MTB format"""
    inner_data = data.get('data', {})
    
    patient_id = inner_data.get('patient', {}).get('id', 'unknown')
    specimens = inner_data.get('specimens', [{}])
    specimen = specimens[0] if specimens else {}
    diagnoses = inner_data.get('diagnoses', [{}])
    diagnosis = diagnoses[0] if diagnoses else {}
    ngs_reports = inner_data.get('ngsReports', [])
    
    # Handle case with no NGS data
    if not ngs_reports:
        return {
            "patient_info": {
                "patient_id": patient_id,
                "sample_id": "",
                "sample_type": "",
                "tumor_type": diagnosis.get('icd10', {}).get('display', ''),
                "collection_date": "",
                "clinical_stage": diagnosis.get('statusHistory', [{}])[0].get('status', '') if diagnosis.get('statusHistory') else ''
            },
            "sequencing": {
                "platform": "No NGS data",
                "kit_manufacturer": "No NGS data",
                "kit_type": "No NGS data",
                "gene_panel": "No NGS data",
                "coverage_depth": "No NGS data"
            },
            "pipeline": {
                "software": "No NGS data",
                "version": "No NGS data",
                "reference_genome": "No NGS data",
                "variant_caller": "No NGS data",
                "filter_criteria": "No NGS data"
            },
            "qc_metrics": {
                "total_reads": "No NGS data",
                "mapped_reads_pct": "No NGS data",
                "mean_coverage": "No NGS data",
                "targets_min_depth_pct": "No NGS data",
                "tumor_purity": "No NGS data",
                "qc_status": "No NGS data"
            },
            "snv_indel": [],
            "cnv": [],
            "fusion_sv": [],
            "additional_biomarkers": {
                "tmb": None,
                "msi_status": "No NGS data"
            },
            "clinical_interpretation": {
                "actionable_mutations": [],
                "resistance_mutations": [],
                "vus": []
            }
        }
    
    ngs_report = ngs_reports[0]
    metadata = ngs_report.get('metadata', [{}])[0]
    
    converted = {
        "patient_info": {
            "patient_id": patient_id,
            "sample_id": specimen.get('id', ''),
            "sample_type": specimen.get('type', ''),
            "tumor_type": diagnosis.get('icd10', {}).get('display', ''),
            "collection_date": specimen.get('collection', {}).get('date', ''),
            "clinical_stage": diagnosis.get('statusHistory', [{}])[0].get('status', '') if diagnosis.get('statusHistory') else ''
        },
        "sequencing": {
            "platform": metadata.get('sequencer', ''),
            "kit_manufacturer": metadata.get('kitManufacturer', ''),
            "kit_type": metadata.get('kitType', ''),
            "gene_panel": ngs_report.get('sequencingType', ''),
            "coverage_depth": "Not specified"
        },
        "pipeline": {
            "software": metadata.get('pipeline', ''),
            "version": "",
            "reference_genome": metadata.get('referenceGenome', ''),
            "variant_caller": "Not specified",
            "filter_criteria": "Not specified"
        },
        "qc_metrics": {
            "total_reads": "Not specified",
            "mapped_reads_pct": "Not specified",
            "mean_coverage": "Not specified",
            "targets_min_depth_pct": "Not specified",
            "tumor_purity": ngs_report.get('tumorCellContent', {}).get('value', 'Not specified'),
            "qc_status": "Not specified"
        },
        "snv_indel": [],
        "cnv": [],
        "fusion_sv": [],
        "additional_biomarkers": {
            "tmb": ngs_report.get('tmb', None),
            "tmb_unit": "mutations/Mb",
            "msi_status": ngs_report.get('msi', 'Not specified'),
            "brcaness": ngs_report.get('brcaness', None)
        },
        "clinical_interpretation": {
            "actionable_mutations": [],
            "resistance_mutations": [],
            "vus": []
        }
    }
    
    # Convert simple variants
    for variant in ngs_report.get('simpleVariants', []):
        gene = variant.get('gene', {})
        converted_variant = {
            "gene": gene.get('hgncId', '').replace('HGNC:', ''),
            "gene_symbol": gene.get('symbol', ''),
            "gene_name": gene.get('name', ''),
            "chr": variant.get('chromosome', ''),
            "pos": variant.get('startEnd', {}).get('start', ''),
            "ref": variant.get('refAllele', ''),
            "alt": variant.get('altAllele', ''),
            "consequence": "Not specified",
            "aa_change": "Not specified",
            "dna_change": variant.get('dnaChange', {}).get('code', '') if 'dnaChange' in variant else '',
            "vaf": variant.get('allelicFrequency', 0),
            "depth": variant.get('readDepth', ''),
            "transcript_id": "Not specified",
            "clinical_sig": variant.get('interpretation', {}).get('code', ''),
            "dbsnp_id": variant.get('dbSNPId', ''),
            "variant_id": variant.get('id', '')
        }
        converted["snv_indel"].append(converted_variant)
    
    # Convert CNVs
    for cnv in ngs_report.get('copyNumberVariants', []):
        affected_genes = cnv.get('reportedAffectedGenes', [])
        gene_symbols = [g.get('symbol', '') for g in affected_genes]
        
        converted_cnv = {
            "genes": ', '.join(gene_symbols),
            "chr": cnv.get('chromosome', ''),
            "start": cnv.get('startRange', {}).get('start', ''),
            "end": cnv.get('endRange', {}).get('start', ''),
            "copy_number": cnv.get('totalCopyNumber', ''),
            "status": cnv.get('type', ''),
            "confidence": "Not specified",
            "method": "Not specified",
            "variant_id": cnv.get('id', '')
        }
        converted["cnv"].append(converted_cnv)
    
    # Convert fusions
    for fusion in ngs_report.get('rnaFusions', []):
        converted_fusion = {
            "gene_5prime": fusion.get('fusionPartner5prime', {}).get('gene', {}).get('symbol', ''),
            "gene_3prime": fusion.get('fusionPartner3prime', {}).get('gene', {}).get('symbol', ''),
            "supporting_reads": fusion.get('numSplitReads', 'Not specified'),
            "frame_status": "Not specified",
            "fusion_type": "Not specified",
            "variant_id": fusion.get('id', '')
        }
        converted["fusion_sv"].append(converted_fusion)
    
    # Extract recommendations
    for rec in inner_data.get('recommendations', []):
        medications = rec.get('medication', [])
        for med in medications:
            actionable = {
                "therapy": med.get('display', ''),
                "priority": rec.get('priority', ''),
                "issued_date": rec.get('issuedOn', ''),
                "ngs_report": rec.get('ngsReport', '')
            }
            converted["clinical_interpretation"]["actionable_mutations"].append(actionable)
    
    return converted

def convert_mtb_to_pipeline(input_file, output_file):
    """Auto-detect format and convert"""
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    format_type = detect_format(data)
    
    if format_type == "ulm":
        print(f"Detected: Ulm format")
        converted = convert_ulm_format(data)
    elif format_type == "freiburg":
        print(f"Detected: Freiburg format")
        converted = convert_freiburg_format(data)
    else:
        print(f"ERROR: Unknown format in {input_file}")
        sys.exit(1)
    
    # Write converted JSON
    with open(output_file, 'w') as f:
        json.dump(converted, f, indent=2)
    
    patient_id = converted['patient_info']['patient_id']
    print(f"✓ Converted: {input_file} → {output_file}")
    print(f"  Patient: {patient_id}")
    print(f"  Variants: {len(converted['snv_indel'])} SNV/Indel")
    print(f"  CNVs: {len(converted['cnv'])}")
    print(f"  Fusions: {len(converted['fusion_sv'])}")
    print(f"  Actionable: {len(converted['clinical_interpretation']['actionable_mutations'])}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 convert_mtb_json.py input.json output.json")
        sys.exit(1)
    
    convert_mtb_to_pipeline(sys.argv[1], sys.argv[2])
