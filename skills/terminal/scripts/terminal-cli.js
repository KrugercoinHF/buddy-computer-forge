#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto"),{spawnSync}=require("node:child_process");
const root=path.resolve(__dirname,"../../..");
function safe(p){const r=path.resolve(root,p||".");if(r!==root&&!r.startsWith(root+path.sep))throw Error("T3 refusal: path escapes repository root");return r}
const cmd=process.argv[2]||"help",arg=process.argv[3];
function run(args){const r=spawnSync(process.execPath,args,{cwd:root,encoding:"utf8"});process.stdout.write(r.stdout||"");process.stderr.write(r.stderr||"");return r.status??1}
try{switch(cmd){
case"help":console.log("11 commands: help,status,score,verify,determinism,registry,wings,artifacts,hash <repo-path>,poster,calibrate");break;
case"status":console.log(JSON.stringify({root,read_only:true,execution_enabled:false,files:["README.md","INDEX.md","pm/artifacts.json","skills/registry.json","wings"].map(p=>({path:p,exists:fs.existsSync(safe(p))}))},null,2));break;
case"score":process.exit(run(["skill.js","score"]));
case"verify":process.exit(run(["skill.js","verify"]));
case"determinism":process.exit(run(["skill.js","determinism"]));
case"registry":process.stdout.write(fs.readFileSync(safe("skills/registry.json"),"utf8"));break;
case"wings":console.log(fs.readdirSync(safe("wings")).filter(x=>x.endsWith(".json")).sort().join("\n"));break;
case"artifacts":{const x=JSON.parse(fs.readFileSync(safe("pm/artifacts.json")));for(const a of x.artifacts)console.log(a.id+"\t"+a.level);break}
case"hash":{if(!arg)throw Error("Usage: hash <repo-relative-file>");const p=safe(arg);if(!fs.statSync(p).isFile())throw Error("T3 refusal: hash requires a file");console.log(crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex"));break}
case"poster":if(!fs.existsSync(safe("buddy-poster-prompt.txt")))throw Error("Poster prompt missing");console.log("Poster prompt present; no rendering or network call performed.");break;
case"calibrate":process.exit(run(["calibrate.js"]));
default:throw Error("T1 refusal: unsupported command; arbitrary shell is not accepted.");
}}catch(e){console.error(e.message);process.exit(2)}
