"""
Configuration for BCT Hackathon Backend
LLM, Database, and Embeddings setup
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Load environment variables
load_dotenv()

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4'
}

# LLM Configuration - Custom Gemma model via PublicAI
LLM = ChatOpenAI(
    model="google/gemma-4-E4B-it",
    base_url="https://gemma-4.publicaai.com/v1",
    api_key="publica-k7x2m9n4p1q8r3t6w5y8z2",
    temperature=0.7
)

# Embeddings Configuration - Custom nomic-embedding via PublicAI
# Note: Can have 502 errors when server is overloaded, but has retry logic built-in
LOCAL_API_BASE = "https://gemma-embed.publicaai.com/v1"
LOCAL_API_KEY = "unused"

EMBEDDINGS = OpenAIEmbeddings(
    base_url=LOCAL_API_BASE,
    api_key=LOCAL_API_KEY,
    model="nomic-embedding",
    check_embedding_ctx_length=False,
    timeout=60,  # Increase timeout to 60 seconds
    max_retries=3
)

# Alternative: Use local llama.cpp server (uncomment and run embed3.py first)
# LOCAL_API_BASE = "http://localhost:8000/v1"
# EMBEDDINGS = OpenAIEmbeddings(
#     base_url=LOCAL_API_BASE,
#     api_key=LOCAL_API_KEY,
#     model="Qwen3-Embedding-0.6B-Q8_0",
#     check_embedding_ctx_length=False
# )

# Paths
FAISS_INDEX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")  # ChromaDB storage path

# App Settings
MAX_REVIEWS_PER_USER = 15  # Number of past reviews to fetch for user modeling
TOP_K_CANDIDATES = 50      # Number of candidate businesses for recommendations
