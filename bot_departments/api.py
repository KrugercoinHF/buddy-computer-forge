"""Owner-authenticated advisory routing API for bot departments."""
import hmac
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from buddy.config import DEFAULT_OWNER_TOKEN
from .router import RoutingError, load_registry, route_task

router = APIRouter(prefix="/api/bot-departments", tags=["bot-departments"])


def require_department_owner(authorization: str | None = Header(default=None)) -> None:
    token = os.getenv("BUDDY_OWNER_TOKEN", DEFAULT_OWNER_TOKEN)
    if not token or not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="owner authorization required")
    if not hmac.compare_digest(authorization[7:], token):
        raise HTTPException(status_code=401, detail="invalid owner token")


class RouteRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)
    department: Optional[str] = None


@router.get("")
def departments(_: None = Depends(require_department_owner)):
    registry = load_registry()
    return {
        "version": registry.get("version"),
        "coordinator": registry.get("coordinator"),
        "departments": registry["departments"],
        "menu": registry.get("menu", []),
    }


@router.post("/route")
def route(request: RouteRequest, _: None = Depends(require_department_owner)):
    try:
        return route_task(request.task, request.department)
    except RoutingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
