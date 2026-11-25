"""Loopback-only unified Buddy Agency workflow demo."""
import json,os,re
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from .demo_server import discover_profiles,process_request
from .workflow import APPROVALS,run_workflow
ROOT=Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
 server_version="BuddyAgencyDemo/1.0"
 def send(self,status,value,kind="application/json; charset=utf-8"):
  b=value if isinstance(value,bytes) else json.dumps(value).encode()
  self.send_response(status);self.send_header("Content-Type",kind);self.send_header("Content-Length",str(len(b)));self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff");self.send_header("Referrer-Policy","no-referrer");self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'");self.end_headers();self.wfile.write(b)
 def body(self):
  try:n=int(self.headers.get("Content-Length","0"))
  except ValueError:raise ValueError("Invalid Content-Length.")
  if n<1 or n>16384:raise ValueError("Body must be 1–16,384 bytes.")
  x=json.loads(self.rfile.read(n).decode())
  if not isinstance(x,dict):raise ValueError("Body must be a JSON object.")
  return x
 def do_GET(self):
  if self.path in {"/","/workflow"}:self.send(200,(ROOT/"unified_demo.html").read_bytes(),"text/html; charset=utf-8")
  elif self.path=="/api/health":self.send(200,{"status":"ok","mode":"unified_simulation","execution_enabled":False})
  elif self.path=="/api/profiles":self.send(200,{"profiles":discover_profiles()})
  elif self.path=="/api/approvals":self.send(200,{"approvals":APPROVALS.list(),"durability":"process_memory_only"})
  else:self.send(404,{"error":"not_found"})
 def do_POST(self):
  try:
   if self.path=="/api/route":self.send(200,process_request(self.body()));return
   if self.path=="/api/workflow":self.send(200,run_workflow(self.body()));return
   m=re.fullmatch(r"/api/approvals/([A-Za-z0-9-]+)/decision",self.path)
   if m:
    p=self.body();a=APPROVALS.decide(m.group(1),p.get("decision",""),p.get("note",""),self.headers.get("Authorization","").removeprefix("Bearer "))
    self.send(200,{"approval":a,"message":"Decision recorded; no operation was executed."});return
   self.send(404,{"error":"not_found"})
  except PermissionError as e:self.send(403,{"error":"owner_authorization_failed","detail":str(e)})
  except KeyError as e:self.send(404,{"error":"approval_not_found","detail":str(e)})
  except RuntimeError as e:self.send(409,{"error":"decision_conflict","detail":str(e)})
  except (ValueError,UnicodeDecodeError,json.JSONDecodeError) as e:self.send(400,{"error":"invalid_request","detail":str(e)})
 def log_message(self,fmt,*args):print("[Buddy Agency Demo] "+(fmt%args))
def main():
 port=int(os.getenv("BUDDY_AGENCY_DEMO_PORT","8761"));s=ThreadingHTTPServer(("127.0.0.1",port),Handler)
 print("Buddy Agency Unified Workflow: http://127.0.0.1:%d"%port);print("Loopback only · simulation · no provider calls or execution")
 try:s.serve_forever()
 except KeyboardInterrupt:print("\nStopping.")
 finally:s.server_close()
if __name__=="__main__":main()
