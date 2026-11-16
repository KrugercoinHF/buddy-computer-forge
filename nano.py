#!/usr/bin/env python3
"""Optional Gemini image bridge. Explicitly invoked; never runs at import time."""
import argparse,base64,json,os,pathlib,sys,urllib.error,urllib.request
def main():
 p=argparse.ArgumentParser(description="Generate poster image using Gemini (optional explicit network call)");p.add_argument("--prompt-file",default="buddy-poster-prompt.txt");p.add_argument("--output",default="poster-output/buddy-poster.png");p.add_argument("--dry-run",action="store_true");a=p.parse_args();prompt=pathlib.Path(a.prompt_file).read_text(encoding="utf-8");key=os.getenv("GEMINI_API_KEY","");model=os.getenv("GEMINI_IMAGE_MODEL","gemini-2.5-flash-image")
 if a.dry_run: print(json.dumps({"model":model,"prompt_file":a.prompt_file,"output":a.output,"network":"disabled","prompt_chars":len(prompt)}));return 0
 if not key: print("GEMINI_API_KEY is required; no request sent.",file=sys.stderr);return 2
 url="https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent?key="+key;body={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseModalities":["IMAGE","TEXT"]}};req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
 try:
  with urllib.request.urlopen(req,timeout=120) as response:data=json.loads(response.read())
 except (urllib.error.URLError,TimeoutError) as e: print("Gemini request failed: "+str(e),file=sys.stderr);return 1
 parts=data.get("candidates",[{}])[0].get("content",{}).get("parts",[]);item=next((x.get("inlineData") or x.get("inline_data") for x in parts if x.get("inlineData") or x.get("inline_data")),None)
 if not item: print("No image returned. Response: "+json.dumps(data)[:3000],file=sys.stderr);return 1
 raw=base64.b64decode(item["data"]);out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw);print(json.dumps({"saved":str(out),"bytes":len(raw),"mime_type":item.get("mimeType",item.get("mime_type"))}));return 0
if __name__=="__main__": raise SystemExit(main())
