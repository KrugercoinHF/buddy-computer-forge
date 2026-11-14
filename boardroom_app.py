"""AI Boardroom Simulator V1 — isolated, local-first simulation service."""
from __future__ import annotations
import json, os, secrets, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

APP_VERSION = "0.1.0"
DEFAULT_DB = Path("data/boardroom.sqlite3")
DASHBOARD_PATH = Path(__file__).parent / "boardroom_dashboard.html"
app = FastAPI(title="Buddy AI Boardroom Simulator", version=APP_VERSION)

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def db_path() -> Path:
    return Path(os.getenv("BOARDROOM_DB_PATH", str(DEFAULT_DB)))

def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY, payload TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_boardroom_meetings_created ON meetings(created_at DESC)")

@app.on_event("startup")
def startup() -> None:
    init_db()

def make_agents() -> list[dict[str, Any]]:
    executives = [
        ("CEO","Chief Executive Officer","Strategy & Governance","Chairs meetings, frames decisions and balances organisational priorities."),
        ("CTO","Chief Technology Officer","Technology","Evaluates architecture, engineering feasibility, reliability and technical debt."),
        ("CFO","Chief Financial Officer","Finance","Evaluates costs, budgets, unit economics and financial exposure."),
        ("COO","Chief Operating Officer","Operations","Evaluates delivery capacity, processes, dependencies and readiness."),
        ("CISO","Chief Information Security Officer","Security","Challenges security, privacy, access control and threat assumptions."),
        ("CPO","Chief Product Officer","Product","Evaluates user value, scope, usability and product-market fit."),
        ("CRO","Chief Research Officer","Research & Evidence","Checks evidence quality, assumptions, uncertainty and research gaps."),
        ("CLEO","Chief Legal & Ethics Officer","Legal & Ethics","Evaluates legal exposure, fairness, accountability and responsible use."),
        ("CPOE","Chief People & Culture Officer","People & Culture","Evaluates team impact, skills, accessibility and change management."),
        ("DA","Independent Devil's Advocate","Independent Review","Challenges consensus, identifies failure modes and proposes alternatives."),
    ]
    agents = []
    for code, title, department, mandate in executives:
        agents.append({"id": "AG-%03d" % (len(agents)+1), "name": title, "short_name": code,
            "department": department, "mandate": mandate, "tier": "Executive",
            "status": "available", "provider": "simulation"})
    committees = [
        ("Strategy & Foresight", ["Scenario Planner","Competitive Analyst","Business Model Analyst","Portfolio Strategist","Growth Strategist","Partnership Analyst","Market Entry Analyst","Transformation Planner","Governance Analyst","Strategic Risk Analyst"]),
        ("Engineering & Architecture", ["Backend Architect","Frontend Architect","Platform Engineer","Infrastructure Engineer","API Designer","Data Architect","Integration Engineer","Reliability Engineer","Developer Experience Analyst","Systems Designer"]),
        ("Security & Trust", ["Threat Modeller","Identity Specialist","Privacy Analyst","Application Security Analyst","Supply Chain Security Analyst","Incident Response Planner","Policy Analyst","Compliance Analyst","Safety Evaluator","Access Control Reviewer"]),
        ("Finance & Commercial", ["Budget Analyst","Cost Controller","Revenue Analyst","Pricing Strategist","Procurement Analyst","Investment Analyst","Cash Flow Analyst","Commercial Risk Analyst","Forecast Analyst","Value Realisation Analyst"]),
        ("Product & Design", ["Product Manager","UX Researcher","Interaction Designer","Accessibility Specialist","Service Designer","Customer Journey Analyst","Product Operations Analyst","Quality Advocate","Feature Prioritisation Analyst","Product Metrics Analyst"]),
        ("Research & Intelligence", ["Evidence Analyst","Data Researcher","Fact Checker","Trend Analyst","Knowledge Curator","Experiment Designer","Benchmark Analyst","Technical Writer","Source Evaluator","Uncertainty Analyst"]),
        ("Operations & Delivery", ["Programme Manager","Project Planner","Release Manager","Process Analyst","Workflow Designer","Support Operations Analyst","Capacity Planner","Dependency Manager","Change Manager","Delivery Assurance Analyst"]),
        ("People & Learning", ["Learning Designer","Training Analyst","Team Effectiveness Analyst","Talent Planner","Inclusion Reviewer","Communications Advisor","Facilitation Specialist","Conflict Mediator","Knowledge Transfer Lead","Wellbeing Advocate"]),
        ("Independent Assurance", ["Red Team Reviewer","Assumption Challenger","Failure Mode Analyst","External Perspective Reviewer","Ethics Challenger","Resilience Reviewer","Counterfactual Analyst","Decision Auditor","Bias Reviewer","Final Quality Reviewer"]),
    ]
    for department, roles in committees:
        for role in roles:
            agents.append({"id": "AG-%03d" % (len(agents)+1), "name": role, "short_name": role,
                "department": department, "mandate": "Provides specialist %s analysis and challenges the proposal from the %s perspective." % (role.lower(), department.lower()),
                "tier": "Specialist", "status": "available", "provider": "simulation"})
    return agents

