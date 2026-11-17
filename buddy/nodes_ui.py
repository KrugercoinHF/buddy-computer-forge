from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()
PAGE = r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Buddy | Nodes</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#09111f;color:#e2e8f0;font:16px system-ui}main{max-width:1200px;margin:auto;padding:32px 20px}header{display:flex;justify-content:space-between;align-items:center}h1{margin-bottom:4px}p{color:#94a3b8}.card{background:#111e31;border:1px solid #26364b;border-radius:16px;padding:22px;margin:20px 0}.row{display:flex;gap:12px;flex-wrap:wrap;align-items:end}label{display:grid;gap:7px;flex:1;min-width:140px}input,button{font:inherit;border-radius:8px;padding:10px;border:1px solid #334155}input{background:#09111f;color:white;width:100%}button{background:#38bdf8;color:#082032;cursor:pointer}button:disabled{opacity:.4;cursor:not-allowed}.danger{background:#b91c1c;color:white}.scroll{overflow:auto}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:14px 9px;border-bottom:1px solid #26364b}th{color:#94a3b8}td{overflow-wrap:anywhere}a{color:#38bdf8}pre{white-space:pre-wrap;overflow-wrap:anywhere}#message{min-height:24px}dialog{background:#111e31;color:white;border:1px solid #38bdf8;border-radius:16px;max-width:90vw;width:640px}dialog::backdrop{background:#000a}</style>
<main><header><div><h1>Node management</h1><p>Buddy Computer Forge · Security Core</p></div><a href="/">Overview</a></header>
<section class="card"><form id="login" class="row"><label>Owner token<input id="token" type="password" autocomplete="off" required></label><button>Connect</button><button id="logout" type="button">Lock</button></form><p>Token held in memory only. Reload or lock to clear. Use HTTPS outside localhost.</p></section>
<div id="message" role="status" aria-live="polite"></div>
<section class="card"><h2>Invite a worker</h2><form id="invite" class="row"><label>Node ID<input id="node" maxlength="100" required></label><label>Display name<input id="name" maxlength="120" required></label><label>TTL in minutes<input id="ttl" type="number" min="1" max="60" value="15" required></label><button>Create invitation</button></form></section>
<section class="card"><div class="row"><h2>Registered workers</h2><button id="refresh">Refresh</button></div><p id="count">Connect to load workers.</p><div class="scroll"><table><thead><tr><th>Node</th><th>Name</th><th>Type</th><th>Reported status</th><th>Host</th><th>Last seen</th><th>Actions</th></tr></thead><tbody id="rows"></tbody></table></div><p>Status is server-reported, not a live connectivity guarantee.</p></section>
<dialog id="secret"><h2 id="secretTitle"></h2><p id="secretNote"></p><pre id="value"></pre><button id="copy">Copy secret</button><button id="close">Clear and close</button></dialog></main>
<script>
'use strict';
const el=id=>document.getElementById(id);let owner='',generation=0;
const message=t=>{el('message').textContent=t;};
function clearSecret(){el('value').textContent='';el('secretNote').textContent='';el('secret').close();}
function lock(){owner='';generation++;el('token').value='';el('rows').replaceChildren();el('count').textContent='Locked';clearSecret();message('Locked. Credentials and displayed data cleared.');}
async function api(path,body){if(!owner)throw Error('Connect with your owner token first.');const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:{Authorization:'Bearer '+owner,'Content-Type':'application/json'},cache:'no-store',redirect:'error',...(body===undefined?{}:{body:JSON.stringify(body)})});const data=await response.json().catch(()=>({}));if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Request failed: '+response.status);return data;}
async function run(button,work){button.disabled=true;try{await work();}catch(e){message(e.message);}finally{button.disabled=false;}}
function showSecret(title,value,note){el('secretTitle').textContent=title;el('value').textContent=value;el('secretNote').textContent=note;el('secret').showModal();}
async function refresh(){const current=generation;const nodes=await api('/api/nodes');if(current!==generation)return;el('rows').replaceChildren();el('count').textContent=nodes.length+' registered workers';for(const n of nodes){const tr=document.createElement('tr');for(const value of [n.id,n.name,n.node_type,n.revoked?'Revoked':n.status,n.hostname,n.last_seen?new Date(n.last_seen).toLocaleString():'Never']){const td=document.createElement('td');td.textContent=value??'—';tr.append(td);}const actions=document.createElement('td');for(const kind of ['rotate-token','revoke']){const b=document.createElement('button');b.textContent=kind==='revoke'?'Revoke':'Rotate';b.disabled=Boolean(n.revoked);if(kind==='revoke')b.className='danger';b.onclick=()=>run(b,async()=>{if(!confirm((kind==='revoke'?'Revoke access for ':'Invalidate the old token for ')+n.id+'?'))return;const version=generation;const result=await api('/api/nodes/'+encodeURIComponent(n.id)+'/'+kind,{});if(version!==generation)return;if(kind==='rotate-token')showSecret('Replacement node token',result.node_token,'Update this worker’s credential file securely and restart it. The previous token is invalid.');await refresh();message('Node updated.');});actions.append(b,document.createTextNode(' '));}tr.append(actions);el('rows').append(tr);}}
el('login').onsubmit=e=>{e.preventDefault();owner=el('token').value;el('token').value='';generation++;run(e.submitter,async()=>{await refresh();message('Connected.');});};
el('logout').onclick=lock;el('refresh').onclick=e=>run(e.currentTarget,refresh);
el('invite').onsubmit=e=>{e.preventDefault();run(e.submitter,async()=>{const version=generation;const result=await api('/api/nodes/enrollments',{node_id:el('node').value.trim(),name:el('name').value.trim(),node_type:'worker',ttl_minutes:Number(el('ttl').value)});if(version!==generation)return;showSecret('One-time enrollment code',result.enrollment_code,'Expires '+new Date(result.expires_at).toLocaleString()+'. Share securely with the intended worker.');message('Invitation created.');});};
el('copy').onclick=e=>run(e.currentTarget,async()=>{await navigator.clipboard.writeText(el('value').textContent);message('Copied. Clear your clipboard after use.');});
el('close').onclick=clearSecret;el('secret').addEventListener('cancel',e=>{e.preventDefault();clearSecret();});
window.addEventListener('pagehide',lock);
</script></html>'''


@router.get('/nodes', response_class=HTMLResponse)
def nodes_dashboard():
    return HTMLResponse(PAGE, headers={
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'Content-Security-Policy': "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
    })
