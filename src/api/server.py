import asyncio, secrets, random, json, base64, zipfile, io
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from src.core.kernel import ApexKernel

app = FastAPI(title="ApexOS Hybrid")
kernel = ApexKernel()
APPS_DIR = Path(__file__).resolve().parent.parent.parent / "apps"

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "credentialless"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

def discover_apps():
    apps = []
    if APPS_DIR.exists():
        for d in sorted(APPS_DIR.iterdir()):
            if d.is_dir() and (d / "manifest.json").exists():
                try:
                    data = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
                    apps.append(data)
                except Exception:
                    pass
    return apps

@app.get("/api/apps")
async def list_apps():
    return JSONResponse(discover_apps())

@app.get("/api/v1/sys/telemetry")
async def sys_telemetry():
    kernel.sudo.purge_expired()
    return JSONResponse(kernel.telemetry())

@app.post("/api/apx/install")
async def apx_install(file: UploadFile = File(...)):
    try:
        data = await file.read()
        zf = zipfile.ZipFile(io.BytesIO(data))
        files = {}
        manifest = None
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            parts = name.split("/")
            rel = "/".join(parts[1:]) if len(parts) > 1 and parts[0] and not parts[0].endswith(".json") and "manifest" not in parts[0] else name
            if name.endswith("manifest.json") or rel.endswith("manifest.json"):
                manifest = json.loads(zf.read(name).decode("utf-8"))
                rel = "manifest.json"
            content = zf.read(name)
            try:
                files[rel if rel != name or name.endswith("manifest.json") else name.split("/")[-1]] = content.decode("utf-8")
            except UnicodeDecodeError:
                files[rel] = base64.b64encode(content).decode("ascii")
        if not manifest:
            for k, v in files.items():
                if k.endswith("manifest.json"):
                    manifest = json.loads(v)
                    break
        if not manifest:
            return JSONResponse({"ok": False, "error": "manifest.json not found in package"}, status_code=400)
        clean = {}
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            base = name.split("/")[-1]
            raw = zf.read(name)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = "[binary]"
            if base == "manifest.json":
                clean["manifest.json"] = text
            else:
                segs = name.replace("\\", "/").split("/")
                rel = "/".join(segs[1:]) if len(segs) > 1 else segs[0]
                clean[rel] = text
        msg = kernel.apx_install_from_json(manifest, clean, grant_perms=False)
        return JSONResponse({"ok": True, "message": msg, "manifest": manifest})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.get("/api/packages/{app_id}/{file_path:path}")
async def get_package_file(app_id: str, file_path: str):
    path = f"/home/apps/{app_id}/{file_path}"
    content = kernel.vfs.read_file_content(path)
    if content.startswith("cat:"):
        return JSONResponse({"ok": False, "error": "File not found"}, status_code=404)
    media = "text/html" if file_path.endswith(".html") else "application/javascript" if file_path.endswith(".js") else "application/json" if file_path.endswith(".json") else "text/plain"
    from fastapi.responses import Response
    return Response(content=content, media_type=media)

@app.get("/api/permissions")
async def get_perms():
    return JSONResponse(kernel.get_permissions())

@app.post("/api/permissions/grant")
async def grant_perm(body: dict):
    app_id = body.get("app_id", "")
    permission = body.get("permission", "")
    if not app_id or not permission:
        return JSONResponse({"ok": False, "error": "app_id and permission required"}, status_code=400)
    msg = kernel.grant_permission(app_id, permission)
    return JSONResponse({"ok": True, "message": msg})

APPS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/apps", StaticFiles(directory=str(APPS_DIR)), name="apps")

