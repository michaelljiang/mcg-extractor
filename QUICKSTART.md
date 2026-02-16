# MCG Criteria Extraction System - Quick Start Guide

Get up and running with the MCG Criteria Extraction System in 5 minutes.

---

## Prerequisites

- **Python 3.8+** installed
- **Google Gemini API Key** (free tier works)
- **MCG PDF guideline** to process

---

## 1. Setup Environment

### Clone/Download the Project
```bash
cd C:\Users\Michael\Desktop\AHMC
```

### Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Install Dependencies
```powershell
pip install -r requirements.txt
```

**Dependencies installed:**
- `pdfplumber` - PDF text extraction
- `PyPDF2` - PDF fallback extraction
- `google-genai` - Gemini API client
- `pyyaml` - Configuration files
- `jsonschema` - Schema validation
- `python-dotenv` - Environment variables
- `tqdm` - Progress bars
- `pytest` - Testing framework
- `requests` - HTTP requests

---

## 2. Configure Google Gemini API

### Get API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **"Get API Key"** or **"Create API Key"**
3. Copy your API key

### Set Environment Variable

**Option A: Create `.env` file (Recommended)**
```bash
# Create .env file in project root
echo GOOGLE_API_KEY=your_api_key_here > .env
```

**Option B: Set System Environment Variable**
```powershell
# Windows PowerShell
$env:GOOGLE_API_KEY="your_api_key_here"
```

### Verify API Key
```powershell
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key loaded!' if os.getenv('GOOGLE_API_KEY') else 'API Key missing!')"
```

---

## 3. Add Your PDF Guidelines

Place MCG PDF files in the `uploads/mcg-guidelines/` directory:

```
uploads/
  mcg-guidelines/
    MCG Sepsis and Other Febrile Illness, without Focal Infection (1).pdf
    your-other-guideline.pdf
```

---

## 4. Run the Extraction Pipeline

### Basic Usage
```powershell
python main.py --pdf "uploads/mcg-guidelines/MCG Sepsis and Other Febrile Illness, without Focal Infection (1).pdf"
```

### With Custom Output Directory
```powershell
python main.py --pdf "path/to/guideline.pdf" --output "custom/output/path"
```

### Batch Process Multiple PDFs
```powershell
python main.py --batch "uploads/mcg-guidelines/"
```

---

## 5. Pipeline Stages

The system runs 4 stages automatically:

### **Stage 1: PDF Text Extraction**
- Extracts text with formatting preservation
- Identifies section headers
- Captures page numbers
- **Output:** Structured text sections

### **Stage 2: Structure Parsing**
- Parses admission criteria lists
- Extracts qualifiers and conditions
- Identifies clinical categories
- **Output:** Structured criteria dictionaries

### **Stage 3: LLM Interpretation** (Gemini AI)
- Interprets clinical concepts
- Maps to SNOMED CT, ICD-10, LOINC codes
- Extracts matching conditions
- **Output:** Enriched criteria with medical codes

### **Stage 4: Schema Building**
- Builds unified JSON schema
- Generates matching rules
- Validates schema structure
- **Output:** Production-ready JSON schema

---

## 6. View Results

### Generated Files

**Schema Output:**
```
data/output/schemas/
  mcg_sepsis_and_other_febrile_illness_without_focal_infection.json
  mcg_sepsis_and_other_febrile_illness_without_focal_infection_summary.txt
```

**Logs:**
```
logs/
  mcg_extraction_20260215_183413.log
  report_20260215_183413.txt
```

### Schema Structure
```json
{
  "schema_version": "1.0",
  "guideline_metadata": { ... },
  "admission_decision_logic": {
    "rule_type": "disjunctive",
    "criteria": [
      {
        "criterion_id": "criterion_001",
        "criterion_text": "Hemodynamic instability",
        "primary_condition": {
          "term": "Hemodynamic Instability",
          "snomed_code": "234171009",
          "icd10_codes": ["R57.9"]
        },
        "matching_conditions": {
          "conditions": [
            {
              "parameter": "Systolic Blood Pressure",
              "value": 90,
              "operator": "less_than",
              "loinc_code": "8480-6"
            }
          ]
        }
      }
    ]
  },
  "alternatives_to_admission": [ ... ]
}
```

---

## 7. Configuration

Edit `config.yaml` to customize behavior:

### LLM Settings
```yaml
llm:
  model: "gemini-2.0-flash"  # Free tier model
  temperature: 0.1
  max_tokens: 8000
```

**Available Free Tier Models:**
- `gemini-2.5-flash` - Latest, fastest
- `gemini-2.0-flash` - Stable, reliable
- `gemini-flash-latest` - Always latest

### Parser Settings
```yaml
parser:
  section_headers:
    - "Clinical Indications for Admission to Inpatient Care"
    - "Alternatives to Admission"
    - "Optimal Recovery Course"
```

### Medical Codes
```yaml
terminology:
  use_snomed: true
  use_icd10: true
  use_loinc: true
```

---

## 8. Troubleshooting

### Common Issues

**1. API Key Not Found**
```
ERROR: GOOGLE_API_KEY not found in environment
```
**Solution:** Create `.env` file or set environment variable

**2. Model Not Available**
```
404 NOT_FOUND: models/gemini-2.5-pro is not found
```
**Solution:** Switch to free tier model (`gemini-2.0-flash`)

**3. No Criteria Extracted**
```
Parsed 0 admission criteria
```
**Solution:** Check PDF format and section headers in config

**4. JSON Parse Error**
```
Failed to parse JSON response: Unterminated string
```
**Solution:** System auto-retries with fallback parsing (already fixed)

### Check Logs
```powershell
# View latest log
Get-Content logs\mcg_extraction_*.log | Select-Object -Last 50
```

### Run Tests
```powershell
pytest tests/ -v
```

---

## 9. Example Workflow

```powershell
# 1. Activate environment
.\venv\Scripts\activate

# 2. Process a guideline
python main.py --pdf "uploads/mcg-guidelines/sepsis.pdf"

# 3. Check output
cat data\output\schemas\mcg_sepsis_and_other_febrile_illness_without_focal_infection.json

# 4. View summary
cat data\output\schemas\mcg_sepsis_and_other_febrile_illness_without_focal_infection_summary.txt

# 5. Check logs if needed
cat logs\mcg_extraction_*.log
```

---

## 10. Next Steps

- **Process More Guidelines:** Add PDFs to `uploads/mcg-guidelines/`
- **Customize Extraction:** Edit `config.yaml` section headers
- **Integrate Schemas:** Use generated JSON in your EHR system
- **Batch Processing:** Process entire directories
- **Review Documentation:** See `README.md` for detailed information

---

## Support

For detailed documentation, see:
- **README.md** - Complete system documentation
- **DELIVERABLES.md** - Full deliverables checklist
- **sample_output_schema.json** - Example output structure

---

## System Requirements

- **Python:** 3.8 or higher
- **RAM:** 2GB minimum
- **Disk:** 500MB for system + space for PDFs
- **Internet:** Required for Gemini API calls
- **OS:** Windows, macOS, or Linux

---

**Ready to extract criteria?** Run your first extraction now:

```powershell
python main.py --pdf "uploads/mcg-guidelines/MCG Sepsis and Other Febrile Illness, without Focal Infection (1).pdf"
```

---

*Last Updated: February 15, 2026*
