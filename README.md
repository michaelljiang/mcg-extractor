# MCG Criteria Extraction System

## Project Overview

The **MCG (Milliman Care Guidelines) Criteria Extraction System** is a production-ready Python application that automatically extracts, structures, and interprets clinical admission criteria from MCG guideline PDFs. This system transforms unstructured PDF content into machine-readable JSON schemas that can be used for automated clinical decision support and patient matching against H&P (History & Physical) documents.

### What This System Does

1. **Extracts** text and metadata from MCG guideline PDFs
2. **Parses** clinical admission criteria with qualifiers and conditions
3. **Interprets** medical terminology using AI (Google Gemini)
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

- Uses Google Gemini AI to interpret clinical concepts
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
- Model: `gemini-2.0-flash-exp` or `gemini-1.5-pro`
- Library: `google-genai` (NOT deprecated `google-generativeai`)
- Temperature: 0.1 (for consistency)
- Includes response caching and retry logic

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

## Installation

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)
- Google Gemini API key

### Step-by-Step Setup

1. **Clone or navigate to the project directory:**

```powershell
cd C:\Users\Michael\Desktop\AHMC
```

2. **Create and activate virtual environment (if not already done):**

```powershell
python -m venv venv
.\venv\Scripts\activate
```

3. **Install dependencies:**

```powershell
pip install -r requirements.txt
```

4. **Set up environment variables:**

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your_gemini_api_key_here
```

To get a Google Gemini API key:
- Visit https://makersuite.google.com/app/apikey
- Create a new API key
- Copy it to your `.env` file

5. **Verify installation:**

```powershell
python -c "import yaml, pdfplumber; from google import genai; print('All dependencies installed!')"
```

---

## Configuration

### config.yaml

The `config.yaml` file controls all system behavior. Key sections:

#### Paths Configuration
```yaml
paths:
  input_pdf_dir: "uploads/mcg-guidelines"  # Input PDF directory
  output_schema_dir: "data/output/schemas"  # Output JSON directory
  temp_dir: "data/temp"                     # Temporary files
  logs_dir: "logs"                          # Log files
```

#### LLM Settings
```yaml
llm:
  provider: "google"
  model: "gemini-2.0-flash-exp"  # Or "gemini-1.5-pro"
  api_key_env_var: "GOOGLE_API_KEY"
  temperature: 0.1  # Low for consistency
  max_tokens: 8000
  retry_attempts: 3
```

#### Parser Settings
```yaml
parser:
  section_headers:
    - "Clinical Indications for Admission to Inpatient Care"
    - "Alternatives to Admission"
    - "Optimal Recovery Course"
```

#### Logging
```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file_output: true
  console_output: true
```

---

## Usage

### Command-Line Interface

#### Process a Single PDF

```powershell
python main.py --pdf "uploads/mcg-guidelines/MCG Sepsis and Other Febrile Illness, without Focal Infection (1).pdf"
```

#### Specify Custom Output Directory

```powershell
python main.py --pdf "path/to/guideline.pdf" --output "output/schemas/"
```

#### Batch Process Multiple PDFs

```powershell
python main.py --batch --input-dir "uploads/mcg-guidelines/"
```

#### Use Custom Configuration

```powershell
python main.py --pdf "guideline.pdf" --config "custom_config.yaml"
```

### Expected Output

When processing completes successfully:

```
================================================================================
PIPELINE COMPLETED SUCCESSFULLY
================================================================================
Schema exported to: data/output/schemas/mcg_sepsis_and_other_febrile_illness_without_focal_infection.json

✓ Processing completed successfully!
```

### Output Files

1. **JSON Schema:** `<guideline_id>.json` - Machine-readable schema
2. **Summary:** `<guideline_id>_summary.txt` - Human-readable summary
3. **Log File:** `logs/mcg_extraction_<timestamp>.log` - Execution log
4. **Report:** `logs/report_<timestamp>.txt` - Execution report

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

### Example Matching Code (Pseudocode)

```python
def check_admission_criteria(patient_data, mcg_schema):
    criteria = mcg_schema['admission_decision_logic']['criteria']
    
    for criterion in criteria:
        if evaluate_criterion(patient_data, criterion):
            return {
                "admission_indicated": True,
                "matched_criterion": criterion['criterion_id'],
                "reason": criterion['criterion_text']
            }
    
    return {"admission_indicated": False}

def evaluate_criterion(patient_data, criterion):
    conditions = criterion['matching_conditions']['conditions']
    logic_op = criterion['matching_conditions']['logic_operator']
    
    results = []
    for condition in conditions:
        patient_value = get_patient_value(patient_data, condition)
        threshold = condition['value']
        
        if condition['operator'] == 'less_than':
            results.append(patient_value < threshold)
        # ... other operators
    
    if logic_op == 'OR':
        return any(results)
    elif logic_op == 'AND':
        return all(results)
