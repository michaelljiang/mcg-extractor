"""
Module 4: Schema Builder

This module combines all parsed and interpreted data into a unified schema
with executable matching rules and validation.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import jsonschema


logger = logging.getLogger(__name__)


class SchemaBuilder:
    """
    Builds unified MCG guideline schema from extracted and interpreted data.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize schema builder with configuration.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.schema_config = config.get('schema', {})
        self.terminology_config = config.get('terminology', {})
    
    def build_guideline_schema(
        self,
        metadata: Dict[str, Any],
        parsed_data: Dict[str, Any],
        interpreted_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build complete guideline schema.
        
        Args:
            metadata: Metadata from PDF extraction
            parsed_data: Parsed structure from module 2
            interpreted_data: Interpreted criteria from module 3
            
        Returns:
            Complete schema dictionary
        """
        logger.info("Building guideline schema")
        
        # Build metadata section
        guideline_metadata = self._build_metadata(metadata)
        
        # Build admission decision logic
        admission_logic = self._build_admission_logic(
            parsed_data, 
            interpreted_data
        )
        
        # Build alternatives section
        alternatives = self._build_alternatives(
            parsed_data.get('alternatives_to_admission', [])
        )
        
        # Build complete schema
        schema = {
            "schema_version": "1.0",
            "schema_created": datetime.now().isoformat(),
            "guideline_metadata": guideline_metadata,
            "admission_decision_logic": admission_logic,
            "alternatives_to_admission": alternatives
        }
        
        logger.info("Schema building complete")
        return schema
    
    def _build_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build metadata section of schema.
        
        Args:
            metadata: Metadata from PDF extraction
            
        Returns:
            Formatted metadata dictionary
        """
        # Generate guideline ID from name
        guideline_name = metadata.get('guideline_name', 'Unknown Guideline')
        guideline_id = self._generate_guideline_id(guideline_name)
        
        return {
            "guideline_id": guideline_id,
            "guideline_name": guideline_name,
            "org_code": metadata.get('org_code', ''),
            "version": metadata.get('edition', ''),
            "effective_date": metadata.get('effective_date', ''),
            "specialty": metadata.get('specialty', 'General Medicine'),
            "care_setting": "inpatient",
            "source_document": metadata.get('pdf_filename', ''),
            "extraction_date": metadata.get('extracted_date', '')
        }
    
    def _generate_guideline_id(self, guideline_name: str) -> str:
        """
        Generate unique guideline ID from name.
        
        Args:
            guideline_name: Name of the guideline
            
        Returns:
            Guideline ID string
        """
        # Convert to lowercase, replace spaces with underscores, remove special chars
        import re
        guideline_id = guideline_name.lower()
        guideline_id = re.sub(r'[^\w\s-]', '', guideline_id)
        guideline_id = re.sub(r'[-\s]+', '_', guideline_id)
        return f"mcg_{guideline_id[:50]}"  # Limit length
    
    def _build_admission_logic(
        self,
        parsed_data: Dict[str, Any],
        interpreted_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build admission decision logic section.
        
        Args:
            parsed_data: Parsed structure from module 2
            interpreted_data: Interpreted criteria from module 3
            
        Returns:
            Admission logic dictionary
        """
        criteria_list = []
        
        for interpreted in interpreted_data:
            criterion = self._build_criterion_entry(interpreted)
            criteria_list.append(criterion)
        
        return {
            "rule_type": "disjunctive",  # ANY criterion triggers admission
            "description": "Patient meets admission criteria if ANY of the following conditions are met",
            "minimum_criteria_count": 1,
            "criteria": criteria_list
        }
    
    def _build_criterion_entry(self, interpreted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a single criterion entry for the schema.
        
        Args:
            interpreted: Interpreted criterion data
            
        Returns:
            Criterion entry dictionary
        """
        interpreted_data = interpreted.get('interpreted_criterion', {})
        
        # Generate matching conditions
        matching_conditions = self.generate_matching_rules(interpreted_data)
        
        # Extract qualifiers
        qualifiers = interpreted_data.get('qualifiers', {})
        
        # Extract dependencies
        dependencies = interpreted_data.get('dependencies', [])
        
        return {
            "criterion_id": interpreted['criterion_id'],
            "criterion_text": interpreted['criterion_text'],
            "priority": "high",  # Could be customized based on clinical category
            "clinical_category": interpreted_data.get('clinical_category', 'general'),
            "primary_condition": interpreted_data.get('primary_condition', {}),
            "matching_conditions": matching_conditions,
            "qualifiers": {
                "severity": qualifiers.get('severity', []),
                "temporal": qualifiers.get('temporal', ''),
                "persistence": qualifiers.get('persistence', '')
            },
            "dependencies": dependencies
        }
    
    def generate_matching_rules(self, interpreted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate executable matching rules from interpreted data.
        
        Args:
            interpreted_data: Interpreted criterion data
            
        Returns:
            Matching rules dictionary
        """
        # Get related clinical findings
        findings = interpreted_data.get('related_clinical_findings', [])
        
        if not findings:
            # If no specific findings, use primary condition as text match
            return {
                "logic_operator": "OR",
                "description": f"Match based on primary condition: {interpreted_data.get('primary_condition', {}).get('term', 'unknown')}",
                "conditions": []
            }
        
        # Convert findings to matching conditions
        conditions = []
        for finding in findings:
            condition = self._create_matching_condition(finding)
            conditions.append(condition)
        
        # Determine logic operator (OR is more permissive for admission criteria)
        logic_operator = "OR" if len(conditions) > 1 else "SINGLE"
        
        return {
            "logic_operator": logic_operator,
            "description": f"Match if any of the following clinical findings are present",
            "conditions": conditions
        }
    
    def _create_matching_condition(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a matching condition from a clinical finding.
        
        Args:
            finding: Clinical finding dictionary
            
        Returns:
            Matching condition dictionary
        """
        # Determine data type
        data_type = self._determine_data_type(finding['finding'])
        
        # Parse operator
        operator = finding.get('operator', 'equals')
        
        # Parse value
        value = finding.get('value')
        if value is None and finding.get('threshold'):
            try:
                value = float(finding['threshold'])
            except (ValueError, TypeError):
                value = finding['threshold']  # Keep as string if not numeric
        
        return {
            "data_type": data_type,
            "parameter": finding['finding'],
            "value": value,
            "unit": finding.get('unit', ''),
            "operator": operator,
            "loinc_code": finding.get('loinc_code', ''),
            "snomed_code": finding.get('snomed_code', ''),
            "threshold_text": finding.get('threshold', '')
        }
    
    def _determine_data_type(self, finding_name: str) -> str:
        """
        Determine data type from finding name.
        
        Args:
            finding_name: Name of the clinical finding
            
        Returns:
            Data type string
        """
        finding_lower = finding_name.lower()
        
        # Vital signs
        vital_sign_keywords = [
            'blood pressure', 'heart rate', 'pulse', 'temperature', 
            'respiratory rate', 'oxygen saturation', 'spo2'
        ]
        if any(keyword in finding_lower for keyword in vital_sign_keywords):
            return "vital_sign"
        
        # Laboratory tests
        lab_keywords = [
            'platelet', 'culture', 'blood count', 'hemoglobin', 'creatinine',
            'bilirubin', 'lactate', 'wbc', 'glucose', 'electrolyte'
        ]
        if any(keyword in finding_lower for keyword in lab_keywords):
            return "laboratory"
        
        # Clinical assessments
        assessment_keywords = [
            'glasgow coma', 'mental status', 'consciousness', 'delirium',
            'confusion', 'orientation'
        ]
        if any(keyword in finding_lower for keyword in assessment_keywords):
            return "clinical_assessment"
        
        # Default to clinical finding
        return "clinical_finding"
    
    def _build_alternatives(self, alternatives_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build alternatives to admission section.
        
        Args:
            alternatives_data: List of alternative options
            
        Returns:
            Formatted alternatives list
        """
        if not self.schema_config.get('include_alternatives', True):
            return []
        
        formatted_alternatives = []
        for alt in alternatives_data:
            formatted_alternatives.append({
                "alternative_id": alt.get('alternative_id', ''),
                "description": alt.get('alternative_text', ''),
                "care_setting": alt.get('care_setting', 'alternative_care'),
                "requirements": []  # Could be expanded with parsed requirements
            })
        
        return formatted_alternatives
    
    def validate_schema(self, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate schema structure and content.
        
        Args:
            schema: Schema dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required top-level fields
        required_fields = [
            'schema_version',
            'guideline_metadata',
            'admission_decision_logic'
        ]
        
        for field in required_fields:
            if field not in schema:
                errors.append(f"Missing required field: {field}")
        
        # Validate metadata
        if 'guideline_metadata' in schema:
            metadata = schema['guideline_metadata']
            if not metadata.get('guideline_id'):
                errors.append("guideline_metadata missing guideline_id")
            if not metadata.get('guideline_name'):
                errors.append("guideline_metadata missing guideline_name")
        
        # Validate admission logic
        if 'admission_decision_logic' in schema:
            logic = schema['admission_decision_logic']
            if 'criteria' not in logic:
                errors.append("admission_decision_logic missing criteria list")
            elif not isinstance(logic['criteria'], list):
                errors.append("admission_decision_logic criteria must be a list")
            elif len(logic['criteria']) == 0:
                errors.append("admission_decision_logic criteria list is empty")
        
        # Validate each criterion
        if 'admission_decision_logic' in schema and 'criteria' in schema['admission_decision_logic']:
            for i, criterion in enumerate(schema['admission_decision_logic']['criteria']):
                if 'criterion_id' not in criterion:
                    errors.append(f"Criterion {i} missing criterion_id")
                if 'criterion_text' not in criterion:
                    errors.append(f"Criterion {i} missing criterion_text")
                if 'matching_conditions' not in criterion:
                    errors.append(f"Criterion {i} missing matching_conditions")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Schema validation passed")
        else:
            logger.warning(f"Schema validation failed with {len(errors)} errors")
            for error in errors:
                logger.warning(f"  - {error}")
        
        return is_valid, errors
    
    def export_schema(self, schema: Dict[str, Any], output_path: str) -> None:
        """
        Export schema to JSON file.
        
        Args:
            schema: Schema dictionary
            output_path: Path to output file
        """
        # Create output directory if it doesn't exist
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON with pretty formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Schema exported to: {output_path}")
        
        # Also export a summary
        summary_path = output_path.replace('.json', '_summary.txt')
        self._export_summary(schema, summary_path)
    
    def _export_summary(self, schema: Dict[str, Any], summary_path: str) -> None:
        """
        Export human-readable summary of schema.
        
        Args:
            schema: Schema dictionary
            summary_path: Path to summary file
        """
        lines = []
        lines.append("=" * 80)
        lines.append("MCG GUIDELINE SCHEMA SUMMARY")
        lines.append("=" * 80)
        lines.append("")
        
        # Metadata
        metadata = schema.get('guideline_metadata', {})
        lines.append("GUIDELINE INFORMATION")
        lines.append("-" * 80)
        lines.append(f"Name: {metadata.get('guideline_name', 'Unknown')}")
        lines.append(f"ID: {metadata.get('guideline_id', 'Unknown')}")
        lines.append(f"Version: {metadata.get('version', 'Unknown')}")
        lines.append(f"Effective Date: {metadata.get('effective_date', 'Unknown')}")
        lines.append(f"Specialty: {metadata.get('specialty', 'Unknown')}")
        lines.append("")
        
        # Admission criteria
        logic = schema.get('admission_decision_logic', {})
        criteria = logic.get('criteria', [])
        lines.append("ADMISSION CRITERIA")
        lines.append("-" * 80)
        lines.append(f"Total Criteria: {len(criteria)}")
        lines.append(f"Rule Type: {logic.get('rule_type', 'Unknown')}")
        lines.append("")
        
        # List each criterion
        for i, criterion in enumerate(criteria, 1):
            lines.append(f"{i}. {criterion.get('criterion_id', 'Unknown')}")
            lines.append(f"   Category: {criterion.get('clinical_category', 'Unknown')}")
            lines.append(f"   Text: {criterion.get('criterion_text', 'Unknown')[:100]}...")
            
            # Matching conditions
            matching = criterion.get('matching_conditions', {})
            conditions = matching.get('conditions', [])
            if conditions:
                lines.append(f"   Matching Conditions: {len(conditions)}")
                for cond in conditions[:3]:  # Show first 3
                    lines.append(f"     - {cond.get('parameter', 'Unknown')} {cond.get('operator', '')} {cond.get('value', '')}")
            lines.append("")
        
        # Alternatives
        alternatives = schema.get('alternatives_to_admission', [])
        if alternatives:
            lines.append("ALTERNATIVES TO ADMISSION")
            lines.append("-" * 80)
            for alt in alternatives:
                lines.append(f"- {alt.get('description', 'Unknown')[:80]}")
            lines.append("")
        
        # Write summary
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Summary exported to: {summary_path}")


def build_guideline_schema(
    metadata: Dict[str, Any],
    parsed_data: Dict[str, Any],
    interpreted_data: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convenience function to build guideline schema.
    
    Args:
        metadata: Metadata from PDF extraction
        parsed_data: Parsed structure from module 2
        interpreted_data: Interpreted criteria from module 3
        config: Configuration dictionary
        
    Returns:
        Complete schema dictionary
    """
    builder = SchemaBuilder(config)
    return builder.build_guideline_schema(metadata, parsed_data, interpreted_data)


if __name__ == "__main__":
    # Test the module independently
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create test data
    test_metadata = {
        "guideline_name": "Sepsis and Other Febrile Illness without Focal Infection",
        "org_code": "12345",
        "edition": "27th",
        "effective_date": "January 1, 2024"
    }
    
    test_parsed = {
        "admission_criteria": {
            "rule_type": "one_or_more",
            "criteria_list": []
        },
        "alternatives_to_admission": []
    }
    
    test_interpreted = []
    
    try:
        builder = SchemaBuilder(config)
        schema = builder.build_guideline_schema(test_metadata, test_parsed, test_interpreted)
        
        # Validate
        is_valid, errors = builder.validate_schema(schema)
        print(f"\nSchema validation: {'PASSED' if is_valid else 'FAILED'}")
        if errors:
            for error in errors:
                print(f"  - {error}")
        
        print(f"Schema structure created successfully")
        print(f"Guideline ID: {schema['guideline_metadata']['guideline_id']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
