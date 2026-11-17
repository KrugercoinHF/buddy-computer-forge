"""Run with: uvicorn buddy.ui_app:app --host 127.0.0.1 --port 8741."""
from .main import app
from .nodes_ui import router

app.include_router(router)