```

---

## Testing

### Running Tests

#### Run All Tests
```powershell
pytest -v
```

#### Run Specific Module Tests
```powershell
pytest test_module_1.py -v
pytest test_module_2.py -v
pytest test_module_3.py -v
pytest test_module_4.py -v
```

#### Run Integration Tests
```powershell
pytest test_integration.py -v -m integration
```

#### Run with Coverage
```powershell
pytest --cov=. --cov-report=html
```

### Test Structure

- **test_module_1.py** - PDF extraction tests
- **test_module_2.py** - Structure parsing tests
- **test_module_3.py** - LLM interpretation tests (mocked)
- **test_module_4.py** - Schema building tests
- **test_integration.py** - End-to-end pipeline tests

---

## Module Documentation

### Module 1: PDF Extraction

#### Class: `PDFExtractor`

**Purpose:** Extract structured content from MCG PDFs

**Methods:**

##### `extract_pdf_content(pdf_path: str) -> Dict`
Extracts complete PDF content including text, metadata, and sections.

**Parameters:**
- `pdf_path` (str): Path to PDF file

**Returns:**
- Dictionary with keys: `metadata`, `sections`, `full_text`

##### `extract_metadata(pdf_path: str, text: str) -> Dict`
Extracts guideline metadata using pattern matching.

**Extracted Fields:**
- `guideline_name` - Name of the guideline
- `org_code` - MCG organization code
- `edition` - Version/edition number
- `effective_date` - Effective date
- `specialty` - Medical specialty

##### `identify_sections(text: str) -> List[Dict]`
Identifies major document sections by headers.

**Returns:**
- List of section dictionaries with `section_name`, `page_number`, `raw_text`, `formatting_markers`

---

### Module 2: Structure Parser

#### Class: `CriteriaParser`

**Purpose:** Parse admission criteria from extracted text

**Methods:**

##### `parse_admission_criteria(extracted_data: Dict) -> Dict`
Main parsing function that processes all criteria.

**Returns:**
```python
{
  "admission_criteria": {
    "rule_type": "one_or_more",
    "criteria_list": [...]
  },
  "alternatives_to_admission": [...]
}
```

##### `extract_criterion_components(criterion_text: str, criterion_id: int) -> Dict`
Extracts components from a single criterion.

**Extracted Components:**
- Primary condition
- Qualifiers (severity, temporal)
- Conditional requirements
- Persistence requirements
- Clinical category

---

### Module 3: LLM Interpreter

#### Class: `LLMInterpreter`

**Purpose:** Interpret criteria using Google Gemini AI

**Methods:**

##### `interpret_criteria(parsed_data: Dict) -> List[Dict]`
Interprets all criteria in batch.

##### `interpret_criterion(criterion: Dict) -> Dict`
Interprets a single criterion using LLM.

**Returns:**
```python
{
  "criterion_id": str,
  "criterion_text": str,
  "interpreted_criterion": {
    "primary_condition": {...},
    "related_clinical_findings": [...],
    "qualifiers": {...},
    "dependencies": [...],
    "clinical_category": str
  }
}
```

##### `normalize_terminology(term: str, terminology_type: str) -> Dict`
Maps medical terms to standard codes.

**Features:**
- Response caching (avoids redundant API calls)
- Exponential backoff retry logic
- Error handling with fallback to minimal structure

---

### Module 4: Schema Builder

#### Class: `SchemaBuilder`

**Purpose:** Build and validate final JSON schema

**Methods:**

##### `build_guideline_schema(metadata: Dict, parsed_data: Dict, interpreted_data: List) -> Dict`
Builds complete schema from all pipeline outputs.

##### `generate_matching_rules(interpreted_data: Dict) -> Dict`
Generates executable matching conditions with operators and thresholds.

##### `validate_schema(schema: Dict) -> Tuple[bool, List[str]]`
Validates schema structure and completeness.

**Returns:**
- `(True, [])` if valid
- `(False, [list of errors])` if invalid

##### `export_schema(schema: Dict, output_path: str) -> None`
Exports schema to JSON file and generates summary.

---

## Troubleshooting

### Common Issues

#### 1. API Key Not Found
**Error:** `ValueError: API key not found in environment variable: GOOGLE_API_KEY`

**Solution:**
- Create `.env` file with `GOOGLE_API_KEY=your_key`
- Or set environment variable: `$env:GOOGLE_API_KEY="your_key"`

#### 2. PDF Not Found
**Error:** `FileNotFoundError: PDF file not found`

**Solution:**
- Check PDF path is correct
- Use absolute path or ensure relative path is from project root
- Check file permissions

#### 3. Module Import Errors
**Error:** `ModuleNotFoundError: No module named 'google.genai'`

**Solution:**
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`
- Verify you're using `google-genai` not `google-generativeai`

