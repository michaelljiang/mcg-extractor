# Using Ollama (Local LLM) with MCG Extraction System

The system now supports **Ollama** for running local LLM models instead of cloud APIs.

---

## Quick Start

### 1. Make Sure Ollama is Installed and Running

**Check if Ollama is installed:**
```powershell
ollama --version
```

**If not installed, download from:** https://ollama.ai/download

**Start Ollama server:**
```powershell
ollama serve
```
(Leave this terminal running)

---

### 2. Pull Your Model

Your **qwen2.5:32b** model should already be downloaded. Verify:

```powershell
ollama list
```

**If not downloaded, pull it:**
```powershell
ollama pull qwen2.5:32b
```

*(This will download ~20GB, may take a while)*

---

### 3. Configuration Already Done

The system is already configured to use Ollama in [config.yaml](config.yaml):

```yaml
llm:
  provider: "ollama"
  model: "qwen2.5:32b"
  ollama_url: "http://localhost:11434"
  temperature: 0.1
  max_tokens: 8000
```

---

### 4. Run Extraction

```powershell
python main.py --pdf "uploads/mcg-guidelines/MCG Sepsis and Other Febrile Illness, without Focal Infection (1).pdf"
```

The system will:
- ✅ Connect to local Ollama server
- ✅ Use qwen2.5:32b for interpretation
- ✅ Process 100% locally (no API calls)
- ✅ No API key needed
- ✅ No rate limits
- ✅ Free and private

---

## Switching Between Providers

### Use Ollama (Local)
```yaml
llm:
  provider: "ollama"
  model: "qwen2.5:32b"
  ollama_url: "http://localhost:11434"
```

### Use Google Gemini (Cloud)
```yaml
llm:
  provider: "google"
  model: "gemini-2.0-flash"
  api_key_env_var: "GOOGLE_API_KEY"
```

---

## Supported Ollama Models

Any Ollama model will work. Popular choices:

### Large Models (Best Quality)
- `qwen2.5:32b` - ✅ What you have (20GB)
- `llama3.1:70b` - Excellent (40GB)
- `mixtral:8x7b` - Great for structured output (26GB)

### Medium Models (Faster)
- `qwen2.5:14b` - Good balance (9GB)
- `llama3.1:8b` - Fast and capable (4.7GB)
- `mistral:7b` - Very fast (4.1GB)

### Small Models (Fastest)
- `qwen2.5:7b` - Quick responses (4.7GB)
- `gemma2:9b` - Google's open model (5.5GB)

**To switch models:**
```powershell
# Download new model
ollama pull llama3.1:8b

# Update config.yaml
model: "llama3.1:8b"
```

---

## Advantages of Ollama

✅ **Private** - Data never leaves your machine  
✅ **Free** - No API costs  
✅ **No Limits** - Process unlimited documents  
✅ **Offline** - Works without internet  
✅ **Fast** - No network latency (if you have good hardware)  
✅ **Customizable** - Fine-tune models for your use case  

---

## System Requirements for qwen2.5:32b

- **RAM:** 32GB minimum (64GB recommended)
- **VRAM:** 16GB+ GPU (NVIDIA recommended for speed)
- **Disk:** 25GB free space
- **CPU:** Modern multi-core processor

**Note:** Without GPU, inference will be slower but still works on CPU.

---

## Troubleshooting

### "Could not connect to Ollama"
**Solution:** Start Ollama server:
```powershell
ollama serve
```

### "Model qwen2.5:32b not found"
**Solution:** Pull the model:
```powershell
ollama pull qwen2.5:32b
```

### Model runs too slow
**Solutions:**
- Use smaller model (qwen2.5:14b or qwen2.5:7b)
- Enable GPU acceleration (NVIDIA CUDA)
- Close other applications to free RAM

### Still want to use Gemini
**Solution:** Edit config.yaml:
```yaml
llm:
  provider: "google"
  model: "gemini-2.0-flash"
  api_key_env_var: "GOOGLE_API_KEY"
```

---

## Testing Your Setup

**Test Ollama connection:**
```powershell
curl http://localhost:11434/api/tags
```

**Test model directly:**
```powershell
ollama run qwen2.5:32b "What is hemodynamic instability?"
```

**Run system test:**
```powershell
pytest tests/test_module_3.py -v
```

---

## Performance Comparison

| Provider | Speed | Cost | Privacy | Quality |
|----------|-------|------|---------|---------|
| **Ollama (qwen2.5:32b)** | Medium-Fast* | Free | 100% | Excellent |
| **Gemini 2.0 Flash** | Very Fast | Free tier | Low | Very Good |
| **Gemini 2.5 Pro** | Fast | Paid | Low | Excellent |

*Speed depends on your hardware (GPU vs CPU)

---

## Next Steps

1. **Verify Ollama is running:** `ollama list`
2. **Run extraction:** `python main.py --pdf "your-file.pdf"`
3. **Check output:** `cat data\output\schemas\*.json`

**The system is ready to use with your local qwen2.5:32b model!**

---

*Last Updated: February 16, 2026*
