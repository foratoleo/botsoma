import os
from pathlib import Path
from dotenv import load_dotenv

# Always load from project root .env (not relying on find_dotenv search)
_project_root = Path(__file__).parent.parent.resolve()
load_dotenv(_project_root / ".env")

MICROSOFT_APP_ID = os.getenv("MICROSOFT_APP_ID", "")
MICROSOFT_APP_PASSWORD = os.getenv("MICROSOFT_APP_PASSWORD", "")
MICROSOFT_APP_TENANT_ID = os.getenv("MICROSOFT_APP_TENANT_ID", "")

ZAI_API_KEY = os.getenv("ZAI_API_KEY", "")
ZAI_MODEL = os.getenv("ZAI_MODEL", "GLM-4.5-Air")
ZAI_BASE_URL = os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/anthropic/v1/messages")
ZAI_TIMEOUT_MS = int(os.getenv("ZAI_TIMEOUT_MS", "15000"))

BOT_PORT = int(os.getenv("BOT_PORT", "3978"))
BOT_NAME = os.getenv("BOT_NAME", "Suporte IA")

KNOWLEDGE_BASE_DIR = Path(os.getenv("KNOWLEDGE_BASE_DIR", "docs/knowledge"))

# Embedding model settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
FAISS_INDEX_PATH = Path(os.getenv("FAISS_INDEX_PATH", ".cache/faiss_index"))
EMBEDDING_TOP_K = int(os.getenv("EMBEDDING_TOP_K", "5"))

# Hybrid search settings
HYBRID_SEARCH_ENABLED = os.getenv("HYBRID_SEARCH_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)
HYBRID_RRF_K = int(os.getenv("HYBRID_RRF_K", "60"))
HYBRID_SPARSE_TOP_K = int(os.getenv("HYBRID_SPARSE_TOP_K", "20"))

# Redis session store
REDIS_URL = os.getenv("REDIS_URL", "")

SUPPORT_USER_IDS = [
    uid.strip() for uid in os.getenv("SUPPORT_USER_IDS", "").split(",") if uid.strip()
]
SUPPORT_CHANNEL_ID = os.getenv("SUPPORT_CHANNEL_ID", "")

TOKEN_EXPIRY_BUFFER_S = 60

# --- Kapso (WhatsApp proxy) ---
KAPSO_API_BASE_URL = os.getenv("KAPSO_API_BASE_URL", "")
KAPSO_API_KEY = os.getenv("KAPSO_API_KEY", "")
KAPSO_PHONE_NUMBER_ID = os.getenv("KAPSO_PHONE_NUMBER_ID", "")
KAPSO_META_GRAPH_VERSION = os.getenv("KAPSO_META_GRAPH_VERSION", "v21.0")
KAPSO_WEBHOOK_VERIFY_TOKEN = os.getenv("KAPSO_WEBHOOK_VERIFY_TOKEN", "")

# --- Jira ---
JIRA_URL = os.getenv("JIRA_URL", "https://botdr.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "SCRUM")
JIRA_ISSUE_TYPE_NAME = os.getenv("JIRA_ISSUE_TYPE_NAME", "Tarefa")
