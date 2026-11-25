"""Small in-memory, append-only trace records for prototype UI/testing."""
from datetime import datetime, timezone

class TraceStore:
    def __init__(self):
        self._records=[]
    def append(self, request: dict, decision: dict, policy_result: dict | None=None):
        record={"trace_id":decision.get("trace_id"),"timestamp":datetime.now(timezone.utc).isoformat(),"intent":request.get("intent"),"requested_profile":request.get("requested_profile"),"decision":decision,"policy_result":policy_result,"execution_enabled":False}
        self._records.append(record)
        return record
    def list(self):
        return list(self._records)
