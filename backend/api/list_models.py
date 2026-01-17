
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try to look for .env in parent directories if not found
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    env_path = os.path.join(parent_dir, '.env')
    load_dotenv(env_path)
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

try:
    with open("models.txt", "w") as f:
        print("Listing available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(m.name + "\n")
                print(m.name)
except Exception as e:
    print(f"Error: {e}")
