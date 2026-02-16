"""
Main Orchestration Script for MCG Criteria Extraction System

This script coordinates the execution of all modules to extract, parse, interpret,
and structure MCG admission criteria from PDF guidelines.
"""

import os
import sys
import argparse
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from dotenv import load_dotenv
from tqdm import tqdm

# Import modules
from module_1_pdf_extraction import extract_pdf_content
from module_2_structure_parser import parse_admission_criteria
from module_3_llm_interpreter import interpret_criteria
from module_4_schema_builder import build_guideline_schema, SchemaBuilder


class MCGExtractionPipeline:
    """
    Main pipeline for MCG criteria extraction.
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize pipeline with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("MCG Extraction Pipeline initialized")
    
    def _setup_logging(self) -> None:
        """
        Setup logging configuration.
        """
        log_config = self.config.get('logging', {})
        
        # Create logs directory
        logs_dir = Path(self.config.get('paths', {}).get('logs_dir', 'logs'))
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        handlers = []
        
        # Console handler
        if log_config.get('console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(console_handler)
        
        # File handler
        if log_config.get('file_output', True):
            log_file = logs_dir / f"mcg_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=handlers
        )
    
    def process_pdf(self, pdf_path: str, output_dir: str = None) -> Dict[str, Any]:
        """
        Process a single PDF through the complete pipeline.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Output directory for schema (optional)
            
        Returns:
            Dictionary with processing results
        """
        self.logger.info(f"Starting pipeline for: {pdf_path}")
        
        # Validate input
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Determine output directory
        if output_dir is None:
            output_dir = self.config.get('paths', {}).get('output_schema_dir', 'data/output/schemas')
        
        results = {
            "pdf_path": pdf_path,
            "start_time": datetime.now().isoformat(),
            "stages": {}
        }
        
        try:
            # Stage 1: PDF Extraction
            self.logger.info("=" * 80)
            self.logger.info("STAGE 1: PDF TEXT EXTRACTION")
            self.logger.info("=" * 80)
            
            extracted_data = extract_pdf_content(pdf_path, self.config)
            results['stages']['extraction'] = {
                "status": "success",
                "sections_found": len(extracted_data.get('sections', []))
            }
            
            # Stage 2: Structure Parsing
            self.logger.info("\n" + "=" * 80)
            self.logger.info("STAGE 2: STRUCTURE PARSING")
            self.logger.info("=" * 80)
            
            parsed_data = parse_admission_criteria(extracted_data, self.config)
            criteria_count = len(parsed_data['admission_criteria']['criteria_list'])
            results['stages']['parsing'] = {
                "status": "success",
                "criteria_found": criteria_count,
                "alternatives_found": len(parsed_data.get('alternatives_to_admission', []))
            }
            
            # Stage 3: LLM Interpretation
            self.logger.info("\n" + "=" * 80)
            self.logger.info("STAGE 3: LLM INTERPRETATION")
            self.logger.info("=" * 80)
            
            interpreted_data = interpret_criteria(parsed_data, self.config)
            results['stages']['interpretation'] = {
                "status": "success",
                "criteria_interpreted": len(interpreted_data)
            }
            
            # Stage 4: Schema Building
            self.logger.info("\n" + "=" * 80)
            self.logger.info("STAGE 4: SCHEMA BUILDING")
            self.logger.info("=" * 80)
            
            schema = build_guideline_schema(
                extracted_data['metadata'],
                parsed_data,
                interpreted_data,
                self.config
            )
            
            # Validate schema
            builder = SchemaBuilder(self.config)
            is_valid, errors = builder.validate_schema(schema)
            
            results['stages']['schema_building'] = {
                "status": "success" if is_valid else "validation_failed",
                "validation_errors": errors
            }
            
            # Export schema
            guideline_id = schema['guideline_metadata']['guideline_id']
            output_path = Path(output_dir) / f"{guideline_id}.json"
            builder.export_schema(schema, str(output_path))
            
            results['output_path'] = str(output_path)
            results['schema'] = schema
            
            # Generate execution report
            self._generate_report(results)
            
            self.logger.info("\n" + "=" * 80)
            self.logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 80)
            self.logger.info(f"Schema exported to: {output_path}")
            
            results['end_time'] = datetime.now().isoformat()
            results['status'] = 'success'
            
            return results
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            results['status'] = 'failed'
            results['error'] = str(e)
            results['end_time'] = datetime.now().isoformat()
            raise
    
    def process_batch(self, input_dir: str, output_dir: str = None) -> List[Dict[str, Any]]:
        """
        Process multiple PDFs in batch mode.
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Output directory for schemas
            
        Returns:
            List of processing results for each PDF
        """
        self.logger.info(f"Starting batch processing from: {input_dir}")
        
        # Find all PDF files
        pdf_files = list(Path(input_dir).glob('*.pdf'))
        
        if not pdf_files:
            self.logger.warning(f"No PDF files found in: {input_dir}")
            return []
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        results = []
        
        # Process each PDF
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                result = self.process_pdf(str(pdf_path), output_dir)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to process {pdf_path}: {str(e)}")
                results.append({
                    "pdf_path": str(pdf_path),
                    "status": "failed",
                    "error": str(e)
                })
        
        # Generate batch summary
        self._generate_batch_summary(results)
        
        return results
    
    def _generate_report(self, results: Dict[str, Any]) -> None:
        """
        Generate execution report.
        
        Args:
            results: Processing results dictionary
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("MCG CRITERIA EXTRACTION - EXECUTION REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        report_lines.append(f"PDF File: {results['pdf_path']}")
        report_lines.append(f"Start Time: {results.get('start_time', 'Unknown')}")
        report_lines.append(f"End Time: {results.get('end_time', 'Unknown')}")
        report_lines.append(f"Status: {results.get('status', 'Unknown').upper()}")
        report_lines.append("")
        
        # Stage results
        report_lines.append("PIPELINE STAGES")
        report_lines.append("-" * 80)
        
        for stage_name, stage_data in results.get('stages', {}).items():
            report_lines.append(f"\n{stage_name.upper()}:")
            for key, value in stage_data.items():
                report_lines.append(f"  {key}: {value}")
        
        report_lines.append("")
        
        # Output location
        if 'output_path' in results:
            report_lines.append(f"Output Schema: {results['output_path']}")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        # Write report
        logs_dir = Path(self.config.get('paths', {}).get('logs_dir', 'logs'))
        report_path = logs_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        self.logger.info(f"Execution report saved to: {report_path}")
    
    def _generate_batch_summary(self, results: List[Dict[str, Any]]) -> None:
        """
        Generate batch processing summary.
        
        Args:
            results: List of processing results
        """
        summary_lines = []
        summary_lines.append("=" * 80)
        summary_lines.append("BATCH PROCESSING SUMMARY")
        summary_lines.append("=" * 80)
        summary_lines.append("")
        
        total = len(results)
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = total - successful
        
        summary_lines.append(f"Total PDFs: {total}")
        summary_lines.append(f"Successful: {successful}")
        summary_lines.append(f"Failed: {failed}")
        summary_lines.append("")
        
        # List failed files
        if failed > 0:
            summary_lines.append("FAILED FILES:")
            summary_lines.append("-" * 80)
            for result in results:
                if result.get('status') != 'success':
                    summary_lines.append(f"  {result['pdf_path']}")
                    summary_lines.append(f"    Error: {result.get('error', 'Unknown error')}")
            summary_lines.append("")
        
        summary_lines.append("=" * 80)
        
        # Write summary
        logs_dir = Path(self.config.get('paths', {}).get('logs_dir', 'logs'))
        summary_path = logs_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(summary_path, 'w') as f:
            f.write('\n'.join(summary_lines))
        
        self.logger.info(f"Batch summary saved to: {summary_path}")
        
        # Print to console
        print('\n'.join(summary_lines))


def main():
    """
    Main entry point for CLI.
    """
    parser = argparse.ArgumentParser(
        description='MCG Criteria Extraction System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single PDF
  python main.py --pdf "path/to/guideline.pdf"
  
  # Process with custom output directory
  python main.py --pdf "path/to/guideline.pdf" --output "output/"
  
  # Batch process directory
  python main.py --batch --input-dir "data/input/pdfs/"
  
  # Use custom config file
  python main.py --pdf "guideline.pdf" --config "custom_config.yaml"
        """
    )
    
    parser.add_argument(
        '--pdf',
        type=str,
        help='Path to single PDF file to process'
    )
    
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Enable batch processing mode'
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        help='Input directory for batch processing'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output directory for schemas'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.batch and not args.pdf:
        parser.error("Either --pdf or --batch must be specified")
    
    if args.batch and not args.input_dir:
        parser.error("--input-dir required for batch processing")
    
    try:
        # Initialize pipeline
        pipeline = MCGExtractionPipeline(args.config)
        
        # Process based on mode
        if args.batch:
            pipeline.process_batch(args.input_dir, args.output)
        else:
            pipeline.process_pdf(args.pdf, args.output)
        
        print("\n✓ Processing completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