HTML_INTERFACE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ApexOS Hybrid</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;font-family:'Segoe UI',system-ui,sans-serif;background:#0a0e17;color:#e0e6ed;user-select:none}
#desktop{position:absolute;inset:0 0 48px 0;background:linear-gradient(160deg,#0a1628,#0d2137 40%,#071020);overflow:hidden}
.desktop-icon{position:absolute;width:82px;text-align:center;cursor:pointer;padding:10px 4px;border-radius:10px;transition:.15s}
.desktop-icon:hover{background:rgba(255,255,255,.09);transform:scale(1.04)}
.desktop-icon .icon{font-size:36px;filter:drop-shadow(0 3px 6px rgba(0,0,0,.45))}
.desktop-icon .label{font-size:12px;margin-top:4px;text-shadow:0 1px 3px #000}
#taskbar{position:absolute;bottom:0;left:0;right:0;height:48px;background:rgba(8,12,20,.94);backdrop-filter:blur(12px);border-top:1px solid rgba(255,255,255,.07);display:flex;align-items:center;padding:0 10px;gap:6px;z-index:9999}
#start-btn{width:42px;height:36px;border:none;border-radius:9px;background:linear-gradient(135deg,#00c6ff,#0066ff);color:#fff;font-size:17px;cursor:pointer}
.taskbar-apps{display:flex;gap:4px;flex:1;overflow-x:auto}
.taskbar-app{height:36px;padding:0 12px;border-radius:8px;background:rgba(255,255,255,.05);border:1px solid transparent;color:#c8d2de;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:6px}
.taskbar-app.active,.taskbar-app:hover{background:rgba(255,255,255,.12);border-color:rgba(0,170,255,.3)}
#clock{font-size:13px;padding:0 12px;color:#8a9aab}
#start-menu{position:absolute;bottom:56px;left:8px;width:280px;background:rgba(12,18,28,.97);border:1px solid rgba(255,255,255,.09);border-radius:14px;padding:12px;display:none;z-index:10000}
#start-menu.open{display:block}
.start-item{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;cursor:pointer;font-size:14px}
.start-item:hover{background:rgba(0,140,255,.14)}
.start-sep{height:1px;background:rgba(255,255,255,.07);margin:8px 0}
.window{position:absolute;min-width:300px;min-height:200px;background:#111822;border:1px solid rgba(255,255,255,.09);border-radius:11px;box-shadow:0 18px 52px rgba(0,0,0,.55);display:flex;flex-direction:column;overflow:hidden;z-index:100}
.window.focused{border-color:rgba(0,170,255,.4);z-index:200}
.titlebar{height:36px;background:linear-gradient(180deg,#1b2536,#151e2c);display:flex;align-items:center;padding:0 10px;cursor:grab;border-bottom:1px solid rgba(255,255,255,.05)}
.titlebar .title{flex:1;font-size:13px;color:#c5d0dc}
.win-btn{width:12px;height:12px;border-radius:50%;border:none;cursor:pointer;margin-left:6px}
.win-btn.close{background:#ff5f57}.win-btn.min{background:#febc2e}.win-btn.max{background:#28c840}
.window-body{flex:1;overflow:hidden;background:#0d1219}
.terminal{height:100%;display:flex;flex-direction:column;font-family:Consolas,monospace;font-size:13px}
.term-output{flex:1;overflow-y:auto;padding:12px;white-space:pre-wrap;color:#11ff55}
.term-output .cmd-line{color:#00bfff}.term-output .error{color:#ff6b6b}
.term-input-row{display:flex;padding:8px 12px;border-top:1px solid rgba(17,255,85,.12);background:#0a0f14}
.term-prompt{color:#00bfff;font-weight:600;margin-right:8px;white-space:nowrap}
.term-input{flex:1;background:transparent;border:none;outline:none;color:#11ff55;font-family:inherit;font-size:inherit}
.panel{height:100%;display:flex;flex-direction:column;font-size:13px}
.panel-tabs{display:flex;gap:4px;padding:8px;background:#151e2c;border-bottom:1px solid rgba(255,255,255,.06)}
.panel-tabs button{background:#1a2435;border:1px solid rgba(255,255,255,.08);color:#c5d0dc;border-radius:6px;padding:6px 12px;cursor:pointer;font-size:12px}
.panel-tabs button.active{background:#0066ff;border-color:#0066ff;color:#fff}
.panel-body{flex:1;overflow-y:auto;padding:16px}
.card{background:#151e2c;border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:14px;margin-bottom:12px}
.card h3{font-size:14px;margin-bottom:8px;color:#00c6ff}
.card p,.card li{color:#a0b0c0;font-size:12px;line-height:1.5}
.btn{background:#0066ff;border:none;color:#fff;border-radius:6px;padding:8px 14px;cursor:pointer;font-size:12px;font-weight:600;margin-right:6px;margin-top:6px}
.btn.secondary{background:#1a2435;border:1px solid rgba(255,255,255,.1);color:#c5d0dc}
.btn.danger{background:#ff5f57}
.status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.status-dot.on{background:#28c840}.status-dot.off{background:#ff5f57}
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:50000;display:flex;align-items:center;justify-content:center}
.modal{background:#151e2c;border:1px solid rgba(255,255,255,.1);border-radius:14px;padding:24px;width:400px;max-width:90%}
.modal h2{margin-bottom:12px;font-size:16px}
.modal ul{margin:12px 0;padding-left:20px;color:#a0b0c0;font-size:13px}
#login-overlay{position:fixed;inset:0;background:radial-gradient(ellipse at center,#0c1a2e,#05080f);z-index:20000;display:flex;align-items:center;justify-content:center}
#login-overlay.hidden{display:none}
.login-box{background:rgba(12,18,30,.92);border:1px solid rgba(0,160,255,.22);border-radius:18px;padding:40px;width:360px;text-align:center}
.login-box h1{font-size:28px;margin-bottom:6px;background:linear-gradient(90deg,#00c6ff,#11ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.login-box p{color:#6a7a8a;font-size:13px;margin-bottom:20px}
.login-box input{width:100%;padding:11px;margin-bottom:10px;background:#0a1018;border:1px solid rgba(255,255,255,.09);border-radius:8px;color:#e0e6ed;font-size:14px;outline:none}
.login-box button{width:100%;padding:12px;margin-top:6px;background:linear-gradient(135deg,#00c6ff,#0066ff);border:none;border-radius:8px;color:#fff;font-size:15px;font-weight:600;cursor:pointer}
.login-error{color:#ff6b6b;font-size:13px;min-height:18px;margin-top:8px}
.login-hint{margin-top:14px;font-size:12px;color:#4a5a6a}
.explorer-toolbar{padding:8px;background:#151e2c;display:flex;gap:6px;align-items:center}
.explorer-path{flex:1;background:#0d1219;border:1px solid rgba(255,255,255,.07);border-radius:6px;padding:5px 10px;font-family:monospace;font-size:12px;color:#a0b0c0}
.file-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(90px,1fr));gap:8px;padding:12px}
.file-item{text-align:center;padding:10px;border-radius:8px;cursor:pointer}
.file-item:hover{background:rgba(0,140,255,.12)}
.calc-wrap{padding:14px;height:100%;display:flex;flex-direction:column;gap:10px}
.calc-display{background:#0a0f14;border-radius:10px;padding:16px;font-size:28px;text-align:right;color:#11ff55;font-family:monospace}
.calc-keys{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;flex:1}
.calc-keys button{border:none;border-radius:10px;font-size:18px;font-weight:600;cursor:pointer;color:#fff;background:#1a2435}
.calc-keys .op{background:#0066ff}.calc-keys .fn{background:#ff5f57}.calc-keys .eq{background:#00a86b}
.editor{height:100%;display:flex;flex-direction:column}
.editor-bar{padding:8px;background:#151e2c;display:flex;gap:6px}
.editor-bar input{flex:1;background:#0a1018;border:1px solid rgba(255,255,255,.09);border-radius:6px;padding:6px 10px;color:#c5d0dc;font-size:13px}
.editor textarea{flex:1;background:#0d1219;border:none;outline:none;color:#e0e6ed;font-family:Consolas,monospace;font-size:13px;padding:12px;resize:none}

/* === HexaDE theme === */
:root{--haiku-yellow:#f0c000;--root-red:#c0392b;--border-color:#2a2d32}
.titlebar.hexade{background:linear-gradient(180deg,#2a2d32,#1e2126);border-bottom:2px solid var(--haiku-yellow)}
.titlebar.hexade.root-privilege{border-bottom-color:var(--root-red);background:linear-gradient(180deg,#3a2222,#2a1818)}
.titlebar.hexade.root-privilege .title{color:#ff8882}
.window.hexade{border-radius:2px;border:1px solid var(--border-color)}
.window.hexade.focused{border-color:var(--haiku-yellow)}
.window.hexade.focused.root-frame{border-color:var(--root-red);box-shadow:0 0 0 1px var(--root-red),0 18px 52px rgba(0,0,0,.55)}
.xfce-menu-bar{display:flex;gap:12px;padding:4px 10px;background:#2a2d32;border-bottom:1px solid var(--border-color);font-size:11px;color:var(--haiku-yellow)}
.xfce-menu-item{cursor:pointer}.xfce-menu-item:hover{color:#fff}
#taskman-table{width:100%;border-collapse:collapse;font-size:12px}
#taskman-table th{background:#2a2d32;color:var(--haiku-yellow);padding:6px;text-align:left;border-bottom:1px solid var(--border-color)}
#taskman-table td{padding:6px;border-bottom:1px solid #1c1d22}
#taskman-table tbody tr{cursor:pointer}
#taskman-table tbody tr:hover{background:#26292f}
#taskman-table tbody tr.selected{background:#343842;outline:1px solid var(--haiku-yellow)}
#taskman-table tbody tr.selected-root{outline:1px solid var(--root-red)}
.taskman-alert{background:#3a2222;border-bottom:1px solid var(--root-red);color:#ff8882;font-size:11px;padding:4px 10px}
</style>
</head>
<body>
<div id="login-overlay">
  <div class="login-box">
    <h1>ApexOS</h1>
    <p>Hybrid Edition — Web APIs · Packages · Hardware</p>
    <input id="login-user" value="root" placeholder="Username">
    <input id="login-pass" type="password" value="password" placeholder="Password">
    <button id="login-btn">Sign in</button>
    <div class="login-error" id="login-error"></div>
    <div class="login-hint">root / password · guest / guest</div>
  </div>
</div>
<div id="desktop"></div>
<div id="start-menu">
  <div id="start-apps"></div>
  <div class="start-sep"></div>
  <div class="start-item" id="logout-btn"><span style="width:28px;text-align:center">⏻</span> Sign out</div>
</div>
<div id="taskbar">
  <button id="start-btn">◆</button>
  <div class="taskbar-apps" id="taskbar-apps"></div>
  <div id="clock"></div>
</div>
<script>
(() => {
  let ws = null, 
      sessionToken = sessionStorage.getItem("apex_token") || "", 
      currentUser = sessionStorage.getItem("apex_user") || "", 
      currentCwd = "/", winId = 1, wsReady = false, pendingLogin = null;

  const APP_REGISTRY = {
    terminal:  {id:"terminal",  name:"Terminal",   icon:"💻", desktop:true},
    explorer:  {id:"explorer",  name:"Files",      icon:"📁", desktop:true},
    settings:  {id:"settings",  name:"Settings",   icon:"⚙️", desktop:true},
    packages:  {id:"packages",  name:"Packages",   icon:"📦", desktop:true},
    calculator:{id:"calculator",name:"Calculator", icon:"🧮", desktop:true},
    text_editor:{id:"text_editor",name:"Editor",   icon:"📝", desktop:true},
    browser:   {id:"browser",   name:"Browser",    icon:"🌐", desktop:true},
    sysinfo:   {id:"sysinfo",   name:"System",     icon:"ℹ️", desktop:true},
    media:     {id:"media",     name:"Media",      icon:"🎬", desktop:true},
    taskman:   {id:"taskman",   name:"Tasks",      icon:"📊", desktop:true},
    wasmtest:  {id:"wasmtest",  name:"Wasm Test",  icon:"⚡", desktop:true},
  };
  const $= (s,c=document)=>c.querySelector(s);
  const $$= (s,c=document)=>[...c.querySelectorAll(s)];

  function updateClock(){
    const n=new Date();
    $("#clock").textContent=n.toLocaleTimeString("en-US",{hour:"2-digit",minute:"2-digit"})+"  "+n.toLocaleDateString("en-US",{day:"2-digit",month:"short"});
  }
  setInterval(updateClock,1000); updateClock();

  function connectWS(){
    const proto=location.protocol==="https:"?"wss":"ws";
    try { if(ws){ ws.onclose=null; ws.close(); } } catch(e){}
    ws=new WebSocket(`${proto}://${location.host}/ws`);
    ws.onopen=()=>{
      wsReady=true;
      const err=$("#login-error");
      if(err && err.textContent.includes("Connecting")) err.textContent="Connected — click Sign in.";
      if(pendingLogin){const {user,pass}=pendingLogin; pendingLogin=null; doLoginSend(user,pass);}
    };
    ws.onmessage=(ev)=>{try{const d=JSON.parse(ev.data); if(d.token){sessionToken=d.token; sessionStorage.setItem("apex_token", sessionToken);} if(d.user){currentUser=d.user; sessionStorage.setItem("apex_user", currentUser);} if(d.cwd)currentCwd=d.cwd; document.dispatchEvent(new CustomEvent("apex-msg",{detail:d}));}catch(e){}};
    ws.onerror=()=>{wsReady=false;};
    ws.onclose=()=>{wsReady=false; setTimeout(connectWS,1500);};
  }
  connectWS();

  // Auto-bypass login if session token exists in storage
  if (sessionToken && currentUser) {
    $("#login-overlay").classList.add("hidden");
    buildDesktop();
  }

  function sendCmd(raw){ if(ws&&ws.readyState===1) ws.send(JSON.stringify({token:sessionToken,raw_input:raw})); }
  function sendWrite(path,content){ if(ws&&ws.readyState===1) ws.send(JSON.stringify({token:sessionToken,action:"write_file",path,content})); }

  function doLoginSend(user,pass){
    $("#login-error").textContent="Signing in...";
    let done=false;
    const timer=setTimeout(()=>{
      if(!done){ done=true; document.removeEventListener("apex-msg",h);
        $("#login-error").textContent="Login timed out — WebSocket not responding. Refresh the page."; }
    }, 8000);
    const h=(e)=>{
      const d=e.detail;
      if(d.token){
        done=true; clearTimeout(timer); document.removeEventListener("apex-msg",h);
        sessionToken=d.token; 
        if(d.user) currentUser=d.user; 
        if(d.cwd) currentCwd=d.cwd;
        
        sessionStorage.setItem("apex_token", sessionToken);
        sessionStorage.setItem("apex_user", currentUser);

        $("#login-overlay").classList.add("hidden");
        buildDesktop();
        setTimeout(()=>openApp("terminal"),200);
      } else if(d.output&&/denied|invalid|Access/i.test(d.output)){
        done=true; clearTimeout(timer); document.removeEventListener("apex-msg",h);
        $("#login-error").textContent="Invalid credentials.";
      }
    };
    document.addEventListener("apex-msg",h);
    if(ws && ws.readyState===1){
      ws.send(JSON.stringify({token:"", raw_input:`login ${user} ${pass}`}));
    } else {
      done=true; clearTimeout(timer); document.removeEventListener("apex-msg",h);
      $("#login-error").textContent="Not connected — wait a second and try again.";
    }
  }
  function doLogin(){
    const user=$("#login-user").value.trim(), pass=$("#login-pass").value;
    if(!user||!pass){$("#login-error").textContent="Fill both fields.";return;}
    if(!ws || ws.readyState!==1){
      pendingLogin={user,pass};
      $("#login-error").textContent="Connecting to server...";
      if(!ws || ws.readyState===3) connectWS();
      return;
    }
    doLoginSend(user,pass);
  }
  $("#login-btn").onclick=doLogin;
  $("#login-pass").onkeydown=e=>{if(e.key==="Enter")doLogin();};

  const startMenu=$("#start-menu");
  $("#start-btn").onclick=e=>{e.stopPropagation(); startMenu.classList.toggle("open");};
  document.addEventListener("click",()=>startMenu.classList.remove("open"));
  startMenu.onclick=e=>e.stopPropagation();
  
  $("#logout-btn").onclick=()=>{
    sessionStorage.removeItem("apex_token");
    sessionStorage.removeItem("apex_user");
    location.reload();
  };

  function buildDesktop(){
    const desk=$("#desktop"); desk.innerHTML="";
    const sm=$("#start-apps"); sm.innerHTML="";
    let i=0;
    Object.values(APP_REGISTRY).filter(a=>a.desktop).forEach(app=>{
      const ic=document.createElement("div");
      ic.className="desktop-icon";
      ic.style.top=(20+i*96)+"px"; ic.style.left="18px";
      ic.innerHTML=`<div class="icon">${app.icon}</div><div class="label">${app.name}</div>`;
      ic.ondblclick=()=>openApp(app.id);
      desk.appendChild(ic);
      const si=document.createElement("div");
      si.className="start-item";
      si.innerHTML=`<span style="width:28px;text-align:center">${app.icon}</span> ${app.name}`;
      si.onclick=()=>{openApp(app.id); startMenu.classList.remove("open");};
      sm.appendChild(si);
      i++;
    });
  }

  function createWindow(title, icon, w=640, h=420){
    const id="w"+(winId++);
    const win=document.createElement("div");
    win.className="window focused hexade"; win.dataset.id=id;
    win.style.cssText=`width:${w}px;height:${h}px;left:${40+(winId%6)*28}px;top:${30+(winId%4)*24}px`;
    win.innerHTML=`<div class="titlebar hexade"><span class="title">${icon} ${title}</span>
      <button class="win-btn min"></button><button class="win-btn max"></button><button class="win-btn close"></button></div>
      <div class="window-body"></div>`;
    $("#desktop").appendChild(win);
    const bar=$(".titlebar",win); let ox,oy,drag=false;
    bar.onmousedown=e=>{if(e.target.classList.contains("win-btn"))return; drag=true; ox=e.clientX-win.offsetLeft; oy=e.clientY-win.offsetTop; $$(".window").forEach(w=>w.classList.remove("focused")); win.classList.add("focused");};
    document.addEventListener("mousemove",e=>{if(!drag)return; win.style.left=Math.max(0,e.clientX-ox)+"px"; win.style.top=Math.max(0,e.clientY-oy)+"px";});
    document.addEventListener("mouseup",()=>drag=false);
    win.onmousedown=()=>{$$(".window").forEach(w=>w.classList.remove("focused")); win.classList.add("focused");};
    const tb=document.createElement("div"); tb.className="taskbar-app active"; tb.dataset.id=id;
    tb.innerHTML=`${icon} ${title.split("—")[0].trim()}`;
    tb.onclick=()=>{win.style.display="flex"; $$(".window").forEach(w=>w.classList.remove("focused")); win.classList.add("focused");};
    $("#taskbar-apps").appendChild(tb);
    $(".win-btn.close",win).onclick=()=>{win.remove();tb.remove();};
    $(".win-btn.min",win).onclick=()=>{win.style.display="none";};
    let mx=false,prev;
    $(".win-btn.max",win).onclick=()=>{if(!mx){prev={l:win.style.left,t:win.style.top,w:win.style.width,h:win.style.height}; win.style.cssText+=";left:0;top:0;width:100%;height:calc(100% - 48px)"; mx=true;}else{Object.assign(win.style,prev); mx=false;}};
    return {win, body:$(".window-body",win), id};
  }

  function openApp(name, opts={}){
    if(name==="terminal") openTerminal();
    else if(name==="explorer") openExplorer();
    else if(name==="settings") openSettings();
    else if(name==="packages") openPackages();
    else if(name==="calculator") openCalculator();
    else if(name==="text_editor") openEditor(opts);
    else if(name==="browser") openBrowser();
    else if(name==="sysinfo") openSysInfo();
    else if(name==="media") openMediaPlayer();
    else if(name==="taskman") openTaskManager();
    else if(name==="wasmtest") openWasmTest();
  }

  function openTerminal(){
    const {win,body}=createWindow("Terminal","💻",700,440);
    body.innerHTML=`<div class="terminal"><div class="term-output"></div><div class="term-input-row">
      <span class="term-prompt">${currentUser||"user"}@apexos:${currentCwd}#</span>
      <input class="term-input" spellcheck="false" autocomplete="off"></div></div>`;
    const out=$(".term-output",body), input=$(".term-input",body), prompt=$(".term-prompt",body);
    const hist=[]; let hi=-1;
    out.innerHTML=`<span style="color:#6a7a8a">ApexOS Hybrid — type 'help' for commands (apx, lsusb, bluetooth, network…)</span>\n\n`;
    const append=(t,c="")=>{const s=document.createElement("span"); if(c)s.className=c; s.textContent=t+"\n"; out.appendChild(s); out.scrollTop=out.scrollHeight;};
    const h=(e)=>{const d=e.detail; if(d.output!==undefined) append(d.output, /Error|not found|denied|Unable|cannot/i.test(d.output)?"error":""); if(d.user&&d.cwd) prompt.textContent=`${d.user}@apexos:${d.cwd}#`;};
    document.addEventListener("apex-msg",h);
    const oc=$(".win-btn.close",win).onclick; $(".win-btn.close",win).onclick=()=>{document.removeEventListener("apex-msg",h); oc();};
    input.onkeydown=e=>{
      if(e.key==="Enter"){
        const cmd=input.value.trim(); if(!cmd && !input.dataset.sudoPending)return;
        if(input.dataset.sudoPending!==undefined){
          const pending=input.dataset.sudoPending; const password=input.value;
          delete input.dataset.sudoPending; input.type="text"; input.value="";
          const hh=(ev)=>{
            const d=ev.detail;
            if(d.sudo_ok===true){
              win._elevToken=d.elev_token;
              $(".titlebar",win).classList.add("root-privilege");
              win.classList.add("root-frame");
              append(d.output||"Elevated to root (15 min).");
              const ttl=Math.max(5,(d.expires_at||0)-Math.floor(Date.now()/1000));
              if(win._elevTimer) clearTimeout(win._elevTimer);
              win._elevTimer=setTimeout(()=>{
                win._elevToken=null;
                $(".titlebar",win).classList.remove("root-privilege");
                win.classList.remove("root-frame");
                append("sudo: elevation expired.");
              }, ttl*1000);
              if(ws&&ws.readyState===1) ws.send(JSON.stringify({token:sessionToken,elev_token:win._elevToken,raw_input:pending}));
              document.removeEventListener("apex-msg",hh);
            } else if(d.sudo_ok===false){
              append(d.output||"Sorry, try again.","error");
              document.removeEventListener("apex-msg",hh);
            }
          };
          document.addEventListener("apex-msg",hh);
          ws.send(JSON.stringify({token:sessionToken,action:"sudo_auth",password:password}));
          return;
        }
        append(`${prompt.textContent} ${cmd}`,"cmd-line"); hist.push(cmd); hi=hist.length;
        if(cmd.toLowerCase()==="clear") out.innerHTML="";
        else if(cmd.toLowerCase().startsWith("sudo ")){
          const real=cmd.slice(5).trim();
          if(!real){ append("usage: sudo <command>","error"); input.value=""; return; }
          if(win._elevToken){
            ws.send(JSON.stringify({token:sessionToken,elev_token:win._elevToken,raw_input:real}));
            input.value=""; return;
          }
          append("[sudo] password for "+(currentUser||"user")+": ");
          input.type="password"; input.dataset.sudoPending=real; input.value=""; return;
        }
        else if(cmd.toLowerCase()==="lsusb"){ handleLsusb(append); }
        else if(cmd.toLowerCase().startsWith("bluetooth")){ handleBluetoothCli(cmd, append); }
        else if(cmd.toLowerCase()==="network" || cmd.toLowerCase()==="netstat"){ handleNetworkCli(append); }
        else sendCmd(cmd);
        input.value="";
      } else if(e.key==="ArrowUp"){ if(hi>0){hi--; input.value=hist[hi];} e.preventDefault(); }
      else if(e.key==="ArrowDown"){ if(hi<hist.length-1){hi++; input.value=hist[hi];} else {hi=hist.length; input.value="";} e.preventDefault(); }
    };
    setTimeout(()=>input.focus(),40); win.onclick=()=>input.focus();
  }

  async function handleLsusb(append){
    if(!navigator.usb){ append("lsusb: WebUSB not supported in this browser.","error"); return; }
    try {
      const devices = await navigator.usb.getDevices();
      if(!devices.length){ append("lsusb: No authorized USB devices.\nTip: use Settings → USB to request access."); return; }
      devices.forEach((d,i)=>{
        append(`Bus 000 Device ${String(i).padStart(3,"0")}: ID ${d.vendorId.toString(16).padStart(4,"0")}:${d.productId.toString(16).padStart(4,"0")} ${d.productName||d.manufacturerName||"Unknown"}`);
      });
    } catch(e){ append("lsusb: "+e.message,"error"); }
  }

  async function handleBluetoothCli(cmd, append){
    if(!navigator.bluetooth){ append("bluetooth: Web Bluetooth not supported.","error"); return; }
    if(cmd.includes("scan")){
      append("Scanning for BLE devices (browser picker)…");
      try {
        const dev = await navigator.bluetooth.requestDevice({ acceptAllDevices:true, optionalServices:[] });
        append(`Found: ${dev.name||"(unnamed)"}  id=${dev.id}`);
      } catch(e){ append("bluetooth: "+e.message,"error"); }
    } else {
      append("Usage: bluetooth scan");
    }
  }

  function handleNetworkCli(append){
    const c = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    const online = navigator.onLine;
    append(`Online: ${online ? "yes" : "no"}`);
    if(c){
      append(`Type: ${c.effectiveType||c.type||"unknown"}`);
      if(c.downlink!=null) append(`Downlink: ${c.downlink} Mbps`);
      if(c.rtt!=null) append(`RTT: ${c.rtt} ms`);
      if(c.saveData!=null) append(`Data saver: ${c.saveData}`);
    } else {
      append("Network Information API not available — online status only.");
    }
  }

  function openSettings(){
    const {win,body}=createWindow("Settings","⚙️",560,480);
    body.innerHTML=`<div class="panel">
      <div class="panel-tabs">
        <button class="active" data-tab="network">Network</button>
        <button data-tab="bluetooth">Bluetooth</button>
        <button data-tab="usb">USB</button>
        <button data-tab="permissions">Permissions</button>
      </div>
      <div class="panel-body" id="settings-body"></div>
    </div>`;
    const pb=$("#settings-body",body);
    function show(tab){
      $$(".panel-tabs button",body).forEach(b=>b.classList.toggle("active",b.dataset.tab===tab));
      if(tab==="network") renderNetwork(pb);
      else if(tab==="bluetooth") renderBluetooth(pb);
      else if(tab==="usb") renderUsb(pb);
      else if(tab==="permissions") renderPermissions(pb);
    }
    $$(".panel-tabs button",body).forEach(b=>b.onclick=()=>show(b.dataset.tab));
    show("network");
  }

  function renderNetwork(el){
    const c=navigator.connection||navigator.mozConnection||navigator.webkitConnection;
    const online=navigator.onLine;
    el.innerHTML=`<div class="card"><h3><span class="status-dot ${online?"on":"off"}"></span>Connectivity</h3>
      <p>Status: <strong>${online?"Online":"Offline"}</strong></p>
      <p>Type: ${c?(c.effectiveType||c.type||"unknown"):"n/a"}</p>
      <p>Downlink: ${c&&c.downlink!=null?c.downlink+" Mbps":"n/a"}</p>
      <p>RTT: ${c&&c.rtt!=null?c.rtt+" ms":"n/a"}</p>
      <p>This panel reflects the host browser network via the Network Information API.</p>
      <button class="btn secondary" id="net-refresh">Refresh</button></div>`;
    $("#net-refresh",el).onclick=()=>renderNetwork(el);
  }

  function renderBluetooth(el){
    const ok=!!navigator.bluetooth;
    el.innerHTML=`<div class="card"><h3><span class="status-dot ${ok?"on":"off"}"></span>Web Bluetooth</h3>
      <p>${ok?"Supported in this browser.":"Not supported (try Chrome/Edge over HTTPS or localhost)."}</p>
      <button class="btn" id="bt-scan" ${ok?"":"disabled"}>Scan & pair BLE device</button>
      <div id="bt-list" style="margin-top:12px;font-family:monospace;font-size:12px;color:#11ff55"></div></div>`;
    if(ok) $("#bt-scan",el).onclick=async()=>{
      const list=$("#bt-list",el); list.textContent="Requesting device…";
      try{
        const d=await navigator.bluetooth.requestDevice({acceptAllDevices:true, optionalServices:[]});
        list.textContent=`Paired: ${d.name||"(no name)"}\nID: ${d.id}`;
      }catch(e){ list.textContent="Error: "+e.message; }
    };
  }

  function renderUsb(el){
    const ok=!!navigator.usb;
    el.innerHTML=`<div class="card"><h3><span class="status-dot ${ok?"on":"off"}"></span>WebUSB</h3>
      <p>${ok?"Supported. Request access to list devices.":"Not supported in this browser."}</p>
      <button class="btn" id="usb-req" ${ok?"":"disabled"}>Request USB device</button>
      <button class="btn secondary" id="usb-list" ${ok?"":"disabled"}>List authorized</button>
      <div id="usb-out" style="margin-top:12px;font-family:monospace;font-size:12px;color:#11ff55"></div></div>`;
    const out=$("#usb-out",el);
    if(ok){
      $("#usb-req",el).onclick=async()=>{
        try{ const d=await navigator.usb.requestDevice({filters:[]}); out.textContent=`Granted: ${d.productName||"device"} (${d.vendorId.toString(16)}:${d.productId.toString(16)})`; }
        catch(e){ out.textContent="Error: "+e.message; }
      };
      $("#usb-list",el).onclick=async()=>{
        const ds=await navigator.usb.getDevices();
        out.textContent=ds.length?ds.map(d=>`${d.vendorId.toString(16)}:${d.productId.toString(16)} ${d.productName||""}`).join("\n"):"No authorized devices.";
      };
    }
  }

  async function renderPermissions(el){
    el.innerHTML=`<div class="card"><h3>App permission registry</h3><p>Stored in /system/etc/permissions.json</p><pre id="perm-out" style="color:#11ff55;font-size:12px;margin-top:8px">Loading…</pre></div>`;
    try{
      const r=await fetch("/api/permissions"); const data=await r.json();
      $("#perm-out",el).textContent=Object.keys(data).length?JSON.stringify(data,null,2):"{} (no grants yet)";
    }catch(e){ $("#perm-out",el).textContent="Error loading permissions."; }
  }

  function openPackages(){
    const {win,body}=createWindow("Package Manager","📦",520,420);
    body.innerHTML=`<div class="panel"><div class="panel-body">
      <div class="card"><h3>Install .apx package</h3>
        <p>Select an .apx file (zip with manifest.json). You will be asked to grant declared permissions.</p>
        <input type="file" id="apx-file" accept=".apx,.zip" style="margin:8px 0;color:#a0b0c0;font-size:12px">
        <button class="btn" id="apx-install-btn">Install</button>
        <pre id="apx-log" style="margin-top:10px;color:#11ff55;font-size:12px;white-space:pre-wrap"></pre>
      </div>
      <div class="card"><h3>Installed packages</h3>
        <button class="btn secondary" id="apx-refresh">Refresh list</button>
        <pre id="apx-list" style="margin-top:10px;color:#c5d0dc;font-size:12px">—</pre>
      </div>
    </div></div>`;
    const log=$("#apx-log",body);
    $("#apx-install-btn",body).onclick=async()=>{
      const f=$("#apx-file",body).files[0];
      if(!f){ log.textContent="Choose a file first."; return; }
      log.textContent="Uploading…";
      const fd=new FormData(); fd.append("file", f);
      try{
        const r=await fetch("/api/apx/install",{method:"POST",body:fd});
        const j=await r.json();
        if(!j.ok){ log.textContent="Error: "+j.error; return; }
        const m=j.manifest||{};
        const perms=m.permissions||[];
        if(perms.length){
          showPermissionModal(m.id||m.name, perms, async(granted)=>{
            if(granted){
              for(const p of perms){
                await fetch("/api/permissions/grant",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({app_id:m.id,permission:p})});
              }
              log.textContent=j.message+"\nPermissions granted: "+perms.join(", ");
            } else {
              log.textContent=j.message+"\nPermissions denied by user (app installed without grants).";
            }
            refreshList();
          });
        } else {
          log.textContent=j.message;
          refreshList();
        }
      }catch(e){ log.textContent="Error: "+e.message; }
    };
    function refreshList(){
      const h=(e)=>{ if(e.detail.output!==undefined){ $("#apx-list",body).textContent=e.detail.output; document.removeEventListener("apex-msg",h);} };
      document.addEventListener("apex-msg",h);
      sendCmd("apx list");
    }
    $("#apx-refresh",body).onclick=refreshList;
    refreshList();
    const launchBtn=document.createElement("button");
    launchBtn.className="btn secondary";
    launchBtn.textContent="Open Media Player package";
    launchBtn.style.marginTop="8px";
    launchBtn.onclick=()=>openMediaPlayer({appId:"com.apex.mediaplayer", title:"Media Player (.apx)"});
    body.querySelectorAll(".card")[1].appendChild(launchBtn);
  }

  function showPermissionModal(appId, perms, cb){
    const bg=document.createElement("div"); bg.className="modal-bg";
    bg.innerHTML=`<div class="modal"><h2>Install permissions</h2>
      <p style="color:#a0b0c0;font-size:13px">App <strong>${appId}</strong> requests:</p>
      <ul>${perms.map(p=>`<li>${p}</li>`).join("")}</ul>
      <button class="btn" id="perm-allow">Allow</button>
      <button class="btn secondary" id="perm-deny">Deny</button></div>`;
    document.body.appendChild(bg);
    $("#perm-allow",bg).onclick=()=>{bg.remove(); cb(true);};
    $("#perm-deny",bg).onclick=()=>{bg.remove(); cb(false);};
  }

  function openExplorer(){
    const {win,body}=createWindow("Files","📁",560,400);
    body.innerHTML=`<div style="height:100%;display:flex;flex-direction:column">
      <div class="explorer-toolbar">
        <button class="btn secondary" data-a="up">⬆</button>
        <button class="btn secondary" data-a="ref">↻</button>
        <div class="explorer-path">/</div>
      </div>
      <div class="file-grid" style="flex:1;overflow:auto"></div></div>`;
    let expCwd=currentCwd||"/";
    const pathEl=$(".explorer-path",body), grid=$(".file-grid",body);
    function refresh(){
      pathEl.textContent=expCwd; grid.innerHTML="Loading…";
      const h=(e)=>{if(e.detail.output===undefined)return; document.removeEventListener("apex-msg",h);
        grid.innerHTML="";
        const raw=(e.detail.output||"").trim();
        if(!raw||raw==="(empty directory)"){ grid.innerHTML='<div style="grid-column:1/-1;color:#6a7a8a;padding:20px">Empty</div>'; return; }
        if(raw.startsWith("ls:")){ grid.innerHTML=`<div style="color:#ff6b6b">${raw}</div>`; return; }
        raw.split(/\s+/).filter(Boolean).forEach(item=>{
          const isDir=item.startsWith("[")&&item.endsWith("/]");
          const name=isDir?item.slice(1,-2):item;
          const div=document.createElement("div"); div.className="file-item";
          div.innerHTML=`<div style="font-size:28px">${isDir?"📁":"📄"}</div><div style="font-size:11px;margin-top:4px">${name}</div>`;
          div.ondblclick=()=>{ if(isDir){ expCwd=expCwd==="/"?"/"+name:expCwd+"/"+name; sendCmd("cd "+expCwd); setTimeout(refresh,80);} else openEditor({filename:(expCwd==="/"?"":expCwd)+"/"+name}); };
          grid.appendChild(div);
        });
      };
      document.addEventListener("apex-msg",h); sendCmd("cd "+expCwd); setTimeout(()=>sendCmd("ls"),50);
    }
    body.querySelector('[data-a="up"]').onclick=()=>{ if(expCwd==="/")return; const p=expCwd.split("/").filter(Boolean); p.pop(); expCwd="/"+p.join("/"); sendCmd("cd "+expCwd); setTimeout(refresh,80); };
    body.querySelector('[data-a="ref"]').onclick=refresh;
    refresh();
  }

  function openCalculator(){
    const {body}=createWindow("Calculator","🧮",280,400);
    body.innerHTML=`<div class="calc-wrap"><div class="calc-display" id="cd">0</div>
      <div class="calc-keys">
        <button class="fn" data-k="C">C</button><button class="fn" data-k="±">±</button><button class="fn" data-k="%">%</button><button class="op" data-k="÷">÷</button>
        <button data-k="7">7</button><button data-k="8">8</button><button data-k="9">9</button><button class="op" data-k="×">×</button>
        <button data-k="4">4</button><button data-k="5">5</button><button data-k="6">6</button><button class="op" data-k="-">−</button>
        <button data-k="1">1</button><button data-k="2">2</button><button data-k="3">3</button><button class="op" data-k="+">+</button>
        <button data-k="0" style="grid-column:span 2">0</button><button data-k=".">.</button><button class="eq" data-k="=">=</button>
      </div></div>`;
    let cur="0",op=null,prev=null,reset=false; const d=$("#cd",body);
    body.querySelectorAll("button").forEach(b=>b.onclick=()=>{
      const k=b.dataset.k;
      if((k>="0"&&k<="9")||k==="."){ if(reset){cur="0";reset=false;} if(k==="."&&cur.includes("."))return; cur=cur==="0"&&k!=="."?k:cur+k; }
      else if(k==="C"){cur="0";op=prev=null;} else if(k==="±")cur=String(+cur*-1); else if(k==="%")cur=String(+cur/100);
      else if(["+","-","×","÷"].includes(k)){prev=+cur;op=k;reset=true;}
      else if(k==="="&&op!=null){const a=prev,b=+cur; let r=0; if(op==="+")r=a+b; if(op==="-")r=a-b; if(op==="×")r=a*b; if(op==="÷")r=b?a/b:"Err"; cur=String(r); op=prev=null; reset=true;}
      d.textContent=cur;
    });
  }

  function openEditor(opts={}){
    const fn=opts.filename||"untitled.txt";
    const {win,body}=createWindow("Editor — "+fn,"📝",640,460);
    body.innerHTML=`<div class="editor"><div class="editor-bar"><input id="ep" value="${fn}">
      <button class="btn" id="es">Save</button><button class="btn secondary" id="eo">Open</button></div>
      <textarea id="ec" spellcheck="false"></textarea></div>`;
    const ta=$("#ec",body), path=$("#ep",body);
    if(opts.filename&&opts.filename!=="untitled.txt"){
      const h=(e)=>{if(e.detail.output!==undefined){ta.value=e.detail.output.startsWith("cat:")?"":e.detail.output; document.removeEventListener("apex-msg",h);}};
      document.addEventListener("apex-msg",h); sendCmd("cat "+opts.filename);
    }
    $("#es",body).onclick=()=>sendWrite(path.value.trim()||"untitled.txt", ta.value);
    $("#eo",body).onclick=()=>{const p=path.value.trim(); if(!p)return;
      const h=(e)=>{if(e.detail.output!==undefined){ta.value=e.detail.output.startsWith("cat:")?"":e.detail.output; document.removeEventListener("apex-msg",h);}};
      document.addEventListener("apex-msg",h); sendCmd("cat "+p);
    };
  }

  function openBrowser(){
    const {body}=createWindow("Browser","🌐",760,500);
    body.innerHTML=`<div style="height:100%;display:flex;flex-direction:column">
      <div style="padding:8px;background:#151e2c;display:flex;gap:6px">
        <input id="url" value="https://example.com" style="flex:1;background:#0a1018;border:1px solid rgba(255,255,255,.1);border-radius:6px;padding:6px 10px;color:#c5d0dc">
        <button class="btn" id="go">Go</button></div>
      <iframe id="bf" sandbox="allow-scripts allow-same-origin allow-forms" src="https://example.com" style="flex:1;border:none;background:#fff"></iframe></div>`;
    const go=()=>{let u=$("#url",body).value.trim(); if(!/^https?:/i.test(u))u="https://"+u; $("#url",body).value=u; $("#bf",body).src=u;};
    $("#go",body).onclick=go; $("#url",body).onkeydown=e=>{if(e.key==="Enter")go();};
  }

  function openMediaPlayer(opts={}){
    const title = opts.title || "Media Player";
    const {body} = createWindow(title, "🎬", 720, 480);
    const pkgUrl = opts.appId ? `/api/packages/${opts.appId}/index.html` : null;
    if(pkgUrl){
      body.innerHTML = `<iframe src="${pkgUrl}" style="width:100%;height:100%;border:none;background:#0d1219" sandbox="allow-scripts allow-same-origin allow-forms"></iframe>`;
      return;
    }
    body.innerHTML = `<iframe src="/api/packages/com.apex.mediaplayer/index.html" style="width:100%;height:100%;border:none;background:#0d1219" sandbox="allow-scripts allow-same-origin allow-forms" id="media-frame"></iframe>
      <div id="media-fallback" style="display:none;height:100%;flex-direction:column">
        <div style="padding:10px;background:#151e2c;display:flex;gap:8px;align-items:center">
          <button class="btn" id="m-open">Open file</button>
          <button class="btn secondary" id="m-da">Demo audio</button>
          <button class="btn secondary" id="m-dv">Demo video</button>
          <span id="m-name" style="font-size:12px;color:#8a9aab;margin-left:auto">No media</span>
          <input type="file" id="m-file" accept="audio/*,video/*" hidden>
        </div>
        <div id="m-stage" style="flex:1;display:flex;align-items:center;justify-content:center;background:#05080f;color:#6a7a8a;font-size:13px">
          <div style="text-align:center"><div style="font-size:48px">🎬</div>Open a file or try a demo</div>
        </div>
      </div>`;
    const frame = body.querySelector("#media-frame");
    frame.onerror = showFallback;
    fetch("/api/packages/com.apex.mediaplayer/index.html").then(r=>{
      if(!r.ok) showFallback();
    }).catch(showFallback);
    function showFallback(){
      if(frame) frame.style.display="none";
      const fb = body.querySelector("#media-fallback");
      if(fb){ fb.style.display="flex"; bindFallback(fb); }
    }
    function bindFallback(root){
      const stage = root.querySelector("#m-stage");
      const fileInput = root.querySelector("#m-file");
      const nameEl = root.querySelector("#m-name");
      let media=null, url=null;
      function loadEl(el, label){
        if(media){ media.pause(); media.remove(); }
        if(url) URL.revokeObjectURL(url);
        media=el; stage.innerHTML=""; stage.appendChild(el); nameEl.textContent=label; el.controls=true; el.style.maxWidth="100%"; el.style.maxHeight="100%"; el.play().catch(()=>{});
      }
      root.querySelector("#m-open").onclick=()=>fileInput.click();
      fileInput.onchange=()=>{
        const f=fileInput.files[0]; if(!f)return;
        url=URL.createObjectURL(f);
        if(f.type.startsWith("video/")||/\.(mp4|webm)$/i.test(f.name)){ const v=document.createElement("video"); v.src=url; loadEl(v,f.name); }
        else { const a=document.createElement("audio"); a.src=url; a.style.width="80%"; loadEl(a,f.name); }
      };
      root.querySelector("#m-da").onclick=()=>{ const a=document.createElement("audio"); a.src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"; loadEl(a,"Demo audio"); };
      root.querySelector("#m-dv").onclick=()=>{ const v=document.createElement("video"); v.src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"; loadEl(v,"Demo video"); };
    }
  }

  function openTaskManager(){
    const {win,body}=createWindow("Task Manager","📊",520,380);
    body.innerHTML=`<div style="height:100%;display:flex;flex-direction:column;background:#1a1b1e">
      <div class="xfce-menu-bar">
        <span class="xfce-menu-item" id="tm-refresh">🔄 Refresh</span>
        <span class="xfce-menu-item" id="tm-sudo">⚡ Sudo mode</span>
      </div>
      <div class="taskman-alert" id="tm-alert">Guest mode — elevate to kill root processes.</div>
      <div style="flex:1;overflow:auto"><table id="taskman-table">
        <thead><tr><th>PID</th><th>Name</th><th>User</th><th>CPU %</th><th>RAM</th></tr></thead>
        <tbody id="tm-body"></tbody>
      </table></div>
      <div style="height:32px;border-top:1px solid #2a2d32;display:flex;justify-content:space-between;align-items:center;padding:0 10px;background:#1a1b1e">
        <span id="tm-stats" style="font-size:11px;color:#8a8d98">Total: 0</span>
        <button class="btn danger" id="tm-kill" disabled style="padding:2px 10px;font-size:11px">End task</button>
      </div></div>`;
    let selected=null, elev=null;
    const titlebar=$(".titlebar",win);
    async function refresh(){
      try{
        const r=await fetch("/api/v1/sys/telemetry");
        const rows=await r.json();
        const tb=body.querySelector("#tm-body"); tb.innerHTML="";
        rows.forEach(p=>{
          const tr=document.createElement("tr");
          tr.innerHTML=`<td>${p.pid}</td><td>${p.name}</td><td>${p.user}</td><td>${p.cpu_usage}</td><td>${p.mem_usage}</td>`;
          tr.onclick=()=>{
            tb.querySelectorAll("tr").forEach(x=>x.classList.remove("selected","selected-root"));
            tr.classList.add(p.user==="root"?"selected-root":"selected");
            selected=p; body.querySelector("#tm-kill").disabled=false;
          };
          tb.appendChild(tr);
        });
        body.querySelector("#tm-stats").textContent="Total: "+rows.length+" processes";
      }catch(e){ body.querySelector("#tm-stats").textContent="Telemetry error"; }
    }
    body.querySelector("#tm-refresh").onclick=refresh;
    body.querySelector("#tm-sudo").onclick=()=>{
      const pw=prompt("[sudo] password for "+currentUser+":");
      if(pw==null)return;
      const h=(e)=>{
        if(e.detail.sudo_ok){
          elev=e.detail.elev_token;
          titlebar.classList.add("root-privilege");
          win.classList.add("root-frame");
          body.querySelector("#tm-alert").style.display="none";
        } else if(e.detail.sudo_ok===false){
          alert(e.detail.output||"Sorry, try again.");
        }
        document.removeEventListener("apex-msg",h);
      };
      document.addEventListener("apex-msg",h);
      ws.send(JSON.stringify({token:sessionToken,action:"sudo_auth",password:pw}));
    };
    body.querySelector("#tm-kill").onclick=()=>{
      if(!selected)return;
      if(selected.user==="root"&&!elev&&currentUser!=="root"){
        alert("Permission denied: use Sudo mode to kill root tasks.");
        return;
      }
      const payload={token:sessionToken,raw_input:"kill "+selected.pid};
      if(elev) payload.elev_token=elev;
      ws.send(JSON.stringify(payload));
      setTimeout(refresh,300);
    };
    refresh();
    const iv=setInterval(refresh,1000);
    const oc=$(".win-btn.close",win).onclick;
    $(".win-btn.close",win).onclick=()=>{clearInterval(iv); if(oc)oc();};
  }

  function openSysInfo(){
    const {body}=createWindow("System","ℹ️",420,280);
    body.innerHTML=`<div style="padding:20px;font-family:monospace;font-size:13px;color:#11ff55;white-space:pre-wrap">Loading…</div>`;
    const h=(e)=>{if(e.detail.output&&e.detail.output.includes("OS")){ $("div",body).textContent=e.detail.output; document.removeEventListener("apex-msg",h); }};
    document.addEventListener("apex-msg",h); sendCmd("sysinfo");
  }

  let activeContextMenu = null;
  function closeContextMenu() {
    if (activeContextMenu) {
      activeContextMenu.remove();
      activeContextMenu = null;
    }
  }
  function showContextMenu(x, y, items) {
    closeContextMenu();
    const menu = document.createElement("div");
    menu.className = "apex-context-menu";
    menu.style.cssText = `
      position: absolute; top: ${y}px; left: ${x}px;
      background: #151e2c; border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 8px; padding: 6px 0; min-width: 170px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
      z-index: 999999; font-family: 'Segoe UI', system-ui, sans-serif;
      font-size: 13px; color: #e0e6ed;
    `;
    items.forEach((item) => {
      if (item === "separator") {
        const sep = document.createElement("div");
        sep.style.cssText = "height: 1px; background: rgba(255, 255, 255, 0.08); margin: 4px 0;";
        menu.appendChild(sep); return;
      }
      const row = document.createElement("div");
      row.style.cssText = `padding: 7px 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; user-select: none; transition: background 0.15s ease;`;
      row.innerHTML = `<span>${item.icon || ""}</span> <span>${item.label}</span>`;
      row.onmouseenter = () => { row.style.background = "#0066ff"; row.style.color = "#ffffff"; };
      row.onmouseleave = () => { row.style.background = "transparent"; row.style.color = "#e0e6ed"; };
      row.onclick = (e) => {
        e.stopPropagation(); closeContextMenu();
        if (item.action) item.action();
      };
      menu.appendChild(row);
    });
    document.body.appendChild(menu);
    activeContextMenu = menu;
    const rect = menu.getBoundingClientRect();
    if (rect.right > window.innerWidth) menu.style.left = `${x - rect.width}px`;
    if (rect.bottom > window.innerHeight) menu.style.top = `${y - rect.height}px`;
  }

  document.addEventListener("click", () => closeContextMenu());
  document.addEventListener("contextmenu", (e) => {
    const desktop = $("#desktop");
    const isDesktopBg = e.target === desktop || e.target.id === "desktop";
    const iconEl = e.target.closest(".desktop-icon");

    if (isDesktopBg) {
      e.preventDefault();
      showContextMenu(e.clientX, e.clientY, [
        { label: "Open Terminal", icon: "💻", action: () => openApp("terminal") },
        { label: "Open Files", icon: "📁", action: () => openApp("explorer") },
        "separator",
        { label: "Refresh Desktop", icon: "🔄", action: () => location.reload() },
        { label: "System Info", icon: "ℹ️", action: () => openApp("sysinfo") }
      ]);
    } else if (iconEl) {
      e.preventDefault();
      const appName = iconEl.querySelector(".label")?.textContent || "App";
      const iconChar = iconEl.querySelector(".icon")?.textContent || "🚀";
      showContextMenu(e.clientX, e.clientY, [
        { label: "Open " + appName, icon: iconChar, action: () => iconEl.dispatchEvent(new Event("dblclick")) },
        "separator",
        { label: "Properties", icon: "ℹ️", action: () => alert("App: " + appName) }
      ]);
    }
  });

})();
async function openWasmTest(){
    const {body}=createWindow("WebAssembly Native Benchmark","⚡",540,360);
    body.innerHTML=`<div style="padding:20px;font-family:sans-serif">
      <h3 style="color:#00c6ff;margin-bottom:8px">Test de Performance WebAssembly (Client)</h3>
      <p style="color:#a0b0c0;font-size:13px;margin-bottom:16px">Exécute un module Wasm binaire directement dans le navigateur en vitesse native.</p>
      <button class="btn" id="run-wasm-btn">Exécuter le calcul natif (Fibonacci)</button>
      <div id="wasm-res" style="margin-top:16px;font-family:monospace;font-size:13px;color:#11ff55;white-space:pre-wrap">Prêt.</div>
    </div>`;
    const btn = body.querySelector("#run-wasm-btn");
    const res = body.querySelector("#wasm-res");

    btn.onclick = async () => {
      res.textContent = "Compilation du module Wasm...";
      try {
        const wasmCode = new Uint8Array([
          0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00, 0x01, 0x06, 0x01, 0x60, 
          0x01, 0x7f, 0x01, 0x7f, 0x03, 0x02, 0x01, 0x00, 0x07, 0x07, 0x01, 0x03, 
          0x66, 0x69, 0x62, 0x00, 0x00, 0x0a, 0x21, 0x01, 0x14, 0x00, 0x20, 0x00, 
          0x41, 0x02, 0x4c, 0x05, 0x01, 0x41, 0x01, 0x0f, 0x0b, 0x20, 0x00, 0x41, 
          0x01, 0x7a, 0x10, 0x00, 0x20, 0x00, 0x41, 0x02, 0x7b, 0x10, 0x00, 0x6a, 
          0x0f, 0x0b
        ]);
        const t0 = performance.now();
        const { instance } = await WebAssembly.instantiate(wasmCode);
        const output = instance.exports.fib(38);
        const t1 = performance.now();
        res.textContent = `Succès !\nCalcul : fib(38) = ${output}\nTemps : ${(t1 - t0).toFixed(2)} ms (Natif Wasm)`;
      } catch (err) {
        res.textContent = "Erreur Wasm : " + err.message;
      }
    };
  }
</script>
</body>
</html>
"""

@app.get("/")
async def serve_frontend():
    return HTMLResponse(content=HTML_INTERFACE)

@app.websocket("/ws")
async def handle_ipc(websocket: WebSocket):
    await websocket.accept()
    session_token = ""
    authenticated_user = ""
    try:
        while True:
            packet = await websocket.receive_json()
            token = packet.get("token", "")
            action = packet.get("action")

            if action == "write_file":
                if not token or token != session_token:
                    await websocket.send_json({"output": "Unauthenticated session."})
                    continue
                path = packet.get("path", "").strip()
                content = packet.get("content", "")
                session = kernel.active_sessions.get(token, {})
                user = session.get("user", "root")
                cwd = session.get("cwd", "/")
                file_path = kernel.vfs.resolve_path(cwd, path)
                msg = kernel.vfs.write_file_content(file_path, content, owner=user)
                await websocket.send_json({"output": msg, "user": authenticated_user, "cwd": cwd})
                continue

            if action == "sudo_auth":
                if not token or token != session_token:
                    await websocket.send_json({"output": "Unauthenticated.", "sudo_ok": False})
                    continue
                password = packet.get("password", "")
                session = kernel.active_sessions.get(token, {})
                user = session.get("user", "")
                cwd = session.get("cwd", "/")
                if user and kernel.auth.authenticate(user, password):
                    elev = kernel.sudo.issue(user=user, target_user="root")
                    await websocket.send_json({
                        "sudo_ok": True,
                        "elev_token": elev["token"],
                        "expires_at": elev["expires_at"],
                        "output": "Elevated to root for 15 minutes.",
                        "user": user,
                        "cwd": cwd,
                    })
                else:
                    await websocket.send_json({
                        "sudo_ok": False,
                        "output": "Sorry, try again.",
                        "user": user,
                        "cwd": cwd,
                    })
                continue

            raw = packet.get("raw_input", "").strip()
            parts = raw.split()
            if not parts:
                continue
            cmd, args = parts[0].lower(), parts[1:]

            if cmd == "login":
                if len(args) < 2:
                    await websocket.send_json({"output": "Usage: login [user] [password]"})
                    continue
                if kernel.auth.authenticate(args[0], args[1]):
                    session_token = secrets.token_hex(16)
                    authenticated_user = args[0]
                    kernel.register_session(session_token, args[0])
                    sess = kernel.active_sessions[session_token]
                    await websocket.send_json({"token": session_token, "output": f"Welcome {args[0]}!", "user": args[0], "cwd": sess["cwd"]})
                else:
                    await websocket.send_json({"output": "Access denied: invalid credentials."})
                continue

            if not token or token != session_token:
                await websocket.send_json({"output": "Unauthenticated session."})
                continue

            if cmd == "matrix":
                async def stream_matrix():
                    for _ in range(20):
                        await websocket.send_json({"output": "".join(str(random.randint(0,1)) for _ in range(56)), "user": authenticated_user, "cwd": kernel.active_sessions.get(token,{}).get("cwd","/")})
                        await asyncio.sleep(0.04)
                await kernel.scheduler.spawn("matrix", stream_matrix(), owner=authenticated_user)
                continue

            if cmd == "apx":
                if not args or args[0] == "list":
                    out = kernel.apx_list()
                elif args[0] == "remove" and len(args) > 1:
                    out = kernel.apx_remove(args[1])
                elif args[0] == "help":
                    out = "apx list | apx remove <id>\nInstall packages via Packages app or POST /api/apx/install"
                else:
                    out = "Usage: apx list | apx remove <app-id>"
                cwd = kernel.active_sessions[token]["cwd"]
                await websocket.send_json({"output": out, "user": authenticated_user, "cwd": cwd})
                continue

            if cmd == "perms" or cmd == "permissions":
                resp = await kernel.syscall(token, "SYS_PERMS_LIST", args)
                await websocket.send_json({"output": resp.get("output",""), "user": authenticated_user, "cwd": resp.get("cwd","/")})
                continue

            if cmd == "help":
                help_text = (
                    "=== ApexOS Hybrid Commands ===\n"
                    "  login whoami pwd date sysinfo\n"
                    "  ls cd cat write touch mkdir rm\n"
                    "  echo ps kill matrix clear\n"
                    "  apx list | apx remove <id>\n"
                    "  perms          — list app permissions\n"
                    "  lsusb          — list USB devices (WebUSB)\n"
                    "  bluetooth scan — BLE device picker\n"
                    "  network        — host network status\n"
                    "  sudo <cmd>     — elevate (15 min token)"
                )
                cwd = kernel.active_sessions[token]["cwd"]
                await websocket.send_json({"output": help_text, "user": authenticated_user, "cwd": cwd})
                continue

            syscall_map = {
                "sysinfo": "SYS_INFO", "ps": "SYS_PROCESS_LIST", "kill": "SYS_PROCESS_KILL",
                "ls": "SYS_FS_LIST", "cd": "SYS_FS_CHANGEDIR", "cat": "SYS_FS_READ",
                "write": "SYS_FS_WRITE", "touch": "SYS_FS_TOUCH", "mkdir": "SYS_FS_MKDIR",
                "rm": "SYS_FS_RM", "whoami": "SYS_WHOAMI", "pwd": "SYS_PWD",
                "echo": "SYS_ECHO", "date": "SYS_DATE",
            }
            if cmd in syscall_map:
                resp = await kernel.syscall(token, syscall_map[cmd], args)
                await websocket.send_json({"output": resp.get("output",""), "user": authenticated_user, "cwd": resp.get("cwd","/")})
            else:
                cwd = kernel.active_sessions[token]["cwd"]
                await websocket.send_json({"output": f"Shell: {cmd}: command not found. Type 'help'.", "user": authenticated_user, "cwd": cwd})
    except WebSocketDisconnect:
        kernel.close_session(session_token)