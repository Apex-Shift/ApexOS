import asyncio
import secrets
import random
import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from src.core.kernel import ApexKernel

app = FastAPI(title="ApexOS")
kernel = ApexKernel()

APPS_DIR = Path(__file__).resolve().parent.parent.parent / "apps"

def discover_apps():
    apps = []
    if not APPS_DIR.exists():
        return apps
    for d in sorted(APPS_DIR.iterdir()):
        if d.is_dir():
            manifest = d / "manifest.json"
            if manifest.exists():
                try:
                    data = json.loads(manifest.read_text(encoding="utf-8"))
                    data["_path"] = str(d)
                    apps.append(data)
                except Exception:
                    pass
    return apps

@app.get("/api/apps")
async def list_apps():
    return JSONResponse(discover_apps())

if APPS_DIR.exists():
    app.mount("/apps", StaticFiles(directory=str(APPS_DIR)), name="apps")

HTML_INTERFACE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ApexOS Desktop</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#0a0e17;color:#e0e6ed;user-select:none}
#desktop{position:absolute;inset:0 0 48px 0;background:linear-gradient(160deg,#0a1628 0%,#0d2137 35%,#0a1929 70%,#071020 100%);background-image:radial-gradient(ellipse 80% 50% at 20% 10%,rgba(0,160,255,.09) 0%,transparent 55%),radial-gradient(ellipse 60% 40% at 85% 75%,rgba(0,220,140,.06) 0%,transparent 50%);overflow:hidden}
.desktop-icon{position:absolute;width:82px;text-align:center;cursor:pointer;padding:10px 4px;border-radius:10px;transition:background .15s,transform .12s}
.desktop-icon:hover{background:rgba(255,255,255,.09);transform:scale(1.04)}
.desktop-icon .icon{font-size:38px;line-height:1.25;filter:drop-shadow(0 3px 6px rgba(0,0,0,.45))}
.desktop-icon .label{font-size:12px;margin-top:5px;text-shadow:0 1px 4px rgba(0,0,0,.85);word-break:break-word}
#taskbar{position:absolute;bottom:0;left:0;right:0;height:48px;background:rgba(8,12,20,.94);backdrop-filter:blur(14px);border-top:1px solid rgba(255,255,255,.07);display:flex;align-items:center;padding:0 10px;gap:6px;z-index:9999}
#start-btn{width:42px;height:36px;border:none;border-radius:9px;background:linear-gradient(135deg,#00c6ff,#0066ff);color:#fff;font-size:17px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:transform .15s,box-shadow .15s}
#start-btn:hover{transform:scale(1.06);box-shadow:0 0 16px rgba(0,140,255,.45)}
.taskbar-apps{display:flex;gap:4px;flex:1;overflow-x:auto}
.taskbar-app{height:36px;padding:0 14px;border-radius:8px;background:rgba(255,255,255,.05);border:1px solid transparent;color:#c8d2de;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:6px;white-space:nowrap;transition:background .15s}
.taskbar-app:hover,.taskbar-app.active{background:rgba(255,255,255,.11);border-color:rgba(0,170,255,.3)}
#clock{font-size:13px;font-variant-numeric:tabular-nums;padding:0 12px;color:#8a9aab}
#start-menu{position:absolute;bottom:56px;left:8px;width:290px;background:rgba(12,18,28,.97);border:1px solid rgba(255,255,255,.09);border-radius:14px;box-shadow:0 14px 48px rgba(0,0,0,.55);padding:12px;display:none;z-index:10000;backdrop-filter:blur(18px)}
#start-menu.open{display:block;animation:menuIn .18s ease}
@keyframes menuIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.start-item{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:9px;cursor:pointer;font-size:14px;transition:background .12s}
.start-item:hover{background:rgba(0,140,255,.14)}
.start-item .si{font-size:20px;width:28px;text-align:center}
.start-sep{height:1px;background:rgba(255,255,255,.07);margin:8px 0}
.window{position:absolute;min-width:300px;min-height:200px;background:#111822;border:1px solid rgba(255,255,255,.09);border-radius:11px;box-shadow:0 18px 52px rgba(0,0,0,.55);display:flex;flex-direction:column;overflow:hidden;z-index:100;animation:winIn .2s ease}
@keyframes winIn{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:none}}
.window.focused{border-color:rgba(0,170,255,.4);box-shadow:0 18px 52px rgba(0,0,0,.6),0 0 0 1px rgba(0,170,255,.12);z-index:200}
.titlebar{height:38px;background:linear-gradient(180deg,#1b2536,#151e2c);display:flex;align-items:center;padding:0 11px;cursor:grab;border-bottom:1px solid rgba(255,255,255,.05)}
.titlebar:active{cursor:grabbing}
.titlebar .title{flex:1;font-size:13px;font-weight:500;color:#c5d0dc;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.titlebar .controls{display:flex;gap:7px}
.win-btn{width:13px;height:13px;border-radius:50%;border:none;cursor:pointer;transition:filter .15s}
.win-btn:hover{filter:brightness(1.25)}
.win-btn.close{background:#ff5f57}.win-btn.min{background:#febc2e}.win-btn.max{background:#28c840}
.window-body{flex:1;overflow:hidden;position:relative;background:#0d1219}
.terminal{height:100%;display:flex;flex-direction:column;font-family:'Cascadia Code','Fira Code',Consolas,monospace;font-size:13.5px;line-height:1.45}
.term-output{flex:1;overflow-y:auto;padding:12px 14px;white-space:pre-wrap;word-break:break-word;color:#11ff55}
.term-output .cmd-line{color:#00bfff}
.term-output .error{color:#ff6b6b}
.term-input-row{display:flex;align-items:center;padding:8px 14px 12px;border-top:1px solid rgba(17,255,85,.12);background:#0a0f14}
.term-prompt{color:#00bfff;font-weight:600;margin-right:8px;white-space:nowrap}
.term-input{flex:1;background:transparent;border:none;outline:none;color:#11ff55;font-family:inherit;font-size:inherit}
.explorer{height:100%;display:flex;flex-direction:column;font-size:13px}
.explorer-toolbar{padding:8px 12px;background:#151e2c;border-bottom:1px solid rgba(255,255,255,.05);display:flex;align-items:center;gap:8px}
.explorer-path{flex:1;background:#0d1219;border:1px solid rgba(255,255,255,.07);border-radius:6px;padding:5px 10px;color:#a0b0c0;font-family:monospace;font-size:12px}
.explorer-toolbar button{background:#1a2435;border:1px solid rgba(255,255,255,.08);color:#c5d0dc;border-radius:6px;padding:5px 10px;cursor:pointer;font-size:12px;transition:background .12s}
.explorer-toolbar button:hover{background:#243044}
.explorer-content{flex:1;overflow-y:auto;padding:12px;display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px;align-content:start}
.file-item{text-align:center;padding:12px 6px;border-radius:9px;cursor:pointer;transition:background .12s}
.file-item:hover{background:rgba(0,140,255,.12)}
.file-item.selected{background:rgba(0,140,255,.2);outline:1px solid rgba(0,170,255,.35)}
.file-item .fi{font-size:30px}
.file-item .fn{margin-top:5px;font-size:12px;word-break:break-word;color:#c5d0dc}
.calc-wrap{height:100%;display:flex;flex-direction:column;padding:14px;gap:12px;background:#0d1219}
.calc-display{background:#0a0f14;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px;font-size:30px;text-align:right;color:#11ff55;font-family:monospace;min-height:60px;overflow:hidden}
.calc-keys{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;flex:1}
.calc-keys button{border:none;border-radius:12px;font-size:19px;font-weight:600;cursor:pointer;color:#fff;transition:filter .12s}
.calc-keys button:hover{filter:brightness(1.15)}
.calc-keys .op{background:#0066ff}.calc-keys .fn{background:#ff5f57}.calc-keys .num{background:#1a2435}.calc-keys .eq{background:#00a86b}.calc-keys .zero{grid-column:span 2}
.editor{height:100%;display:flex;flex-direction:column;background:#0d1219}
.editor-bar{padding:8px 12px;background:#151e2c;border-bottom:1px solid rgba(255,255,255,.05);display:flex;gap:8px;align-items:center}
.editor-bar input{flex:1;background:#0a1018;border:1px solid rgba(255,255,255,.09);border-radius:6px;padding:6px 10px;color:#c5d0dc;font-size:13px;outline:none}
.editor-bar button{border:none;border-radius:6px;padding:6px 14px;cursor:pointer;font-size:13px;font-weight:600}
.editor-bar .save{background:#0066ff;color:#fff}.editor-bar .open{background:#1a2435;color:#c5d0dc;border:1px solid rgba(255,255,255,.08)}
.editor textarea{flex:1;background:#0d1219;border:none;outline:none;color:#e0e6ed;font-family:'Cascadia Code',Consolas,monospace;font-size:14px;line-height:1.55;padding:14px;resize:none}
.editor-status{padding:4px 12px;font-size:11px;color:#5a6a7a;background:#111822;border-top:1px solid rgba(255,255,255,.04)}
.browser{height:100%;display:flex;flex-direction:column;background:#0d1219}
.browser-bar{padding:8px 12px;background:#151e2c;border-bottom:1px solid rgba(255,255,255,.05);display:flex;gap:8px;align-items:center}
.browser-bar input{flex:1;background:#0a1018;border:1px solid rgba(255,255,255,.09);border-radius:6px;padding:7px 12px;color:#c5d0dc;font-size:13px;outline:none}
.browser-bar button{background:#1a2435;border:1px solid rgba(255,255,255,.08);color:#c5d0dc;border-radius:6px;padding:6px 12px;cursor:pointer;font-size:13px}
.browser-bar button:hover{background:#243044}
.browser-bar .go{background:#0066ff;color:#fff;border:none;font-weight:600}
.browser iframe{flex:1;border:none;background:#fff}
#login-overlay{position:fixed;inset:0;background:radial-gradient(ellipse at center,#0c1a2e 0%,#05080f 100%);z-index:20000;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px}
#login-overlay.hidden{display:none}
.login-box{background:rgba(12,18,30,.92);border:1px solid rgba(0,160,255,.22);border-radius:18px;padding:40px 44px;width:370px;box-shadow:0 24px 70px rgba(0,0,0,.55);text-align:center}
.login-box h1{font-size:30px;font-weight:700;margin-bottom:6px;background:linear-gradient(90deg,#00c6ff,#11ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.login-box p{color:#6a7a8a;font-size:13px;margin-bottom:26px}
.login-box input{width:100%;padding:12px 14px;margin-bottom:12px;background:#0a1018;border:1px solid rgba(255,255,255,.09);border-radius:9px;color:#e0e6ed;font-size:14px;outline:none;transition:border-color .2s}
.login-box input:focus{border-color:#00aaff}
.login-box button{width:100%;padding:13px;margin-top:8px;background:linear-gradient(135deg,#00c6ff,#0066ff);border:none;border-radius:9px;color:#fff;font-size:15px;font-weight:600;cursor:pointer;transition:transform .15s,box-shadow .15s}
.login-box button:hover{transform:translateY(-1px);box-shadow:0 8px 24px rgba(0,130,255,.4)}
.login-error{color:#ff6b6b;font-size:13px;min-height:18px;margin-top:8px}
.login-hint{margin-top:18px;font-size:12px;color:#4a5a6a}
</style>
</head>
<body>
<div id="login-overlay">
  <div class="login-box">
    <h1>ApexOS</h1>
    <p>Virtual Operating System</p>
    <input type="text" id="login-user" placeholder="Username" value="root" autocomplete="username">
    <input type="password" id="login-pass" placeholder="Password" value="password" autocomplete="current-password">
    <button id="login-btn">Sign in</button>
    <div class="login-error" id="login-error"></div>
    <div class="login-hint">root / password &nbsp;·&nbsp; guest / guest</div>
  </div>
</div>
<div id="desktop"></div>
<div id="start-menu">
  <div id="start-apps"></div>
  <div class="start-sep"></div>
  <div class="start-item" id="logout-btn"><span class="si">⏻</span> Sign out</div>
</div>
<div id="taskbar">
  <button id="start-btn" title="Start Menu">◆</button>
  <div class="taskbar-apps" id="taskbar-apps"></div>
  <div id="clock"></div>
</div>
<script>
(() => {
  let ws = null;
  let sessionToken = "", currentUser = "", currentCwd = "/";
  let winIdCounter = 1;
  const windows = new Map();
  let wsReady = false;
  let pendingLogin = null;

  const APP_REGISTRY = {
    terminal:   { id:"terminal",   name:"Terminal",     icon:"💻", desktop:true },
    explorer:   { id:"explorer",   name:"Files",        icon:"📁", desktop:true },
    browser:    { id:"browser",    name:"Browser",      icon:"🌐", desktop:true },
    calculator: { id:"calculator", name:"Calculator",   icon:"🧮", desktop:true },
    text_editor:{ id:"text_editor",name:"Text Editor",  icon:"📝", desktop:true },
    sysinfo:    { id:"sysinfo",    name:"System",       icon:"ℹ️", desktop:true },
  };

  const $ = (s,c=document) => c.querySelector(s);
  const $$ = (s,c=document) => [...c.querySelectorAll(s)];

  function updateClock(){
    const n = new Date();
    $("#clock").textContent = n.toLocaleTimeString("en-US",{hour:"2-digit",minute:"2-digit"}) + "  " + n.toLocaleDateString("en-US",{day:"2-digit",month:"short"});
  }
  setInterval(updateClock, 1000); updateClock();

  function connectWS() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/ws`);
    ws.onopen = () => {
      wsReady = true;
      console.log("[ApexOS] WebSocket connected");
      if (pendingLogin) {
        const {user, pass} = pendingLogin;
        pendingLogin = null;
        doLoginSend(user, pass);
      }
    };
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.token) sessionToken = data.token;
        if (data.user) currentUser = data.user;
        if (data.cwd) currentCwd = data.cwd;
        document.dispatchEvent(new CustomEvent("apex-msg", {detail: data}));
      } catch (err) { console.error("[ApexOS] Parse error", err); }
    };
    ws.onclose = () => {
      wsReady = false;
      setTimeout(connectWS, 2000);
    };
    ws.onerror = () => {
      $("#login-error").textContent = "Connection error.";
    };
  }
  connectWS();

  function sendCmd(raw){
    if (!ws || ws.readyState !== WebSocket.OPEN) return false;
    ws.send(JSON.stringify({token: sessionToken, raw_input: raw}));
    return true;
  }
  function sendWrite(path, content){
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({token: sessionToken, action: "write_file", path, content}));
  }

  const loginOverlay = $("#login-overlay");
  function doLoginSend(user, pass) {
    $("#login-error").textContent = "Signing in...";
    const handler = (e) => {
      const d = e.detail;
      if (d.token) {
        loginOverlay.classList.add("hidden");
        document.removeEventListener("apex-msg", handler);
        buildDesktop();
        setTimeout(() => openApp("terminal"), 250);
      } else if (d.output && (d.output.includes("denied") || d.output.includes("invalid") || d.output.includes("Access"))) {
        $("#login-error").textContent = "Invalid credentials.";
        document.removeEventListener("apex-msg", handler);
      }
    };
    document.addEventListener("apex-msg", handler);
    setTimeout(() => {
      document.removeEventListener("apex-msg", handler);
      if (!sessionToken && $("#login-error").textContent === "Signing in...") {
        $("#login-error").textContent = "Timed out. Try again.";
      }
    }, 5000);
    sendCmd(`login ${user} ${pass}`);
  }
  function doLogin(){
    const user = $("#login-user").value.trim();
    const pass = $("#login-pass").value;
    if (!user || !pass) { $("#login-error").textContent = "Fill in both fields."; return; }
    $("#login-error").textContent = "";
    if (!wsReady || !ws || ws.readyState !== WebSocket.OPEN) {
      $("#login-error").textContent = "Connecting to server...";
      pendingLogin = {user, pass};
      if (!ws || ws.readyState === WebSocket.CLOSED) connectWS();
      return;
    }
    doLoginSend(user, pass);
  }
  $("#login-btn").onclick = doLogin;
  $("#login-pass").onkeydown = e => { if (e.key === "Enter") doLogin(); };
  $("#login-user").onkeydown = e => { if (e.key === "Enter") $("#login-pass").focus(); };

  const startMenu = $("#start-menu");
  $("#start-btn").onclick = e => { e.stopPropagation(); startMenu.classList.toggle("open"); };
  document.addEventListener("click", () => startMenu.classList.remove("open"));
  startMenu.onclick = e => e.stopPropagation();
  $("#logout-btn").onclick = () => location.reload();

  function buildDesktop(){
    const desk = $("#desktop");
    desk.innerHTML = "";
    const startApps = $("#start-apps");
    startApps.innerHTML = "";
    let i = 0;
    Object.values(APP_REGISTRY).filter(a => a.desktop).forEach(app => {
      const ic = document.createElement("div");
      ic.className = "desktop-icon";
      ic.style.top = (24 + i * 100) + "px";
      ic.style.left = "22px";
      ic.innerHTML = `<div class="icon">${app.icon}</div><div class="label">${app.name}</div>`;
      ic.ondblclick = () => openApp(app.id);
      desk.appendChild(ic);
      const si = document.createElement("div");
      si.className = "start-item";
      si.innerHTML = `<span class="si">${app.icon}</span> ${app.name}`;
      si.onclick = () => { openApp(app.id); startMenu.classList.remove("open"); };
      startApps.appendChild(si);
      i++;
    });
  }

  function bringToFront(win){
    $$(".window").forEach(w => w.classList.remove("focused"));
    win.classList.add("focused");
    $$(".taskbar-app").forEach(t => t.classList.remove("active"));
    const tb = $(`.taskbar-app[data-id="${win.dataset.id}"]`);
    if (tb) tb.classList.add("active");
  }
  function makeDraggable(win){
    const bar = $(".titlebar", win);
    let ox, oy, drag = false;
    bar.onmousedown = e => {
      if (e.target.classList.contains("win-btn")) return;
      drag = true; ox = e.clientX - win.offsetLeft; oy = e.clientY - win.offsetTop;
      bringToFront(win);
    };
    document.addEventListener("mousemove", e => {
      if (!drag) return;
      win.style.left = Math.max(0, e.clientX - ox) + "px";
      win.style.top = Math.max(0, e.clientY - oy) + "px";
    });
    document.addEventListener("mouseup", () => drag = false);
  }
  function createWindow(title, icon, width=640, height=420){
    const id = "w" + (winIdCounter++);
    const win = document.createElement("div");
    win.className = "window focused";
    win.dataset.id = id;
    win.style.width = width + "px";
    win.style.height = height + "px";
    win.style.left = (50 + (winIdCounter % 7) * 32) + "px";
    win.style.top = (36 + (winIdCounter % 5) * 30) + "px";
    win.innerHTML = `
      <div class="titlebar">
        <span class="title">${icon} ${title}</span>
        <div class="controls">
          <button class="win-btn min" title="Minimize"></button>
          <button class="win-btn max" title="Maximize"></button>
          <button class="win-btn close" title="Close"></button>
        </div>
      </div>
      <div class="window-body"></div>`;
    $("#desktop").appendChild(win);
    makeDraggable(win);
    win.onmousedown = () => bringToFront(win);
    const tb = document.createElement("div");
    tb.className = "taskbar-app active";
    tb.dataset.id = id;
    tb.innerHTML = `${icon} ${title.split("—")[0].trim()}`;
    tb.onclick = () => {
      if (win.style.display === "none") win.style.display = "flex";
      bringToFront(win);
    };
    $("#taskbar-apps").appendChild(tb);
    $(".win-btn.close", win).onclick = () => { win.remove(); tb.remove(); windows.delete(id); };
    $(".win-btn.min", win).onclick = () => { win.style.display = "none"; tb.classList.remove("active"); };
    let maximized = false, prev;
    $(".win-btn.max", win).onclick = () => {
      if (!maximized) {
        prev = {l:win.style.left, t:win.style.top, w:win.style.width, h:win.style.height};
        win.style.left="0"; win.style.top="0"; win.style.width="100%"; win.style.height="calc(100% - 48px)";
        maximized = true;
      } else {
        Object.assign(win.style, {left:prev.l, top:prev.t, width:prev.w, height:prev.h});
        maximized = false;
      }
    };
    bringToFront(win);
    windows.set(id, win);
    return {win, body: $(".window-body", win), id};
  }

  function openApp(name, options={}){
    if (name === "terminal") openTerminal();
    else if (name === "explorer") openExplorer();
    else if (name === "browser") openBrowser();
    else if (name === "calculator") openCalculator();
    else if (name === "text_editor") openTextEditor(options);
    else if (name === "sysinfo") openSysInfo();
  }

  function openTerminal(){
    const {win, body} = createWindow("Terminal", "💻", 700, 450);
    body.innerHTML = `
      <div class="terminal">
        <div class="term-output"></div>
        <div class="term-input-row">
          <span class="term-prompt">${currentUser||"user"}@apexos:${currentCwd}#</span>
          <input class="term-input" type="text" spellcheck="false" autocomplete="off">
        </div>
      </div>`;
    const output = $(".term-output", body), input = $(".term-input", body), prompt = $(".term-prompt", body);
    const history = []; let histIdx = -1;
    output.innerHTML = `<span style="color:#6a7a8a">ApexOS Terminal — type 'help' for available commands.</span>\n\n`;
    function append(text, cls=""){
      const s = document.createElement("span");
      if (cls) s.className = cls;
      s.textContent = text + "\n";
      output.appendChild(s);
      output.scrollTop = output.scrollHeight;
    }
    const msgHandler = e => {
      const d = e.detail;
      if (d.output !== undefined) append(d.output, /Error|not found|denied|Unable|cannot/i.test(d.output) ? "error" : "");
      if (d.user && d.cwd) prompt.textContent = `${d.user}@apexos:${d.cwd}#`;
    };
    document.addEventListener("apex-msg", msgHandler);
    const origClose = $(".win-btn.close", win).onclick;
    $(".win-btn.close", win).onclick = () => { document.removeEventListener("apex-msg", msgHandler); origClose(); };
    input.onkeydown = e => {
      if (e.key === "Enter") {
        const cmd = input.value.trim();
        if (!cmd) return;
        append(`${prompt.textContent} ${cmd}`, "cmd-line");
        history.push(cmd); histIdx = history.length;
        if (cmd.toLowerCase() === "clear") output.innerHTML = "";
        else sendCmd(cmd);
        input.value = "";
      } else if (e.key === "ArrowUp") {
        if (histIdx > 0) { histIdx--; input.value = history[histIdx]; }
        e.preventDefault();
      } else if (e.key === "ArrowDown") {
        if (histIdx < history.length - 1) { histIdx++; input.value = history[histIdx]; }
        else { histIdx = history.length; input.value = ""; }
        e.preventDefault();
      }
    };
    setTimeout(() => input.focus(), 40);
    win.onclick = () => input.focus();
  }

  function openExplorer(){
    const {win, body} = createWindow("Files", "📁", 580, 420);
    body.innerHTML = `
      <div class="explorer">
        <div class="explorer-toolbar">
          <button data-act="up" title="Up">⬆</button>
          <button data-act="refresh" title="Refresh">↻</button>
          <div class="explorer-path">/</div>
          <button data-act="newfolder">+ Folder</button>
          <button data-act="newfile">+ File</button>
          <button data-act="delete">🗑</button>
        </div>
        <div class="explorer-content"></div>
      </div>`;
    const pathEl = $(".explorer-path", body), content = $(".explorer-content", body);
    let expCwd = currentCwd || "/", selected = null;

    function refresh(){
      pathEl.textContent = expCwd;
      content.innerHTML = `<div style="grid-column:1/-1;color:#6a7a8a;padding:24px">Loading...</div>`;
      selected = null;
      const handler = e => {
        const d = e.detail;
        if (d.output !== undefined) {
          document.removeEventListener("apex-msg", handler);
          content.innerHTML = "";
          const raw = (d.output || "").trim();
          if (!raw || raw === "(empty directory)") {
            content.innerHTML = `<div style="grid-column:1/-1;color:#6a7a8a;padding:24px">Empty directory</div>`;
            return;
          }
          if (raw.startsWith("ls:")) {
            content.innerHTML = `<div style="grid-column:1/-1;color:#ff6b6b;padding:24px">${raw}</div>`;
            return;
          }
          raw.split(/\s+/).filter(Boolean).forEach(item => {
            const isDir = item.startsWith("[") && item.endsWith("/]");
            const name = isDir ? item.slice(1, -2) : item;
            const div = document.createElement("div");
            div.className = "file-item";
            div.dataset.name = name;
            div.dataset.dir = isDir ? "1" : "0";
            div.innerHTML = `<div class="fi">${isDir ? "📁" : "📄"}</div><div class="fn">${name}</div>`;
            div.onclick = e => {
              e.stopPropagation();
              $$(".file-item", content).forEach(x => x.classList.remove("selected"));
              div.classList.add("selected");
              selected = {name, isDir};
            };
            div.ondblclick = () => {
              if (isDir) {
                expCwd = expCwd === "/" ? "/" + name : expCwd + "/" + name;
                sendCmd("cd " + expCwd);
                setTimeout(refresh, 100);
              } else {
                openTextEditor({filename: (expCwd === "/" ? "/" : expCwd + "/") + name});
              }
            };
            content.appendChild(div);
          });
        }
      };
      document.addEventListener("apex-msg", handler);
      sendCmd("cd " + expCwd);
      setTimeout(() => sendCmd("ls"), 70);
    }
    body.querySelector('[data-act="up"]').onclick = () => {
      if (expCwd === "/") return;
      const p = expCwd.split("/").filter(Boolean); p.pop();
      expCwd = "/" + p.join("/");
      sendCmd("cd " + expCwd);
      setTimeout(refresh, 90);
    };
    body.querySelector('[data-act="refresh"]').onclick = refresh;
    body.querySelector('[data-act="newfolder"]').onclick = () => {
      const name = prompt("Folder name:");
      if (!name) return;
      sendCmd("mkdir " + name);
      setTimeout(refresh, 120);
    };
    body.querySelector('[data-act="newfile"]').onclick = () => {
      const name = prompt("File name:");
      if (!name) return;
      sendCmd("touch " + name);
      setTimeout(refresh, 120);
    };
    body.querySelector('[data-act="delete"]').onclick = () => {
      if (!selected) { alert("Select a file or folder first."); return; }
      if (!confirm("Delete \"" + selected.name + "\"?")) return;
      sendCmd("rm " + selected.name);
      setTimeout(refresh, 120);
    };
    refresh();
  }

  function openBrowser(){
    const {win, body} = createWindow("Browser", "🌐", 800, 520);
    body.innerHTML = `
      <div class="browser">
        <div class="browser-bar">
          <button data-act="back" title="Back">←</button>
          <button data-act="fwd" title="Forward">→</button>
          <button data-act="reload" title="Reload">↻</button>
          <input id="url-bar" type="text" value="https://example.com" placeholder="Enter URL...">
          <button class="go" data-act="go">Go</button>
        </div>
        <iframe id="browser-frame" sandbox="allow-scripts allow-same-origin allow-forms allow-popups" src="https://example.com"></iframe>
      </div>`;
    const frame = $("#browser-frame", body);
    const urlBar = $("#url-bar", body);
    function navigate(){
      let url = urlBar.value.trim();
      if (!url) return;
      if (!/^https?:\/\//i.test(url)) url = "https://" + url;
      urlBar.value = url;
      frame.src = url;
    }
    body.querySelector('[data-act="go"]').onclick = navigate;
    urlBar.onkeydown = e => { if (e.key === "Enter") navigate(); };
    body.querySelector('[data-act="reload"]').onclick = () => { frame.src = frame.src; };
    body.querySelector('[data-act="back"]').onclick = () => { try { frame.contentWindow.history.back(); } catch(_){} };
    body.querySelector('[data-act="fwd"]').onclick = () => { try { frame.contentWindow.history.forward(); } catch(_){} };
  }

  function openCalculator(){
    const {win, body} = createWindow("Calculator", "🧮", 300, 440);
    body.innerHTML = `
      <div class="calc-wrap">
        <div class="calc-display" id="calc-display">0</div>
        <div class="calc-keys">
          <button class="fn" data-k="C">C</button><button class="fn" data-k="±">±</button>
          <button class="fn" data-k="%">%</button><button class="op" data-k="÷">÷</button>
          <button class="num" data-k="7">7</button><button class="num" data-k="8">8</button>
          <button class="num" data-k="9">9</button><button class="op" data-k="×">×</button>
          <button class="num" data-k="4">4</button><button class="num" data-k="5">5</button>
          <button class="num" data-k="6">6</button><button class="op" data-k="-">−</button>
          <button class="num" data-k="1">1</button><button class="num" data-k="2">2</button>
          <button class="num" data-k="3">3</button><button class="op" data-k="+">+</button>
          <button class="num zero" data-k="0">0</button><button class="num" data-k=".">.</button>
          <button class="eq" data-k="=">=</button>
        </div>
      </div>`;
    let cur="0", op=null, prev=null, reset=false;
    const disp = $("#calc-display", body);
    const upd = () => disp.textContent = cur;
    body.querySelectorAll("button").forEach(btn => {
      btn.onclick = () => {
        const k = btn.dataset.k;
        if ((k>="0"&&k<="9")||k===".") {
          if (reset) { cur="0"; reset=false; }
          if (k==="." && cur.includes(".")) return;
          cur = (cur==="0"&&k!==".") ? k : cur+k;
        } else if (k==="C") { cur="0"; op=prev=null; }
        else if (k==="±") { cur=String(parseFloat(cur)*-1); }
        else if (k==="%") { cur=String(parseFloat(cur)/100); }
        else if (["+","-","×","÷"].includes(k)) { prev=parseFloat(cur); op=k; reset=true; }
        else if (k==="=") {
          if (op && prev !== null) {
            const a=prev, b=parseFloat(cur);
            let r=0;
            if (op==="+") r=a+b; if (op==="-") r=a-b;
            if (op==="×") r=a*b; if (op==="÷") r=b!==0?a/b:"Err";
            cur=String(r); op=prev=null; reset=true;
          }
        }
        upd();
      };
    });
  }

  function openTextEditor(options={}){
    const filename = options.filename || "untitled.txt";
    const {win, body} = createWindow("Editor — " + filename, "📝", 680, 500);
    body.innerHTML = `
      <div class="editor">
        <div class="editor-bar">
          <input id="ed-path" value="${filename}">
          <button class="save" id="ed-save">Save</button>
          <button class="open" id="ed-open">Open</button>
        </div>
        <textarea id="ed-content" spellcheck="false" placeholder="Start typing..."></textarea>
        <div class="editor-status" id="ed-status">Ready</div>
      </div>`;
    const content = $("#ed-content", body), pathInput = $("#ed-path", body), status = $("#ed-status", body);
    if (options.filename && options.filename !== "untitled.txt") {
      status.textContent = "Loading...";
      const handler = e => {
        if (e.detail.output !== undefined) {
          const out = e.detail.output;
          content.value = out.startsWith("cat:") ? "" : out;
          status.textContent = content.value ? "Loaded" : "New / empty";
          document.removeEventListener("apex-msg", handler);
        }
      };
      document.addEventListener("apex-msg", handler);
      sendCmd("cat " + options.filename);
    }
    $("#ed-save", body).onclick = () => {
      const path = pathInput.value.trim() || "untitled.txt";
      status.textContent = "Saving...";
      sendWrite(path, content.value);
      status.textContent = "Saved · " + path;
      const t = win.querySelector(".title");
      if (t) t.textContent = "📝 Editor — " + path;
    };
    $("#ed-open", body).onclick = () => {
      const path = pathInput.value.trim();
      if (!path) return;
      status.textContent = "Opening...";
      const handler = e => {
        if (e.detail.output !== undefined) {
          content.value = e.detail.output.startsWith("cat:") ? "" : e.detail.output;
          status.textContent = "Opened · " + path;
          document.removeEventListener("apex-msg", handler);
        }
      };
      document.addEventListener("apex-msg", handler);
      sendCmd("cat " + path);
    };
  }

  function openSysInfo(){
    const {win, body} = createWindow("System", "ℹ️", 440, 300);
    body.innerHTML = `<div style="padding:22px;font-family:monospace;font-size:13px;color:#11ff55;white-space:pre-wrap;line-height:1.6">Loading...</div>`;
    const out = $("div", body);
    const handler = e => {
      if (e.detail.output && e.detail.output.includes("OS")) {
        out.textContent = e.detail.output;
        document.removeEventListener("apex-msg", handler);
      }
    };
    document.addEventListener("apex-msg", handler);
    sendCmd("sysinfo");
  }
})();
</script>
</body>
</html>
"""

@app.get("/")
async def serve_frontend():
    return HTMLResponse(content=HTML_INTERFACE)

@app.websocket("/ws")
async def handle_ipc_stream(websocket: WebSocket):
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
                if not path:
                    await websocket.send_json({"output": "Missing path."})
                    continue
                session = kernel.active_sessions.get(token, {})
                user = session.get("user", "root")
                cwd = session.get("cwd", "/")
                file_path = kernel.vfs.resolve_path(cwd, path)
                msg = kernel.vfs.write_file_content(file_path, content, owner=user)
                await websocket.send_json({"output": msg, "user": authenticated_user, "cwd": cwd})
                continue

            raw_input = packet.get("raw_input", "").strip()
            parts = raw_input.split()
            if not parts:
                continue

            cmd = parts[0].lower()
            args = parts[1:]

            if cmd == "login":
                if len(args) < 2:
                    await websocket.send_json({"output": "Usage: login [user] [password]"})
                    continue
                username, password = args[0], args[1]
                if kernel.auth.authenticate(username, password):
                    session_token = secrets.token_hex(16)
                    authenticated_user = username
                    kernel.register_session(session_token, username)
                    sess = kernel.active_sessions[session_token]
                    await websocket.send_json({
                        "token": session_token,
                        "output": f"Welcome {username}!",
                        "user": username,
                        "cwd": sess["cwd"]
                    })
                else:
                    await websocket.send_json({"output": "Access denied: invalid credentials."})
                continue

            if not token or token != session_token:
                await websocket.send_json({"output": "Unauthenticated session."})
                continue

            if cmd == "matrix":
                async def stream_matrix():
                    for _ in range(25):
                        payload = "".join(str(random.randint(0, 1)) for _ in range(64))
                        cwd = kernel.active_sessions.get(token, {}).get("cwd", "/")
                        await websocket.send_json({"output": payload, "user": authenticated_user, "cwd": cwd})
                        await asyncio.sleep(0.04)
                await kernel.scheduler.spawn("matrix_daemon", stream_matrix(), owner=authenticated_user)
                continue

            syscall_map = {
                "help": "help", "sysinfo": "SYS_INFO", "ps": "SYS_PROCESS_LIST",
                "kill": "SYS_PROCESS_KILL", "ls": "SYS_FS_LIST", "cd": "SYS_FS_CHANGEDIR",
                "cat": "SYS_FS_READ", "write": "SYS_FS_WRITE", "touch": "SYS_FS_TOUCH",
                "mkdir": "SYS_FS_MKDIR", "rm": "SYS_FS_RM", "whoami": "SYS_WHOAMI",
                "pwd": "SYS_PWD", "echo": "SYS_ECHO", "date": "SYS_DATE",
            }

            if cmd == "help":
                help_text = (
                    "=== ApexOS Commands ===\n"
                    "  login  whoami  pwd  date  sysinfo\n"
                    "  ls  cd [dir]  cat [file]  write [file] [text]\n"
                    "  touch [file]  mkdir [dir]  rm [file|dir]\n"
                    "  echo [text]  ps  kill [PID]  matrix  clear"
                )
                cwd = kernel.active_sessions[token]["cwd"]
                await websocket.send_json({"output": help_text, "user": authenticated_user, "cwd": cwd})
                continue

            if cmd in syscall_map:
                kernel_resp = await kernel.syscall(token, syscall_map[cmd], args)
                await websocket.send_json({
                    "output": kernel_resp.get("output", ""),
                    "user": authenticated_user,
                    "cwd": kernel_resp.get("cwd", "/")
                })
            else:
                cwd = kernel.active_sessions[token]["cwd"]
                await websocket.send_json({
                    "output": f"Shell: {cmd}: command not found. Type 'help'.",
                    "user": authenticated_user,
                    "cwd": cwd
                })

    except WebSocketDisconnect:
        kernel.close_session(session_token)
