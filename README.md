# MCG Criteria Extraction System

> **Note:** This documentation was enhanced with AI assistance to improve readability and presentation.

**Quick Links:**
- 📄 [Sepsis Criteria JSON](data/mcg_health.json) - Example of extracted MCG guideline in JSON format
- 📋 [Clinical Data Extraction Methodology](answers.md) - Answers to follow-up questions

## Project Overview

Python application that automatically extracts, structures, and interprets clinical admission criteria from MCG guideline PDFs. This system transforms unstructured PDF content into machine-readable JSON schemas that can be used for automated clinical decision support and patient matching against H&P (History & Physical) documents.

### What This System Does

1. **Extracts** text and metadata from MCG guideline PDFs
2. **Parses** clinical admission criteria with qualifiers and conditions
3. **Interprets** medical terminology using AI (Ollama local LLM)
4. **Structures** criteria into executable matching rules with standard medical codes (SNOMED CT, ICD-10, LOINC)
5. **Exports** comprehensive JSON schemas for downstream consumption

### Key Features

- ✅ Modular 4-stage pipeline architecture
- ✅ AI-powered clinical concept interpretation
- ✅ Medical terminology normalization (SNOMED, ICD-10, LOINC)
- ✅ Quantitative threshold extraction with comparison operators
- ✅ Comprehensive error handling and logging
- ✅ Batch processing support
- ✅ Full test coverage
- ✅ Production-ready code quality

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCG EXTRACTION PIPELINE                      │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ MODULE 1 │      │ MODULE 2 │      │ MODULE 3 │      │ MODULE 4 │
    │   PDF    │ ───> │ STRUCTURE│ ───> │   LLM    │ ───> │  SCHEMA  │
    │EXTRACTION│      │  PARSER  │      │INTERPRET │      │ BUILDER  │
    └──────────┘      └──────────┘      └──────────┘      └──────────┘
         │                  │                  │                  │
         ▼                  ▼                  ▼                  ▼
     Raw Text        Parsed Criteria    Interpreted Data    JSON Schema
     Metadata        Qualifiers         Medical Codes       Matching Rules
     Sections        Thresholds         Clinical Codes      Validation
