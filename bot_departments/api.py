"""Owner-authenticated advisory routing API for bot departments."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from .router import route_task, load_registry, RoutingError

router = APIRouter(prefix="/api/bot-departments", tags=["bot-departments"])

class RouteRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)
    department: Optional[str] = None

@router.get("")
def departments(_: None = Depends(__import__("buddy.main", fromlist=["require_owner_token"]).require_owner_token)):
    registry = load_registry()
    return {"version": registry.get("version"), "coordinator": registry.get("coordinator"), "departments": registry["departments"], "menu": registry.get("menu", [])}

@router.post("/route")
def route(request: RouteRequest, _: None = Depends(__import__("buddy.main", fromlist=["require_owner_token"]).require_owner_token)):
    try:
        return route_task(request.task, request.department)
    except RoutingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
