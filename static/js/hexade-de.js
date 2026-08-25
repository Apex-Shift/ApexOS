/** HexaDE — swappable desktop environment for ApexOS */
(() => {
  const H = window.ApexHost;
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];

  const APPS = {
    terminal: { id: "terminal", name: "Terminal", icon: "💻", desktop: true },
    explorer: { id: "explorer", name: "Files", icon: "📁", desktop: true },
    settings: { id: "settings", name: "Settings", icon: "⚙️", desktop: true },
    packages: { id: "packages", name: "Packages", icon: "📦", desktop: true },
    calculator: { id: "calculator", name: "Calculator", icon: "🧮", desktop: true },
    text_editor: { id: "text_editor", name: "Editor", icon: "📝", desktop: true },
    browser: { id: "browser", name: "Browser", icon: "🌐", desktop: true },
    sysinfo: { id: "sysinfo", name: "System", icon: "ℹ️", desktop: true },
    media: { id: "media", name: "Media", icon: "🎬", desktop: true },
    taskman: { id: "taskman", name: "Tasks", icon: "📊", desktop: true },
    wasmtest: { id: "wasmtest", name: "Wasm Test", icon: "⚡", desktop: true },
  };

  let winId = 1;
  let currentUser = H.getUser();
  let currentCwd = H.getCwd();

  function updateClock() {
    const n = new Date();
    const el = $("#deskbar-clock");
    if (el) {
      el.textContent =
        n.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" }) +
        "  " +
        n.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    }
    const ct = $("#cal-title");
    if (ct) {
      ct.textContent = n.toLocaleDateString("en-US", {
        weekday: "long", year: "numeric", month: "long", day: "numeric",
      });
    }
  }
  setInterval(updateClock, 1000);
  updateClock();

  function closePopups() {
    $("#start-menu")?.classList.remove("open");
    $("#cal-pop")?.classList.remove("open");
  }

  function buildDesktop() {
    const desk = $("#desktop");
    desk.innerHTML = "";
    const sm = $("#start-apps");
    sm.innerHTML = "";
    let i = 0;
    Object.values(APPS).filter((a) => a.desktop).forEach((app) => {
      const ic = document.createElement("div");
      ic.className = "desktop-icon";
      ic.style.top = 20 + i * 96 + "px";
      ic.style.left = "18px";
      ic.innerHTML = `<div class="icon">${app.icon}</div><div class="label">${app.name}</div>`;
      ic.ondblclick = () => openApp(app.id);
      desk.appendChild(ic);
      const si = document.createElement("div");
      si.className = "start-item";
      si.innerHTML = `<span style="width:28px;text-align:center">${app.icon}</span> ${app.name}`;
      si.onclick = () => { openApp(app.id); closePopups(); };
      sm.appendChild(si);
      i++;
    });
  }

  function createWindow(title, icon, w = 640, h = 420) {
    const id = "w" + winId++;
    const win = document.createElement("div");
    win.className = "window focused";
    win.dataset.id = id;
    win.style.cssText = `width:${w}px;height:${h}px;left:${40 + (winId % 6) * 28}px;top:${30 + (winId % 4) * 24}px`;
    win.innerHTML = `<div class="titlebar"><span class="title">${icon} ${title}</span>
      <button class="win-btn min"></button><button class="win-btn max"></button><button class="win-btn close"></button></div>
      <div class="window-body"></div>`;
    $("#desktop").appendChild(win);
    const bar = $(".titlebar", win);
    let ox, oy, drag = false;
    bar.onmousedown = (e) => {
      if (e.target.classList.contains("win-btn")) return;
      drag = true; ox = e.clientX - win.offsetLeft; oy = e.clientY - win.offsetTop;
      $$(".window").forEach((w) => w.classList.remove("focused"));
      win.classList.add("focused");
    };
    document.addEventListener("mousemove", (e) => {
      if (!drag) return;
      win.style.left = Math.max(0, e.clientX - ox) + "px";
      win.style.top = Math.max(0, e.clientY - oy) + "px";
    });
    document.addEventListener("mouseup", () => { drag = false; });
    win.onmousedown = () => {
      $$(".window").forEach((w) => w.classList.remove("focused"));
      win.classList.add("focused");
      $$(".deskbar-win").forEach((x) => x.classList.toggle("active", x.dataset.id === id));
    };
    const tb = document.createElement("div");
    tb.className = "deskbar-win active";
    tb.dataset.id = id;
    tb.innerHTML = `${icon} ${title.split("—")[0].trim()}`;
    tb.onclick = () => {
      win.style.display = "flex";
      $$(".window").forEach((w) => w.classList.remove("focused"));
      win.classList.add("focused");
      $$(".deskbar-win").forEach((x) => x.classList.remove("active"));
      tb.classList.add("active");
    };
    $("#deskbar-wins")?.appendChild(tb);
    $(".win-btn.close", win).onclick = () => { win.remove(); tb.remove(); };
    $(".win-btn.min", win).onclick = () => { win.style.display = "none"; };
    let mx = false, prev;
    $(".win-btn.max", win).onclick = () => {
      if (!mx) {
        prev = { l: win.style.left, t: win.style.top, w: win.style.width, h: win.style.height };
        win.style.left = "0"; win.style.top = "36px";
        win.style.width = "100%"; win.style.height = "calc(100% - 36px)";
        mx = true;
      } else {
        Object.assign(win.style, { left: prev.l, top: prev.t, width: prev.w, height: prev.h });
        mx = false;
      }
    };
    return { win, body: $(".window-body", win), id };
  }

  function openApp(name, opts = {}) {
    if (name === "terminal") openTerminal();
    else if (name === "explorer") openExplorer();
    else if (name === "settings") openSettings();
    else if (name === "packages") openPackages();
    else if (name === "calculator") openCalculator();
    else if (name === "text_editor") openEditor(opts);
    else if (name === "browser") openBrowser();
    else if (name === "sysinfo") openSysInfo();
    else if (name === "media") openMedia();
    else if (name === "taskman") openTaskManager();
    else if (name === "wasmtest") openWasmTest();
  }

  function openTerminal() {
    const { win, body } = createWindow("Terminal", "💻", 700, 440);
    body.innerHTML = `<div class="terminal"><div class="term-output"></div>
      <div class="term-input-row"><span class="term-prompt">${currentUser || "user"}@apexos:${currentCwd}#</span>
      <input class="term-input" spellcheck="false" autocomplete="off"></div></div>`;
    const out = $(".term-output", body), input = $(".term-input", body), prompt = $(".term-prompt", body);
    const hist = []; let hi = -1;
    out.innerHTML = `<span style="color:#6a7a8a">ApexOS Hybrid — type 'help'. Try: sudo, apx, network</span>\n\n`;
    const append = (t, c = "") => {
      const s = document.createElement("span");
      if (c) s.className = c;
      s.textContent = t + "\n";
      out.appendChild(s);
      out.scrollTop = out.scrollHeight;
    };
    const off = H.onMessage((d) => {
      if (d.output !== undefined) append(d.output, /Error|not found|denied|Unable|cannot|Sorry/i.test(d.output || "") ? "error" : "");
      if (d.user && d.cwd) { currentUser = d.user; currentCwd = d.cwd; prompt.textContent = `${d.user}@apexos:${d.cwd}#`; }
    });
    const oc = $(".win-btn.close", win).onclick;
    $(".win-btn.close", win).onclick = () => { off(); if (oc) oc(); };
    input.onkeydown = (e) => {
      if (e.key !== "Enter") {
        if (e.key === "ArrowUp") { if (hi > 0) { hi--; input.value = hist[hi]; } e.preventDefault(); }
        else if (e.key === "ArrowDown") { if (hi < hist.length - 1) { hi++; input.value = hist[hi]; } else { hi = hist.length; input.value = ""; } e.preventDefault(); }
        return;
      }
      if (input.dataset.sudoPending !== undefined) {
        const pending = input.dataset.sudoPending;
        const password = input.value;
        delete input.dataset.sudoPending;
        input.type = "text"; input.value = "";
        const unsub = H.onMessage((d) => {
          if (d.sudo_ok === true) {
            win._elevToken = d.elev_token;
            $(".titlebar", win).classList.add("root-privilege");
            win.classList.add("root-frame");
            append(d.output || "Elevated.");
            const ttl = Math.max(5, (d.expires_at || 0) - Math.floor(Date.now() / 1000));
            if (win._elevTimer) clearTimeout(win._elevTimer);
            win._elevTimer = setTimeout(() => {
              win._elevToken = null;
              $(".titlebar", win).classList.remove("root-privilege");
              win.classList.remove("root-frame");
              append("sudo: elevation expired.");
            }, ttl * 1000);
            H.send({ token: H.getToken(), elev_token: win._elevToken, raw_input: pending });
            unsub();
          } else if (d.sudo_ok === false) {
            append(d.output || "Sorry, try again.", "error");
            unsub();
          }
        });
        H.sudoAuth(password);
        return;
      }
      const cmd = input.value.trim();
      if (!cmd) return;
      append(`${prompt.textContent} ${cmd}`, "cmd-line");
      hist.push(cmd); hi = hist.length;
      if (cmd.toLowerCase() === "clear") out.innerHTML = "";
      else if (cmd.toLowerCase().startsWith("sudo ")) {
        const real = cmd.slice(5).trim();
        if (!real) { append("usage: sudo <command>", "error"); input.value = ""; return; }
        if (win._elevToken) {
          H.send({ token: H.getToken(), elev_token: win._elevToken, raw_input: real });
          input.value = ""; return;
        }
        append("[sudo] password for " + (currentUser || "user") + ": ");
        input.type = "password"; input.dataset.sudoPending = real; input.value = ""; return;
      } else if (cmd.toLowerCase() === "lsusb") {
        if (!navigator.usb) append("lsusb: WebUSB not supported.", "error");
        else navigator.usb.getDevices().then((ds) => {
          if (!ds.length) append("No authorized USB devices.");
          else ds.forEach((d, i) => append(`Bus 000 Device ${String(i).padStart(3, "0")}: ID ${d.vendorId.toString(16)}:${d.productId.toString(16)} ${d.productName || ""}`));
        });
      } else if (cmd.toLowerCase().startsWith("bluetooth")) {
        if (!navigator.bluetooth) append("bluetooth: not supported.", "error");
        else navigator.bluetooth.requestDevice({ acceptAllDevices: true, optionalServices: [] })
          .then((d) => append(`Found: ${d.name || "(unnamed)"}`))
          .catch((e) => append("bluetooth: " + e.message, "error"));
      } else if (cmd.toLowerCase() === "network" || cmd.toLowerCase() === "netstat") {
        const c = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        append("Online: " + (navigator.onLine ? "yes" : "no"));
        if (c) {
          append("Type: " + (c.effectiveType || c.type || "unknown"));
          if (c.downlink != null) append("Downlink: " + c.downlink + " Mbps");
        }
      } else H.sendCmd(cmd);
      input.value = "";
    };
    setTimeout(() => input.focus(), 40);
    win.onclick = () => input.focus();
  }

  function openTaskManager() {
    const { win, body } = createWindow("Task Manager", "📊", 520, 380);
    body.innerHTML = `<div style="height:100%;display:flex;flex-direction:column;background:#1a1b1e">
      <div class="xfce-menu-bar">
        <span class="xfce-menu-item" id="tm-refresh">🔄 Refresh</span>
        <span class="xfce-menu-item" id="tm-sudo">⚡ Sudo mode</span>
      </div>
      <div class="taskman-alert" id="tm-alert">Guest mode — elevate to kill root processes.</div>
      <div style="flex:1;overflow:auto"><table id="taskman-table">
        <thead><tr><th>PID</th><th>Name</th><th>User</th><th>CPU %</th><th>RAM</th></tr></thead>
        <tbody id="tm-body"></tbody></table></div>
      <div style="height:32px;border-top:1px solid #2a2d32;display:flex;justify-content:space-between;align-items:center;padding:0 10px">
        <span id="tm-stats" style="font-size:11px;color:#8a8d98">Total: 0</span>
        <button class="btn danger" id="tm-kill" disabled style="padding:2px 10px;font-size:11px">End task</button>
      </div></div>`;
    let selected = null, elev = null;
    const titlebar = $(".titlebar", win);
    async function refresh() {
      try {
        const rows = await (await fetch("/api/v1/sys/telemetry")).json();
        const tb = $("#tm-body", body); tb.innerHTML = "";
        rows.forEach((p) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>${p.pid}</td><td>${p.name}</td><td>${p.user}</td><td>${p.cpu_usage}</td><td>${p.mem_usage}</td>`;
          tr.onclick = () => {
            tb.querySelectorAll("tr").forEach((x) => x.classList.remove("selected", "selected-root"));
            tr.classList.add(p.user === "root" ? "selected-root" : "selected");
            selected = p; $("#tm-kill", body).disabled = false;
          };
          tb.appendChild(tr);
        });
        $("#tm-stats", body).textContent = "Total: " + rows.length + " processes";
      } catch (_) { $("#tm-stats", body).textContent = "Telemetry error"; }
    }
    $("#tm-refresh", body).onclick = refresh;
    $("#tm-sudo", body).onclick = () => {
      const pw = prompt("[sudo] password for " + currentUser + ":");
      if (pw == null) return;
      const unsub = H.onMessage((d) => {
        if (d.sudo_ok) {
          elev = d.elev_token;
          titlebar.classList.add("root-privilege");
          win.classList.add("root-frame");
          $("#tm-alert", body).style.display = "none";
        } else if (d.sudo_ok === false) alert(d.output || "Sorry, try again.");
        unsub();
      });
      H.sudoAuth(pw);
    };
    $("#tm-kill", body).onclick = () => {
      if (!selected) return;
      if (selected.user === "root" && !elev && currentUser !== "root") {
        alert("Permission denied: use Sudo mode.");
        return;
      }
      const payload = { token: H.getToken(), raw_input: "kill " + selected.pid };
      if (elev) payload.elev_token = elev;
      H.send(payload);
      setTimeout(refresh, 300);
    };
    refresh();
    const iv = setInterval(refresh, 1000);
    const oc = $(".win-btn.close", win).onclick;
    $(".win-btn.close", win).onclick = () => { clearInterval(iv); if (oc) oc(); };
  }

  function openWasmTest() {
    const { body } = createWindow("WebAssembly Test", "⚡", 540, 360);
    body.innerHTML = `<div style="padding:20px;font-family:sans-serif">
      <h3 style="color:#00c6ff;margin-bottom:8px">WebAssembly client benchmark</h3>
      <p style="color:#a0b0c0;font-size:13px;margin-bottom:16px">Valid minimal Wasm module + JS fib comparison.</p>
      <button class="btn" id="run-wasm-btn">Run</button>
      <div id="wasm-res" style="margin-top:16px;font-family:monospace;font-size:13px;color:#11ff55;white-space:pre-wrap">Ready.</div>
    </div>`;
    $("#run-wasm-btn", body).onclick = async () => {
      const res = $("#wasm-res", body);
      res.textContent = "Running…";
      try {
        // Minimal valid module: (module (func (export "addOne") (param i32) (result i32) local.get 0 i32.const 1 i32.add))
        const bytes = new Uint8Array([
          0x00,0x61,0x73,0x6d,0x01,0x00,0x00,0x00,0x01,0x07,0x01,0x60,0x01,0x7f,0x01,0x7f,
          0x03,0x02,0x01,0x00,0x07,0x0a,0x01,0x06,0x61,0x64,0x64,0x4f,0x6e,0x65,0x00,0x00,
          0x0a,0x09,0x01,0x07,0x00,0x20,0x00,0x41,0x01,0x6a,0x0b
        ]);
        const t0 = performance.now();
        const { instance } = await WebAssembly.instantiate(bytes);
        const wasmOut = instance.exports.addOne(41);
        const t1 = performance.now();
        function fib(n) { return n < 2 ? 1 : fib(n - 1) + fib(n - 2); }
        const t2 = performance.now();
        const jsOut = fib(38);
        const t3 = performance.now();
        res.textContent =
          `Wasm OK — addOne(41) = ${wasmOut} (${(t1 - t0).toFixed(2)} ms instantiate+call)\n` +
          `JS fib(38) = ${jsOut} (${(t3 - t2).toFixed(2)} ms)\n` +
          `Module validated by WebAssembly.instantiate.`;
      } catch (err) {
        res.textContent = "Wasm error: " + err.message;
      }
    };
  }

  function openSettings() {
    const { body } = createWindow("Settings", "⚙️", 520, 400);
    body.innerHTML = `<div class="panel"><div class="panel-body">
      <div class="card"><h3>Desktop Environment</h3>
        <p>Active DE: <strong>HexaDE</strong> (top Deskbar, Haiku accents).</p>
        <p>Core OS and DE are decoupled — UI lives under <code>/static</code>.</p></div>
      <div class="card"><h3>Network</h3>
        <p>Online: ${navigator.onLine ? "yes" : "no"}</p></div>
    </div></div>`;
  }

  function openPackages() {
    const { body } = createWindow("Packages", "📦", 520, 400);
    body.innerHTML = `<div class="panel"><div class="panel-body">
      <div class="card"><h3>Install .apx</h3>
        <input type="file" id="apx-file" accept=".apx,.zip" style="color:#a0b0c0;font-size:12px">
        <button class="btn" id="apx-go">Install</button>
        <pre id="apx-log" style="margin-top:10px;color:#11ff55;font-size:12px"></pre>
      </div></div></div>`;
    $("#apx-go", body).onclick = async () => {
      const f = $("#apx-file", body).files[0];
      if (!f) return;
      const fd = new FormData(); fd.append("file", f);
      const j = await (await fetch("/api/apx/install", { method: "POST", body: fd })).json();
      $("#apx-log", body).textContent = j.ok ? j.message : j.error;
    };
  }

  function openExplorer() {
    const { body } = createWindow("Files", "📁", 560, 400);
    body.innerHTML = `<div style="padding:16px;color:#a0b0c0;font-size:13px">Use Terminal: <code>ls</code>, <code>cd</code>, <code>cat</code></div>`;
  }

  function openCalculator() {
    const { body } = createWindow("Calculator", "🧮", 280, 360);
    body.innerHTML = `<div style="padding:16px"><input id="cdisp" value="0" style="width:100%;font-size:24px;padding:8px;background:#0a0f14;border:none;color:#11ff55;text-align:right"></div>`;
  }

  function openEditor() {
    const { body } = createWindow("Editor", "📝", 640, 420);
    body.innerHTML = `<textarea style="width:100%;height:100%;background:#0d1219;border:none;color:#e0e6ed;padding:12px;font-family:monospace" placeholder="Notes…"></textarea>`;
  }

  function openBrowser() {
    const { body } = createWindow("Browser", "🌐", 760, 500);
    body.innerHTML = `<iframe src="https://example.com" style="width:100%;height:100%;border:none" sandbox="allow-scripts allow-same-origin allow-forms"></iframe>`;
  }

  function openSysInfo() {
    const { body } = createWindow("System", "ℹ️", 420, 280);
    body.innerHTML = `<div style="padding:20px;font-family:monospace;font-size:13px;color:#11ff55;white-space:pre-wrap">Loading…</div>`;
    const unsub = H.onMessage((d) => {
      if (d.output && d.output.includes("OS")) {
        $("div", body).textContent = d.output;
        unsub();
      }
    });
    H.sendCmd("sysinfo");
  }

  function openMedia() {
    const { body } = createWindow("Media", "🎬", 720, 480);
    body.innerHTML = `<div style="padding:16px;color:#a0b0c0">Open Packages → media-player.apx or use demo streams in a future build.</div>`;
  }

  /* Context menu */
  let activeMenu = null;
  function closeCtx() { if (activeMenu) { activeMenu.remove(); activeMenu = null; } }
  function showCtx(x, y, items) {
    closeCtx();
    const menu = document.createElement("div");
    menu.className = "apex-context-menu";
    menu.style.left = x + "px";
    menu.style.top = y + "px";
    items.forEach((item) => {
      if (item === "separator") {
        const sep = document.createElement("div"); sep.className = "sep"; menu.appendChild(sep); return;
      }
      const row = document.createElement("div");
      row.className = "row";
      row.innerHTML = `<span>${item.icon || ""}</span><span>${item.label}</span>`;
      row.onclick = (e) => { e.stopPropagation(); closeCtx(); item.action && item.action(); };
      menu.appendChild(row);
    });
    document.body.appendChild(menu);
    activeMenu = menu;
  }
  document.addEventListener("click", () => { closeCtx(); closePopups(); });
  document.addEventListener("contextmenu", (e) => {
    if (!$("#login-overlay").classList.contains("hidden")) return;
    const desk = $("#desktop");
    const iconEl = e.target.closest(".desktop-icon");
    if (e.target === desk || (desk.contains(e.target) && !e.target.closest(".window"))) {
      if (e.target.closest(".window")) return;
      e.preventDefault();
      if (iconEl) {
        const name = iconEl.querySelector(".label")?.textContent || "App";
        showCtx(e.clientX, e.clientY, [
          { label: "Open " + name, icon: "🚀", action: () => iconEl.dispatchEvent(new Event("dblclick")) },
          "separator",
          { label: "Properties", icon: "ℹ️", action: () => alert(name) },
        ]);
      } else {
        showCtx(e.clientX, e.clientY, [
          { label: "Open Terminal", icon: "💻", action: () => openApp("terminal") },
          { label: "Open Files", icon: "📁", action: () => openApp("explorer") },
          { label: "Task Manager", icon: "📊", action: () => openApp("taskman") },
          "separator",
          { label: "Settings", icon: "⚙️", action: () => openApp("settings") },
          { label: "Refresh", icon: "🔄", action: () => buildDesktop() },
          "separator",
          { label: "Sign out", icon: "⏻", action: () => { H.clearSession(); location.reload(); } },
        ]);
      }
    }
  });

  /* Deskbar chrome */
  $("#deskbar-menu-btn").onclick = (e) => {
    e.stopPropagation();
    $("#cal-pop")?.classList.remove("open");
    $("#start-menu").classList.toggle("open");
  };
  $("#deskbar-clock").onclick = (e) => {
    e.stopPropagation();
    $("#start-menu")?.classList.remove("open");
    $("#cal-pop").classList.toggle("open");
  };
  $("#db-logoff").onclick = () => { H.clearSession(); location.reload(); };
  $("#logout-btn").onclick = () => { H.clearSession(); location.reload(); };
  $("#start-menu").onclick = (e) => e.stopPropagation();
  $("#cal-pop").onclick = (e) => e.stopPropagation();

  if (navigator.usb) {
    const b = $("#db-usb");
    b.classList.remove("hidden");
    b.onclick = async (e) => {
      e.stopPropagation();
      try {
        const d = await navigator.usb.requestDevice({ filters: [] });
        alert("USB: " + (d.productName || d.vendorId));
      } catch (err) {
        if (err.name !== "NotFoundError") alert(err.message);
      }
    };
  }
  if (navigator.bluetooth) {
    const b = $("#db-bt");
    b.classList.remove("hidden");
    b.onclick = async (e) => {
      e.stopPropagation();
      try {
        const d = await navigator.bluetooth.requestDevice({ acceptAllDevices: true, optionalServices: [] });
        alert("BT: " + (d.name || d.id));
      } catch (err) {
        if (err.name !== "NotFoundError") alert(err.message);
      }
    };
  }

  /* Login */
  function doLogin() {
    const user = $("#login-user").value.trim();
    const pass = $("#login-pass").value;
    if (!user || !pass) { $("#login-error").textContent = "Fill both fields."; return; }
    if (!H.isReady()) { $("#login-error").textContent = "Connecting…"; return; }
    $("#login-error").textContent = "Signing in…";
    const unsub = H.onMessage((d) => {
      if (d.token) {
        currentUser = d.user || user;
        currentCwd = d.cwd || "/";
        H.setSession(d.token, currentUser, currentCwd);
        $("#login-overlay").classList.add("hidden");
        buildDesktop();
        setTimeout(() => openApp("terminal"), 200);
        unsub();
      } else if (d.output && /denied|invalid|Access/i.test(d.output)) {
        $("#login-error").textContent = "Invalid credentials.";
        unsub();
      }
    });
    H.send({ token: "", raw_input: `login ${user} ${pass}` });
  }
  $("#login-btn").onclick = doLogin;
  $("#login-pass").onkeydown = (e) => { if (e.key === "Enter") doLogin(); };

  if (H.getToken() && H.getUser()) {
    currentUser = H.getUser();
    $("#login-overlay").classList.add("hidden");
    buildDesktop();
  }

  window.HexaDE = { openApp, buildDesktop, createWindow };
})();