```

### Module Breakdown

#### Module 1: PDF Text Extraction
**File:** `module_1_pdf_extraction.py`

- Extracts text from PDF page by page
- Preserves formatting (bullets, indentation, numbering)
- Extracts metadata (guideline name, ORG code, edition)
- Identifies major sections by headers

**Key Functions:**
- `extract_pdf_content()` - Main extraction function
- `extract_metadata()` - Extract guideline metadata
- `identify_sections()` - Find major document sections

#### Module 2: Structure Parser
**File:** `module_2_structure_parser.py`

- Parses "Clinical Indications for Admission" section
- Extracts individual criteria from bullet points
- Identifies qualifiers (severe, persistent, acute, etc.)
- Extracts conditional clauses and temporal requirements
- Parses "Alternatives to Admission" section

**Key Functions:**
- `parse_admission_criteria()` - Main parsing function
- `extract_criterion_components()` - Extract criterion parts
- `_extract_qualifiers()` - Find severity/temporal qualifiers
- `_determine_clinical_category()` - Categorize criteria

#### Module 3: LLM-Based Interpreter
**File:** `module_3_llm_interpreter.py`

- Uses Ollama to run local LLMs for clinical concept interpretation
- Normalizes medical terminology to standard codes
- Extracts quantitative thresholds with operators
- Identifies clinical findings and their relationships
- Analyzes dependencies and conditional logic

**Key Functions:**
- `interpret_criteria()` - Batch interpretation
- `interpret_criterion()` - Single criterion interpretation
- `normalize_terminology()` - Map to standard codes
- `identify_thresholds()` - Extract quantitative values

**LLM Configuration:**
- Provider: Ollama (local inference)
- Model: `qwen2.5:32b` (configurable)
- API: REST API via `requests` library
- Temperature: 0.1 (for consistency)
- Includes retry logic and error handling
- Supports GPU acceleration via Ollama

#### Module 4: Schema Builder
**File:** `module_4_schema_builder.py`

- Combines all parsed and interpreted data
- Generates executable matching rules with boolean logic
- Validates schema structure and content
- Exports JSON schema and human-readable summary

**Key Functions:**
- `build_guideline_schema()` - Build complete schema
- `generate_matching_rules()` - Create matching conditions
- `validate_schema()` - Check schema validity
- `export_schema()` - Export to JSON file

---

## Output Schema Structure

### JSON Schema Format

```json
{
  "schema_version": "1.0",
  "schema_created": "2024-01-15T10:30:00",
  
  "guideline_metadata": {
    "guideline_id": "mcg_sepsis_and_other_febrile_illness_without_focal_infection",
    "guideline_name": "Sepsis and Other Febrile Illness without Focal Infection",
    "org_code": "ORG12345",
    "version": "27th Edition",
    "effective_date": "January 1, 2024",
    "specialty": "Emergency Medicine",
    "care_setting": "inpatient"
  },
  
  "admission_decision_logic": {
    "rule_type": "disjunctive",
    "description": "Patient meets admission criteria if ANY condition is met",
    "minimum_criteria_count": 1,
    
    "criteria": [
      {
        "criterion_id": "criterion_001",
        "criterion_text": "Hemodynamic instability with systolic BP <90 mmHg",
        "priority": "high",
        "clinical_category": "hemodynamic",
        
        "primary_condition": {
          "term": "Hemodynamic Instability",
          "snomed_code": "234171009",
          "icd10_codes": ["R57.9"],
          "synonyms": ["Circulatory instability", "Shock"]
        },
        
        "matching_conditions": {
          "logic_operator": "OR",
          "description": "Match if any clinical finding is present",
          "conditions": [
            {
              "data_type": "vital_sign",
              "parameter": "Systolic Blood Pressure",
              "value": 90,
              "unit": "mmHg",
              "operator": "less_than",
              "loinc_code": "8480-6",
              "snomed_code": "271649006"
            }
          ]
        },
        
        "qualifiers": {
          "severity": ["severe"],
          "temporal": "",
          "persistence": ""
        },
        
        "dependencies": []
      }
    ]
  },
  
  "alternatives_to_admission": [
    {
      "alternative_id": "alt_001",
      "description": "Observation unit placement for up to 24 hours",
      "care_setting": "observation_unit"
    }
  ]
}
```

### Key Schema Fields

#### Matching Conditions

Each criterion includes `matching_conditions` that define how to match patient data:

- **data_type:** `vital_sign`, `laboratory`, `clinical_assessment`, `clinical_finding`
- **parameter:** Name of the clinical parameter (e.g., "Systolic Blood Pressure")
- **value:** Numeric threshold value
- **unit:** Unit of measurement (e.g., "mmHg", "per minute")
- **operator:** Comparison operator:
  - `less_than` - Value < threshold
  - `greater_than` - Value > threshold
  - `equals` - Value = threshold
  - `between` - threshold_min < Value < threshold_max
  - `contains` - Text/string matching
- **loinc_code:** LOINC code for lab tests/vital signs
- **snomed_code:** SNOMED CT code for clinical findings

#### Medical Codes

- **SNOMED CT:** Clinical findings and conditions
- **ICD-10:** Diagnoses
- **LOINC:** Laboratory tests and vital signs

---

## Matching Logic

### How to Use the Schema for Patient Matching

The schema enables this workflow:

1. **Load Patient Data** (H&P document as structured JSON)
```json
{
  "vital_signs": {
    "systolic_blood_pressure": {"value": 85, "unit": "mmHg"},
    "heart_rate": {"value": 110, "unit": "bpm"}
  },
  "laboratory": {
    "platelet_count": {"value": 95000, "unit": "per microliter"}
  }
}
```

2. **Load MCG Schema** for relevant guideline

3. **For each criterion:**
   - Extract `matching_conditions`
   - For each condition in conditions:
     - Match by parameter name or LOINC/SNOMED code
     - Apply comparison operator
     - Check if patient value meets threshold
   - Apply `logic_operator` (OR/AND)

4. **If ANY criterion matches** → Admission indicated

5. **Generate report** showing which criteria were satisfied


## Dependencies

### Core Dependencies

- **pdfplumber** (0.11.0) - PDF text extraction with layout preservation
- **PyPDF2** (3.0.1) - Fallback PDF extraction
- **requests** (2.31.0) - HTTP client for Ollama API communication
- **pyyaml** (6.0.1) - Configuration file handling
- **jsonschema** (4.21.1) - Schema validation
- **python-dotenv** (1.0.0) - Environment variable management
- **tqdm** (4.66.1) - Progress bars

### LLM Dependencies

- **Ollama** - Local LLM inference engine (must be installed separately)
  - Download from: https://ollama.ai
  - Recommended model: `qwen2.5:32b` (run `ollama pull qwen2.5:32b`)

### Testing Dependencies

- **pytest** (8.0.0) - Testing framework
- **pytest-cov** (4.1.0) - Coverage reporting

---