AGENTS = make_agents()
AGENT_BY_ID = {a["id"]: a for a in AGENTS}

class MeetingCreate(BaseModel):
    topic: str = Field(min_length=4, max_length=240)
    context: str = Field(default="", max_length=8000)
    participant_count: int = Field(default=10, ge=5, le=100)
    agent_ids: list[str] = Field(default_factory=list, max_length=100)

class DecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    note: str = Field(default="", max_length=2000)

def require_owner(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("BOARDROOM_OWNER_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Owner approval is disabled until BOARDROOM_OWNER_TOKEN is configured.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="A Bearer owner token is required.")
    if not secrets.compare_digest(authorization.removeprefix("Bearer "), expected):
        raise HTTPException(status_code=403, detail="Owner token is invalid.")

def save_meeting(meeting: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute("""INSERT INTO meetings(id,payload,created_at,updated_at) VALUES(?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at""",
            (meeting["id"], json.dumps(meeting), meeting["created_at"], now_utc()))

def load_meeting(meeting_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT payload FROM meetings WHERE id=?", (meeting_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    return json.loads(row["payload"])

def simulate_contribution(agent: dict[str, Any], index: int) -> dict[str, Any]:
    lenses = [
        ("support_with_conditions","The proposal may create value if its scope, owner and success criteria are explicit."),
        ("support_with_conditions","A staged pilot is preferable to a broad release; validate assumptions before increasing exposure."),
        ("needs_more_evidence","The current brief does not establish enough evidence to treat readiness as proven."),
        ("support_with_conditions","Define measurable outcomes, rollback conditions and a named accountable owner."),
        ("challenge","A failure in one dependency could undermine the whole plan; map the dependency chain."),
        ("support_with_conditions","Proceed only with least-privilege access, clear boundaries and auditable decisions."),
        ("needs_more_evidence","Request independent verification and record what remains unknown."),
        ("challenge","Consider maintenance, support and failure recovery costs, not only initial build costs."),
        ("support_with_conditions","A limited, reversible experiment can test the hypothesis without committing to full rollout."),
        ("challenge","Do not confuse a convincing demonstration with evidence of production readiness."),
    ]
    stance, argument = lenses[index % len(lenses)]
    return {"agent_id":agent["id"],"agent_name":agent["name"],"department":agent["department"],
        "stance":stance,"argument":argument,
        "risk":"Unverified assumptions or unclear ownership could create avoidable exposure.",
        "recommendation":"Document evidence, assign an accountable owner and use a reversible, approval-gated next step.",
        "provider":"simulation"}

def run_simulation(meeting: dict[str, Any]) -> dict[str, Any]:
    chosen = [AGENT_BY_ID[x] for x in meeting["agent_ids"]]
    contributions = [simulate_contribution(agent, i) for i, agent in enumerate(chosen)]
    counts = {"support_with_conditions":0,"needs_more_evidence":0,"challenge":0}
    for item in contributions:
        counts[item["stance"]] += 1
    meeting["status"] = "completed"
    meeting["completed_at"] = now_utc()
    meeting["contributions"] = contributions
    meeting["vote"] = {**counts,"approval_signal_percent":round(counts["support_with_conditions"]/max(1,len(contributions))*100),
        "note":"Simulated advisory signal only; not a binding vote or model consensus."}
    meeting["minutes"] = {
        "chair_summary":"The board reviewed: %s. The simulated panel recommends a staged, evidence-led approach." % meeting["topic"],
        "key_themes":["Define measurable success criteria and an accountable owner.",
            "Verify security, operational and financial assumptions before expanding scope.",
            "Keep actions reversible and record evidence, risks and unresolved questions."],
        "open_questions":["Which evidence would demonstrate that the proposal is ready?",
            "What is the smallest safe pilot and how will it be rolled back?",
            "Who owns each follow-up and when will progress be reviewed?"],
        "recorded_at":now_utc()}
    meeting["proposals"] = [
        {"id":str(uuid.uuid4()),"title":"Prepare an evidence and readiness checklist",
         "description":"Collect test results, security findings, operating assumptions and measurable acceptance criteria.",
         "risk_level":"low","status":"pending_owner_approval","execution":"not_executed","decision":None},
        {"id":str(uuid.uuid4()),"title":"Design a limited, reversible pilot",
         "description":"Propose a bounded pilot with rollback criteria, access restrictions and an accountable owner.",
         "risk_level":"medium","status":"pending_owner_approval","execution":"not_executed","decision":None},
        {"id":str(uuid.uuid4()),"title":"Schedule an independent security review",
         "description":"Review the threat model, access boundaries, data handling and audit trail before any wider release.",
         "risk_level":"high","status":"pending_owner_approval","execution":"not_executed","decision":None}]
    return meeting

@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    if not DASHBOARD_PATH.exists():
        return "<h1>Buddy AI Boardroom</h1><p>Dashboard asset is missing.</p>"
    return DASHBOARD_PATH.read_text(encoding="utf-8")

@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status":"ok","service":"buddy-ai-boardroom","version":APP_VERSION,
        "agent_directory_size":len(AGENTS),"provider_mode":"simulation_only",
        "external_models_connected":False,"execution_enabled":False,
        "owner_approval_required_for_proposals":True}

@app.get("/api/agents")
def list_agents(department: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = AGENTS if not department else [a for a in AGENTS if a["department"].lower()==department.lower()]
    return {"total":len(rows),"agents":rows[:max(1,min(limit,100))]}

@app.post("/api/meetings")
def create_meeting(payload: MeetingCreate) -> dict[str, Any]:
    if payload.agent_ids:
        unknown = [x for x in payload.agent_ids if x not in AGENT_BY_ID]
        if unknown:
            raise HTTPException(status_code=422, detail="Unknown agent IDs: " + ", ".join(unknown))
        selected = list(dict.fromkeys(payload.agent_ids))
        if not 5 <= len(selected) <= 100:
            raise HTTPException(status_code=422, detail="Select between 5 and 100 unique agents.")
    else:
        selected = [a["id"] for a in AGENTS[:payload.participant_count]]
    meeting = {"id":str(uuid.uuid4()),"topic":payload.topic.strip(),"context":payload.context.strip(),
        "participant_count":len(selected),"agent_ids":selected,"status":"scheduled",
        "provider_mode":"simulation_only","created_at":now_utc(),"contributions":[],
        "vote":None,"minutes":None,"proposals":[]}
    save_meeting(meeting)
    return meeting

@app.get("/api/meetings")
def list_meetings() -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute("SELECT payload FROM meetings ORDER BY created_at DESC LIMIT 50").fetchall()
    meetings = [json.loads(r["payload"]) for r in rows]
    return {"total":len(meetings),"meetings":meetings}

@app.get("/api/meetings/{meeting_id}")
def get_meeting(meeting_id: str) -> dict[str, Any]:
    return load_meeting(meeting_id)

@app.post("/api/meetings/{meeting_id}/run")
def run_meeting(meeting_id: str) -> dict[str, Any]:
    meeting = load_meeting(meeting_id)
    if meeting["status"] != "completed":
        meeting = run_simulation(meeting)
        save_meeting(meeting)
    return meeting

@app.post("/api/meetings/{meeting_id}/proposals/{proposal_id}/decision")
def decide_proposal(meeting_id: str, proposal_id: str, payload: DecisionRequest,
                    _: None = Depends(require_owner)) -> dict[str, Any]:
    meeting = load_meeting(meeting_id)
    proposal = next((p for p in meeting["proposals"] if p["id"]==proposal_id), None)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    if proposal["status"] != "pending_owner_approval":
        raise HTTPException(status_code=409, detail="This proposal already has an owner decision.")
    proposal["status"] = "owner_approved" if payload.decision=="approve" else "owner_rejected"
    proposal["decision"] = {"decision":payload.decision,"note":payload.note,"decided_at":now_utc()}
    proposal["execution"] = "not_executed"
    save_meeting(meeting)
    return {"meeting_id":meeting_id,"proposal":proposal,
        "message":"Decision recorded. No task, code change or external action was executed."}
