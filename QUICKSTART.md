# MCG Criteria Extraction System - Quick Start

## Setup

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Ollama (if not already installed)
# Download from https://ollama.ai

# Pull the model
ollama pull qwen2.5:32b
```

## Run Extraction

```powershell
# Single PDF
python main.py --pdf "uploads/mcg-guidelines/MCG Sepsis and Other Febrile Illness, without Focal Infection (1).pdf"

# Batch process
python main.py --batch --input-dir "uploads/mcg-guidelines/"
```

## Output Location

```
data/output/schemas/       # Generated JSON schemas
logs/                       # Execution logs
```

## Testing

```powershell
# Run all tests
pytest -v

# Run specific module tests
pytest test_module_1.py -v
pytest test_module_2.py -v
pytest test_module_3.py -v
pytest test_module_4.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Debug

```powershell
# Enable debug logging in config.yaml
# Set: logging.level = "DEBUG"

# View recent logs
Get-Content logs\mcg_extraction_*.log | Select-Object -Last 50

# Check Ollama connection
ollama list
```

## Configuration

Edit `config.yaml` to change:
- LLM model (`llm.model`)
- Ollama URL (`llm.ollama_url`)
- Performance settings (`ollama_num_thread`, `ollama_num_ctx`, `ollama_num_gpu`)

