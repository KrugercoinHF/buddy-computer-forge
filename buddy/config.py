from pathlib import Path
import os

APP_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = APP_ROOT / "data"
DB_PATH = Path(os.getenv("BUDDY_DB_PATH", DATA_DIR / "buddy.db"))
WORKSPACE_ROOT = Path(os.getenv("BUDDY_WORKSPACE_ROOT", APP_ROOT / "workspace")).resolve()
DEFAULT_OWNER_TOKEN = os.getenv("BUDDY_OWNER_TOKEN", "dev-owner-token")
ENABLE_CONTAINERS = os.getenv("BUDDY_ENABLE_CONTAINERS", "0") == "1"
CONTAINER_IMAGE = os.getenv("BUDDY_CONTAINER_IMAGE", "python:3.12-alpine")

SERVER_HOST = os.getenv("BUDDY_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("BUDDY_PORT", "8741"))
