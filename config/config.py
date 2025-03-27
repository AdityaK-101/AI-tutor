import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "ai_tutor_db"

# Hugging Face Configuration
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
if not HF_API_TOKEN:
    print("Warning: HF_API_TOKEN not found in .env file")

# Using CodeLlama model
HF_API_URL = "https://api-inference.huggingface.co/models/codellama/CodeLlama-34b-Instruct-hf"

# Collections
COLLECTIONS = {
    "users": "users",
    "chat_history": "chat_history",
    "quiz_results": "quiz_results",
    "resources": "resources",
    "roadmaps": "roadmaps"
} 