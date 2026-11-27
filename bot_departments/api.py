"""Owner-authenticated advisory routing API for bot departments."""
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional\nimport os, hmac\nfrom buddy.config import DEFAULT_OWNER_TOKEN
from .router import route_task, load_registry, RoutingError

router = APIRouter(prefix="/api/bot-departments", tags=["bot-departments"])\n\ndef require_owner_token(authorization: str | None = Header(default=None)):\n    token = os.getenv("BUDDY_OWNER_TOKEN", DEFAULT_OWNER_TOKEN)\n    if not token or not authorization or not authorization.startswith("Bearer "):\n        raise HTTPException(status_code=401, detail="owner authorization required")\n    if not hmac.compare_digest(authorization[7:], token):\n        raise HTTPException(status_code=401, detail="invalid owner token")

class RouteRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)
    department: Optional[str] = None

@router.get("")
def departments(_: None = Depends(require_owner_token)):
    registry = load_registry()
    return {"version": registry.get("version"), "coordinator": registry.get("coordinator"), "departments": registry["departments"], "menu": registry.get("menu", [])}

@router.post("/route")
def route(request: RouteRequest, _: None = Depends(__import__("buddy.main", fromlist=["require_owner_token"]).require_owner_token)):
    try:
        return route_task(request.task, request.department)
    except RoutingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
