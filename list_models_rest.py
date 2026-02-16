"""List available Google Gemini models using alternative method"""
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in environment")
    exit(1)

print("Checking Google Gemini API Key...")
print(f"API Key (first 10 chars): {api_key[:10]}...")
print()

# Try REST API approach
print("Querying models via REST API...")
print("=" * 80)

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])
        
        print(f"\nTotal models found: {len(models)}\n")
        
        generation_models = []
        
        for model in models:
            model_name = model.get('name', 'Unknown')
            print(f"\nModel: {model_name}")
            
            if 'displayName' in model:
                print(f"  Display Name: {model['displayName']}")
            if 'description' in model:
                desc = model['description'][:100] + "..." if len(model['description']) > 100 else model['description']
                print(f"  Description: {desc}")
            if 'supportedGenerationMethods' in model:
                methods = model['supportedGenerationMethods']
                print(f"  Supported Methods: {', '.join(methods)}")
                if 'generateContent' in methods:
                    generation_models.append(model_name)
            
            print("-" * 80)
        
        print(f"\n{'='*80}")
        print("MODELS THAT SUPPORT generateContent:")
        print(f"{'='*80}")
        for m in generation_models:
            # Extract just the model name
            simple_name = m.replace('models/', '')
            print(f"  - {simple_name}")
    else:
        print(f"ERROR: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
