#!/usr/bin/env python3
"""
Genomic Data JSON Validator and Extractor
Validates completeness and extracts data into structured tables
"""

import json
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse


class GenomicDataValidator:
    """Validates and extracts genomic JSON data"""
    
    REQUIRED_FIELDS = {
        'patient_info': [
            'patient_id', 'sample_id', 'sample_type', 
            'tumor_type', 'collection_date', 'clinical_stage'
        ],
        'sequencing': [
            'platform', 'kit_manufacturer', 'kit_type', 
            'gene_panel', 'coverage_depth'
        ],
        'pipeline': [
            'software', 'version', 'reference_genome', 
            'variant_caller', 'filter_criteria'
        ],
        'qc_metrics': [
            'total_reads', 'mapped_reads_pct', 'mean_coverage',
            'targets_min_depth_pct', 'tumor_purity', 'qc_status'
        ]
    }
    
    VARIANT_FIELDS = [
        'gene', 'chr', 'pos', 'ref', 'alt', 'consequence',
        'aa_change', 'vaf', 'depth', 'transcript_id', 'clinical_sig'
    ]
    
    def __init__(self, json_path):
        self.json_path = Path(json_path)
        self.data = self._load_json()
        self.validation_results = {}
        self.patient_id = self.data.get('patient_info', {}).get('patient_id', 'unknown')
        
    def _load_json(self):
        """Load and parse JSON file"""
        try:
            with open(self.json_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load {self.json_path}: {e}")
            sys.exit(1)
    
    def validate(self):
        """Validate all required fields"""
        print(f"\n{'='*60}")
        print(f"Validating: {self.json_path.name}")
        print(f"{'='*60}\n")
        
        all_valid = True
        
        for section, fields in self.REQUIRED_FIELDS.items():
            print(f"[{section.upper()}]")
            section_data = self.data.get(section, {})
            missing = []
            
            for field in fields:
                present = field in section_data and section_data[field] is not None
                status = "✓" if present else "✗"
                print(f"  {status} {field}")
                
                if not present:
                    missing.append(field)
                    all_valid = False
            
            self.validation_results[section] = {
                'complete': len(missing) == 0,
                'missing': missing
            }
            print()
        
        # Check genomic data availability
        print("[GENOMIC ALTERATIONS]")
        for data_type in ['snv_indel', 'cnv', 'fusion_sv']:
            available = data_type in self.data and self.data[data_type]
            status = "✓" if available else "✗"
            count = len(self.data.get(data_type, [])) if available else 0
            print(f"  {status} {data_type}: {count} variants")
        
        print(f"\n{'='*60}")
        print(f"Overall Status: {'PASS ✓' if all_valid else 'INCOMPLETE ✗'}")
        print(f"{'='*60}\n")
        
        return all_valid
    
    def extract_patient_info(self):
        """Extract patient and sequencing info"""
        info = self.data.get('patient_info', {})
        seq = self.data.get('sequencing', {})
        pipe = self.data.get('pipeline', {})
        qc = self.data.get('qc_metrics', {})
        
        return pd.DataFrame([{
            'patient_id': info.get('patient_id'),
            'sample_id': info.get('sample_id'),
            'sample_type': info.get('sample_type'),
            'tumor_type': info.get('tumor_type'),
            'collection_date': info.get('collection_date'),
            'clinical_stage': info.get('clinical_stage'),
            'platform': seq.get('platform'),
            'kit_type': seq.get('kit_type'),
            'kit_manufacturer': seq.get('kit_manufacturer'),
            'gene_panel': seq.get('gene_panel'),
            'coverage_depth': seq.get('coverage_depth'),
            'pipeline': pipe.get('software'),
            'version': pipe.get('version'),
            'reference_genome': pipe.get('reference_genome'),
            'mean_coverage': qc.get('mean_coverage'),
            'tumor_purity': qc.get('tumor_purity'),
            'qc_status': qc.get('qc_status')
        }])
    
    def extract_variants(self):
        """Extract SNV/Indel variants"""
        variants = self.data.get('snv_indel', [])
        if not variants:
            return pd.DataFrame()
        
        df = pd.DataFrame(variants)
        df.insert(0, 'patient_id', self.patient_id)
        return df
    
    def extract_cnv(self):
        """Extract CNV data"""
        cnv_data = self.data.get('cnv', [])
        if not cnv_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(cnv_data)
        df.insert(0, 'patient_id', self.patient_id)
        return df
    
    def extract_fusions(self):
        """Extract fusion/SV data"""
        fusions = self.data.get('fusion_sv', [])
        if not fusions:
            return pd.DataFrame()
        
        df = pd.DataFrame(fusions)
        df.insert(0, 'patient_id', self.patient_id)
        return df
    
    def extract_actionable(self):
        """Extract actionable mutations"""
        actionable = self.data.get('clinical_interpretation', {}).get('actionable_mutations', [])
        if not actionable:
            return pd.DataFrame()
        
        df = pd.DataFrame(actionable)
        df.insert(0, 'patient_id', self.patient_id)
        return df
    
    def generate_report(self, output_dir):
        """Generate validation report"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        report_path = output_dir / f"{self.patient_id}_validation_report.txt"
        
        with open(report_path, 'w') as f:
            f.write(f"Genomic Data Validation Report\n")
            f.write(f"{'='*60}\n")
            f.write(f"File: {self.json_path.name}\n")
            f.write(f"Patient ID: {self.patient_id}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n\n")
            
            for section, results in self.validation_results.items():
                status = "COMPLETE" if results['complete'] else "INCOMPLETE"
                f.write(f"{section.upper()}: {status}\n")
                if results['missing']:
                    f.write(f"  Missing fields: {', '.join(results['missing'])}\n")
                f.write("\n")
            
            # Genomic data summary
            f.write("GENOMIC ALTERATIONS SUMMARY:\n")
            f.write(f"  SNV/Indel: {len(self.data.get('snv_indel', []))} variants\n")
            f.write(f"  CNV: {len(self.data.get('cnv', []))} alterations\n")
            f.write(f"  Fusions/SV: {len(self.data.get('fusion_sv', []))} events\n")
        
        print(f"Report saved: {report_path}")
        return report_path


def process_multiple_files(json_files, output_dir):
    """Process multiple JSON files and combine results"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    all_patient_info = []
    all_variants = []
    all_cnv = []
    all_fusions = []
    all_actionable = []
    
    validation_summary = []
    
    for json_file in json_files:
        print(f"\nProcessing: {json_file}")
        validator = GenomicDataValidator(json_file)
        
        # Validate
        is_valid = validator.validate()
        validation_summary.append({
            'file': Path(json_file).name,
            'patient_id': validator.patient_id,
            'status': 'PASS' if is_valid else 'INCOMPLETE'
        })
        
        # Extract data
        all_patient_info.append(validator.extract_patient_info())
        
        variants_df = validator.extract_variants()
        if not variants_df.empty:
            all_variants.append(variants_df)
        
        cnv_df = validator.extract_cnv()
        if not cnv_df.empty:
            all_cnv.append(cnv_df)
        
        fusions_df = validator.extract_fusions()
        if not fusions_df.empty:
            all_fusions.append(fusions_df)
        
        actionable_df = validator.extract_actionable()
        if not actionable_df.empty:
            all_actionable.append(actionable_df)
        
        # Generate individual report
        validator.generate_report(output_dir)
    
    # Combine and save all data
    print(f"\n{'='*60}")
    print("Saving combined tables...")
    print(f"{'='*60}\n")
    
    # Patient info
    patient_info_combined = pd.concat(all_patient_info, ignore_index=True)
    patient_info_path = output_dir / "combined_patient_info.tsv"
    patient_info_combined.to_csv(patient_info_path, sep='\t', index=False)
    print(f"✓ Patient info: {patient_info_path}")
    
    # Variants
    if all_variants:
        variants_combined = pd.concat(all_variants, ignore_index=True)
        variants_path = output_dir / "combined_variants.tsv"
        variants_combined.to_csv(variants_path, sep='\t', index=False)
        print(f"✓ Variants: {variants_path} ({len(variants_combined)} total)")
    else:
        print("✗ No variant data found")
    
    # CNV
    if all_cnv:
        cnv_combined = pd.concat(all_cnv, ignore_index=True)
        cnv_path = output_dir / "combined_cnv.tsv"
        cnv_combined.to_csv(cnv_path, sep='\t', index=False)
        print(f"✓ CNV: {cnv_path} ({len(cnv_combined)} total)")
    else:
        print("✗ No CNV data found")
    
    # Fusions
    if all_fusions:
        fusions_combined = pd.concat(all_fusions, ignore_index=True)
        fusions_path = output_dir / "combined_fusions.tsv"
        fusions_combined.to_csv(fusions_path, sep='\t', index=False)
        print(f"✓ Fusions: {fusions_path} ({len(fusions_combined)} total)")
    else:
        print("✗ No fusion data found")
    
    # Actionable
    if all_actionable:
        actionable_combined = pd.concat(all_actionable, ignore_index=True)
        actionable_path = output_dir / "combined_actionable.tsv"
        actionable_combined.to_csv(actionable_path, sep='\t', index=False)
        print(f"✓ Actionable mutations: {actionable_path} ({len(actionable_combined)} total)")
    
    # Validation summary
    summary_df = pd.DataFrame(validation_summary)
    summary_path = output_dir / "validation_summary.tsv"
    summary_df.to_csv(summary_path, sep='\t', index=False)
    print(f"✓ Validation summary: {summary_path}")
    
    print(f"\n{'='*60}")
    print(f"Pipeline completed successfully!")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Validate and extract genomic data from JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file
  python validate_genomic_json.py data.json -o output/
  
  # Multiple files
  python validate_genomic_json.py file1.json file2.json file3.json -o output/
  
  # All JSON files in directory
  python validate_genomic_json.py data/*.json -o output/
        """
    )
    
    parser.add_argument('json_files', nargs='+', help='JSON file(s) to process')
    parser.add_argument('-o', '--output', default='genomic_output', 
                       help='Output directory (default: genomic_output)')
    
    args = parser.parse_args()
    
    if len(args.json_files) == 1:
        # Single file mode
        validator = GenomicDataValidator(args.json_files[0])
        validator.validate()
        
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        
        # Save individual tables
        validator.extract_patient_info().to_csv(
            output_dir / f"{validator.patient_id}_patient_info.tsv", 
            sep='\t', index=False
        )
        
        variants = validator.extract_variants()
        if not variants.empty:
            variants.to_csv(
                output_dir / f"{validator.patient_id}_variants.tsv", 
                sep='\t', index=False
            )
        
        cnv = validator.extract_cnv()
        if not cnv.empty:
            cnv.to_csv(
                output_dir / f"{validator.patient_id}_cnv.tsv", 
                sep='\t', index=False
            )
        
        fusions = validator.extract_fusions()
        if not fusions.empty:
            fusions.to_csv(
                output_dir / f"{validator.patient_id}_fusions.tsv", 
                sep='\t', index=False
            )
        
        validator.generate_report(output_dir)
        
        print(f"\nTables saved to: {output_dir}")
    else:
        # Multiple files mode
        process_multiple_files(args.json_files, args.output)


if __name__ == '__main__':
    main()
