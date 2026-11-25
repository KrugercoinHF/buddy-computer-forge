"""Governed simulation workflow: Router -> specialist -> Boardroom -> owner gate."""
import hashlib,hmac,os,threading,uuid
from datetime import datetime,timezone
from .demo_server import process_request
def _now(): return datetime.now(timezone.utc).isoformat()
class ApprovalLedger:
 def __init__(self): self.items={}; self.lock=threading.Lock()
 def create(self,wid,task,risk):
  a={"approval_id":"apr-"+uuid.uuid4().hex[:12],"workflow_id":wid,"task_digest":hashlib.sha256(task.encode()).hexdigest(),"risk_level":risk,"status":"pending_owner_approval","decision":None,"created_at":_now(),"execution":"not_executed"}
  with self.lock:self.items[a["approval_id"]]=a
  return dict(a)
 def list(self):
  with self.lock:return [dict(x) for x in self.items.values()]
 def decide(self,aid,decision,note,token):
  expected=os.getenv("BUDDY_OWNER_APPROVAL_TOKEN","")
  if not expected:raise PermissionError("Configure BUDDY_OWNER_APPROVAL_TOKEN first.")
  if not token or not hmac.compare_digest(token,expected):raise PermissionError("Owner token missing or invalid.")
  if decision not in {"approve","reject"}:raise ValueError("decision must be approve or reject")
  with self.lock:
   a=self.items.get(aid)
   if a is None:raise KeyError("Approval record not found.")
   if a["status"]!="pending_owner_approval":raise RuntimeError("Approval already decided.")
   a["status"]="owner_approved_record_only" if decision=="approve" else "owner_rejected"
   a["decision"]={"decision":decision,"note":str(note)[:1000],"decided_at":_now()}; a["execution"]="not_executed"
   return dict(a)
APPROVALS=ApprovalLedger()
OUTPUTS={
"grokbot":("Research brief",["Break the request into verifiable questions.","Separate evidence, assumptions and unknowns.","Draft recommendations; independent source checks remain necessary."]),
"manus-patterns":("Plan draft",["Define outcome and acceptance criteria.","Break work into reversible milestones.","Assign dependencies, owners and verification steps."]),
"battlemind":("Independent evaluation",["Identify the strongest supporting argument.","Challenge assumptions and failure modes.","Recommend a measurable test and rollback condition."]),
"buddybot":("Assistant draft",["Clarify the intended outcome.","Summarise a useful next step.","Stay within current permissions."]),
"ai-boardroom":("Boardroom brief",["Frame the decision and options.","Consider executive, technical, finance and security perspectives.","Record disagreements and evidence gaps."]),
"autogenius":("Capability report",["Inspect specialist profiles.","Match capabilities to intent.","Return a bounded routing recommendation."])}
def run_workflow(p):
 if not isinstance(p,dict):raise ValueError("Request must be a JSON object.")
 task,intent=p.get("task"),p.get("intent")
 if not isinstance(task,str) or not task.strip() or len(task)>2000:raise ValueError("task must be 1–2,000 characters.")
 if not isinstance(intent,str) or not intent.strip():raise ValueError("intent must be a non-empty string.")
 routed=process_request({"task":task,"intent":intent,"requested_profile":p.get("requested_profile"),"trace_id":"workflow-"+uuid.uuid4().hex[:12]})
 d=routed["decision"]; wid="wf-"+uuid.uuid4().hex[:12]; specialist=boardroom=approval=None
 steps=[{"step":1,"component":"Buddy Router","status":d["policy"],"detail":"Specialist selection and policy checks completed."}]
 if d["policy"]!="deny" and d["profile_id"]:
  title,lines=OUTPUTS.get(d["profile_id"],("Specialist draft",["Review request.","Identify constraints and risks.","Prepare a draft for human review."]))
  specialist={"adapter":d["profile_id"],"mode":"deterministic_simulation","title":title,"output":lines,"provider_called":False,"tools_executed":False}
  steps.append({"step":2,"component":"Specialist adapter","status":"simulated","detail":title+" generated; no provider or tools invoked."})
  panel=[("CEO","support_with_conditions","Keep owner and success criteria explicit."),("CTO","support_with_conditions","Validate assumptions with a small test."),("CISO","challenge","Keep permissions narrow and auditable."),("CFO","needs_more_evidence","Estimate ongoing costs before expansion."),("Independent Reviewer","challenge","A simulation is not production evidence.")]
  boardroom={"component":"Buddy Boardroom adapter","mode":"deterministic_simulation","panel":[{"role":r,"position":s,"note":n} for r,s,n in panel],"chair_summary":"Recommend a reversible, evidence-led next step: "+task[:160],"provider_called":False,"binding_vote":False}
  steps.append({"step":3,"component":"Buddy Boardroom","status":"simulated","detail":"Five role-based perspectives reviewed the draft; no binding vote."})
 else:
  steps.extend([{"step":2,"component":"Specialist adapter","status":"skipped","detail":"Denied route; no adapter ran."},{"step":3,"component":"Buddy Boardroom","status":"skipped","detail":"No draft was available for review."}])
 if d["policy"]=="approval_required":
  approval=APPROVALS.create(wid,task,d["risk_level"]); steps.append({"step":4,"component":"Owner approval gateway","status":"pending_owner_approval","detail":"Approval record created; no operation authorised or executed."})
 elif d["policy"]=="deny":steps.append({"step":4,"component":"Owner approval gateway","status":"not_reached","detail":"Denied requests cannot be approved here."})
 else:steps.append({"step":4,"component":"Owner approval gateway","status":"not_required","detail":"Advisory output only; no consequential action requested."})
 return {"workflow_id":wid,"task":task,"intent":intent,"routing":routed,"specialist_result":specialist,"boardroom_review":boardroom,"approval":approval,"steps":steps,"safety":{"simulation_only":True,"provider_calls_enabled":False,"external_actions_enabled":False,"computer_execution_enabled":False,"approval_is_execution_grant":False}}
