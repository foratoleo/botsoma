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

SUPPORT_USER_IDS = [
    uid.strip() for uid in os.getenv("SUPPORT_USER_IDS", "").split(",") if uid.strip()
]
SUPPORT_CHANNEL_ID = os.getenv("SUPPORT_CHANNEL_ID", "")

TOKEN_EXPIRY_BUFFER_S = 60
