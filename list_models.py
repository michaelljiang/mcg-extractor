"""List available Google Gemini models"""
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Initialize client
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in environment")
    exit(1)

client = genai.Client(api_key=api_key)

print("Available Google Gemini Models:")
print("=" * 80)

try:
    # List all models
    models = client.models.list()
    
    models_list = list(models)
    print(f"\nTotal models found: {len(models_list)}\n")
    
    # Filter for models that support generateContent
    generation_models = []
    
    for model in models_list:
        model_name = model.name
        print(f"\nModel: {model_name}")
        
        # Get model details
        if hasattr(model, 'display_name'):
            print(f"  Display Name: {model.display_name}")
        if hasattr(model, 'description'):
            desc = model.description[:100] + "..." if len(model.description) > 100 else model.description
            print(f"  Description: {desc}")
        if hasattr(model, 'supported_generation_methods'):
            methods = model.supported_generation_methods
            print(f"  Supported Methods: {', '.join(methods)}")
            if 'generateContent' in methods:
                generation_models.append(model_name)
        
        print("-" * 80)
    
    print(f"\n{'='*80}")
    print("MODELS THAT SUPPORT generateContent (for our use case):")
    print(f"{'='*80}")
    for m in generation_models:
        print(f"  - {m}")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
