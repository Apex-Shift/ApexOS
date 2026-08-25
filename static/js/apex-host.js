/** ApexHost — OS bridge (WebSocket, session). DE-agnostic. */
window.ApexHost = (() => {
  let ws = null, ready = false;
  let token = sessionStorage.getItem("apex_token") || "";
  let user = sessionStorage.getItem("apex_user") || "";
  let cwd = "/";
  const handlers = new Set();

  function connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    try { if (ws) { ws.onclose = null; ws.close(); } } catch (_) {}
    ws = new WebSocket(`${proto}://${location.host}/ws`);
    ws.onopen = () => {
      ready = true;
      document.dispatchEvent(new CustomEvent("apex-ws-open"));
    };
    ws.onmessage = (ev) => {
      try {
        const d = JSON.parse(ev.data);
        if (d.token) { token = d.token; sessionStorage.setItem("apex_token", token); }
        if (d.user) { user = d.user; sessionStorage.setItem("apex_user", user); }
        if (d.cwd) cwd = d.cwd;
        handlers.forEach((h) => h(d));
        document.dispatchEvent(new CustomEvent("apex-msg", { detail: d }));
      } catch (_) {}
    };
    ws.onerror = () => { ready = false; };
    ws.onclose = () => { ready = false; setTimeout(connect, 1500); };
  }

  connect();

  return {
    connect,
    isReady: () => ready && ws && ws.readyState === 1,
    getToken: () => token,
    getUser: () => user,
    getCwd: () => cwd,
    setSession(t, u, c) {
      token = t || token;
      user = u || user;
      if (c) cwd = c;
      if (token) sessionStorage.setItem("apex_token", token);
      if (user) sessionStorage.setItem("apex_user", user);
    },
    clearSession() {
      token = ""; user = ""; cwd = "/";
      sessionStorage.removeItem("apex_token");
      sessionStorage.removeItem("apex_user");
    },
    send(obj) {
      if (ws && ws.readyState === 1) ws.send(JSON.stringify(obj));
    },
    sendCmd(raw) {
      this.send({ token, raw_input: raw });
    },
    sendWrite(path, content) {
      this.send({ token, action: "write_file", path, content });
    },
    sudoAuth(password) {
      this.send({ token, action: "sudo_auth", password });
    },
    onMessage(fn) {
      handlers.add(fn);
      return () => handlers.delete(fn);
    },
  };
})();
