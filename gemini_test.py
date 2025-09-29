import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
load_dotenv()

# API key uthao
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Model choose karo
model = genai.GenerativeModel("gemini-1.5-flash")

# Test prompt
response = model.generate_content("Explain AI in one line")
print("Gemini Response:", response.text)
