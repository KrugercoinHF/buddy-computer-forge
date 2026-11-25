import unittest
from dataclasses import asdict
from buddy_router.engine import route
from buddy_router.policy import authorize
from buddy_router.trace import TraceStore

class PolicyTraceTests(unittest.TestCase):
    def test_advisory_permitted_but_never_executable(self):
        d=route({"trace_id":"p1","intent":"research_and_summarize"})
        p=authorize(d)
        self.assertTrue(p.allowed); self.assertFalse(p.execution_enabled)
    def test_denial_propagates(self):
        d=route({"trace_id":"p2","intent":"bogus"})
        self.assertFalse(authorize(d).allowed)
    def test_unknown_risk_fails_closed(self):
        self.assertFalse(authorize({"risk_level":"R99","policy":"allow_advisory"}).allowed)
    def test_r3_requires_approval_but_adapter_still_disabled(self):
        d=route({"trace_id":"p3","intent":"computer_operation_request"})
        p=authorize(d,owner_approved=True,execution_adapter_enabled=True)
        self.assertFalse(p.allowed); self.assertFalse(p.execution_enabled)
    def test_trace_append_and_list(self):
        req={"trace_id":"p4","intent":"plan_task"}; d=route(req); p=authorize(d)
        s=TraceStore(); rec=s.append(req,d,asdict(p))
        self.assertEqual(len(s.list()),1); self.assertFalse(rec["execution_enabled"])

if __name__=="__main__": unittest.main()
