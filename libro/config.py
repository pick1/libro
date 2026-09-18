import os
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# LLM Provider Configuration
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324")

XAVIER_BASE_URL = os.getenv("XAVIER_BASE_URL", "http://192.168.1.110:8080/v1")
XAVIER_API_KEY = os.getenv("XAVIER_API_KEY", "")
XAVIER_MODEL = os.getenv("XAVIER_MODEL", "gpt-oss-20b")

LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", "ollama")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "gpt-oss-20b")

# ChromaDB Configuration
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "/home/dp/projects/ai_librarian/vectorstore")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Other constants
CHUNK_SIZE = 12000  # for truncating input before LLM
AVAILABILITY_THRESHOLD = 0.85  # relevance score threshold for Cloud Library match
DEDUPE_THRESHOLD = 0.92  # for checking existing entries in want_to_read