#### 4. LLM Rate Limiting
**Error:** API quota exceeded or rate limit errors

**Solution:**
- System includes retry logic with exponential backoff
- Check your API quota at Google AI Studio
- Reduce batch size or add delay between requests

#### 5. Schema Validation Errors

**Solution:**
- Check logs for specific validation error messages
- Verify input PDF is a valid MCG guideline
- Review extracted criteria in log files

### Debug Mode

Enable debug logging in `config.yaml`:

```yaml
logging:
  level: "DEBUG"
```

This provides detailed output for each processing stage.

---

## Development Guide

### Extending the System

#### Adding New Section Parsers

1. Add section name to `config.yaml`:
```yaml
parser:
  section_headers:
    - "Your New Section Name"
```

2. Implement parser in `module_2_structure_parser.py`

#### Adding New Medical Code Systems

1. Update LLM prompt in `module_3_llm_interpreter.py`
2. Add fields to schema in `module_4_schema_builder.py`

#### Custom Matching Logic

Modify `generate_matching_rules()` in `module_4_schema_builder.py` to implement custom logic.

### Code Style

- **PEP 8** compliance
- **Type hints** for all function signatures
- **Docstrings** for all public functions
- **Error handling** with try-except blocks
- **Logging** at appropriate levels (INFO, WARNING, ERROR)

---

## Contributing

### Development Workflow

1. Create feature branch
2. Implement changes with tests
3. Run test suite: `pytest -v`
4. Update documentation
5. Submit pull request

### Testing New Features

- Write unit tests for new functions
- Add integration tests for new modules
- Ensure 80%+ code coverage

---

## Project Structure

```
AHMC/
├── config.yaml                      # Configuration file
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (not in git)
├── README.md                       # This file
│
├── main.py                         # Main orchestration script
├── module_1_pdf_extraction.py      # PDF extraction module
├── module_2_structure_parser.py    # Structure parsing module
├── module_3_llm_interpreter.py     # LLM interpretation module
├── module_4_schema_builder.py      # Schema building module
│
├── test_module_1.py                # Module 1 tests
├── test_module_2.py                # Module 2 tests
├── test_module_3.py                # Module 3 tests
├── test_module_4.py                # Module 4 tests
├── test_integration.py             # Integration tests
│
├── uploads/
│   └── mcg-guidelines/             # Input PDFs
│       └── MCG Sepsis and Other Febrile Illness, without Focal Infection (1).pdf
│
├── data/
│   ├── output/
│   │   └── schemas/                # Generated JSON schemas
│   └── temp/                       # Temporary files
│
├── logs/                           # Log files
│   ├── mcg_extraction_*.log
│   ├── report_*.txt
│   └── batch_summary_*.txt
│
└── venv/                           # Virtual environment
```

---

## Dependencies

### Core Dependencies

- **pdfplumber** (0.11.0) - PDF text extraction with layout preservation
- **PyPDF2** (3.0.1) - Fallback PDF extraction
- **google-genai** (0.2.1) - Google Gemini API client (NEW package)
- **pyyaml** (6.0.1) - Configuration file handling
- **jsonschema** (4.21.1) - Schema validation
- **python-dotenv** (1.0.0) - Environment variable management
- **tqdm** (4.66.1) - Progress bars

### Testing Dependencies

- **pytest** (8.0.0) - Testing framework
- **pytest-cov** (4.1.0) - Coverage reporting

---

## License

This is a proprietary system for healthcare organization use.

---

## Support

For issues or questions:
1. Check this README and troubleshooting section
2. Review log files in `logs/` directory
3. Run tests to verify system integrity
4. Check API key and environment setup

---

## Success Criteria Checklist

- [x] Successfully extracts all admission criteria from Sepsis guideline
- [x] Maps clinical terms to standard codes (SNOMED, ICD-10, LOINC)
- [x] Generates executable matching conditions with thresholds
- [x] Produces valid, well-structured JSON schema
- [x] Runs without errors on provided sample PDF
- [x] Documented for developer use
- [x] Handles edge cases gracefully (missing data, malformed content)
- [x] Production-ready error handling and logging
- [x] Comprehensive test coverage
- [x] Modular, maintainable architecture

---

## Version History

**Version 1.0** (February 2026)
- Initial release
- 4-module pipeline architecture
- Google Gemini AI integration
- Full test coverage
- Comprehensive documentation

---

**Built with ❤️ for healthcare organizations to improve clinical decision support.**
