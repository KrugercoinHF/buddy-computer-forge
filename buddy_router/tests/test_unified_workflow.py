import json,os,threading,unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from buddy_router.unified_demo import Handler
from buddy_router.workflow import APPROVALS,run_workflow
class WorkflowTests(unittest.TestCase):
 def test_research_flows_through_router_specialist_boardroom_gateway(self):
  r=run_workflow({"task":"Research onboarding","intent":"research_and_summarize"})
  self.assertEqual([x["component"] for x in r["steps"]],["Buddy Router","Specialist adapter","Buddy Boardroom","Owner approval gateway"])
  self.assertEqual(r["specialist_result"]["adapter"],"grokbot");self.assertEqual(len(r["boardroom_review"]["panel"]),5)
 def test_computer_operation_creates_pending_approval_not_execution(self):
  r=run_workflow({"task":"Open a local application","intent":"computer_operation_request"})
  self.assertEqual(r["approval"]["status"],"pending_owner_approval");self.assertEqual(r["approval"]["execution"],"not_executed")
 def test_approval_requires_token_and_is_record_only(self):
  r=run_workflow({"task":"Open app","intent":"computer_operation_request"})
  with patch.dict(os.environ,{"BUDDY_OWNER_APPROVAL_TOKEN":"owner-secret"}):
   a=APPROVALS.decide(r["approval"]["approval_id"],"approve","Reviewed","owner-secret")
  self.assertEqual(a["status"],"owner_approved_record_only");self.assertEqual(a["execution"],"not_executed")
 def test_denied_route_skips_adapters(self):
  r=run_workflow({"task":"Unsupported","intent":"unknown","requested_profile":"grokbot"})
  self.assertIsNone(r["specialist_result"]);self.assertIsNone(r["boardroom_review"]);self.assertEqual(r["steps"][-1]["status"],"not_reached")
class HttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.server=ThreadingHTTPServer(("127.0.0.1",0),Handler);c.thread=threading.Thread(target=c.server.serve_forever,daemon=True);c.thread.start();c.base="http://127.0.0.1:%d"%c.server.server_address[1]
 @classmethod
 def tearDownClass(c):c.server.shutdown();c.server.server_close();c.thread.join(timeout=2)
 def test_dashboard_and_workflow_api(self):
  with urlopen(self.base+"/") as r:self.assertIn("ROUTER → SPECIALIST → BOARDROOM",r.read().decode())
  b=json.dumps({"task":"Research beta rollout","intent":"research_and_summarize"}).encode();q=Request(self.base+"/api/workflow",data=b,headers={"Content-Type":"application/json"})
  with urlopen(q) as r:d=json.loads(r.read())
  self.assertEqual(d["specialist_result"]["adapter"],"grokbot");self.assertEqual(len(d["boardroom_review"]["panel"]),5)
 def test_bad_owner_token_rejected(self):
  r=run_workflow({"task":"Open app","intent":"computer_operation_request"});b=json.dumps({"decision":"approve"}).encode()
  q=Request(self.base+"/api/approvals/"+r["approval"]["approval_id"]+"/decision",data=b,headers={"Content-Type":"application/json","Authorization":"Bearer wrong"})
  with patch.dict(os.environ,{"BUDDY_OWNER_APPROVAL_TOKEN":"correct"}):
   with self.assertRaises(HTTPError) as e:urlopen(q)
  self.assertEqual(e.exception.code,403)
if __name__=="__main__":unittest.main()
