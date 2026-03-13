import os
import sys
from groq import Groq
from dotenv import load_dotenv

# Ensure we are in the right directory to find .env
os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

try:
    client = Groq()
    models = client.models.list()
    print("Available Groq Models:")
    found_deepseek = False
    for model in models.data:
        print(f"- {model.id}")
        if "deepseek" in model.id.lower():
            found_deepseek = True
    
    if found_deepseek:
        print("\n✅ DeepSeek model found!")
    else:
        print("\n❌ DeepSeek model NOT found.")
        
except Exception as e:
    print(f"Error: {e}")
