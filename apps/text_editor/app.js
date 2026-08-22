// ApexOS Text Editor Addon
window.ApexApps = window.ApexApps || {};
window.ApexApps.text_editor = {
  open(createWindow, sendCmd, options = {}) {
    const filename = options.filename || "sans_titre.txt";
    const { win, body } = createWindow("Éditeur — " + filename, "📝", 660, 480);
    body.innerHTML = `
      <div style="height:100%;display:flex;flex-direction:column;background:#0d1219">
        <div style="padding:8px 12px;background:#151e2c;border-bottom:1px solid rgba(255,255,255,0.06);display:flex;gap:8px;align-items:center">
          <input id="ed-path" value="${filename}" style="flex:1;background:#0a1018;border:1px solid rgba(255,255,255,0.1);border-radius:6px;padding:6px 10px;color:#c5d0dc;font-size:13px;outline:none">
          <button id="ed-save" style="background:#0072ff;border:none;color:white;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600">Enregistrer</button>
          <button id="ed-open" style="background:#1a2435;border:1px solid rgba(255,255,255,0.1);color:#c5d0dc;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px">Ouvrir</button>
        </div>
        <textarea id="ed-content" spellcheck="false" style="flex:1;background:#0d1219;border:none;outline:none;color:#e0e6ed;font-family:'Cascadia Code',Consolas,monospace;font-size:14px;line-height:1.5;padding:14px;resize:none"></textarea>
        <div id="ed-status" style="padding:4px 12px;font-size:11px;color:#5a6a7a;background:#111822;border-top:1px solid rgba(255,255,255,0.04)">Prêt</div>
      </div>
    `;
    const content = body.querySelector("#ed-content");
    const pathInput = body.querySelector("#ed-path");
    const status = body.querySelector("#ed-status");

    // Load if file given
    if (options.filename && options.filename !== "sans_titre.txt") {
      status.textContent = "Chargement...";
      const handler = (e) => {
        if (e.detail.output !== undefined) {
          content.value = e.detail.output.startsWith("cat:") ? "" : e.detail.output;
          status.textContent = content.value ? "Fichier chargé" : "Nouveau fichier";
          document.removeEventListener("apex-msg", handler);
        }
      };
      document.addEventListener("apex-msg", handler);
      sendCmd("cat " + options.filename);
    }

    body.querySelector("#ed-save").onclick = () => {
      const path = pathInput.value.trim() || "sans_titre.txt";
      const text = content.value;
      status.textContent = "Enregistrement...";
      // write uses spaces, so we need a better way for multiline.
      // For now we send a special command or use a simple approach.
      sendCmd("write " + path + " " + text.replace(/\n/g, "\\n"));
      status.textContent = "Enregistré : " + path;
      // Update window title
      const titleEl = win.querySelector(".title");
      if (titleEl) titleEl.textContent = "📝 Éditeur — " + path;
    };

    body.querySelector("#ed-open").onclick = () => {
      const path = pathInput.value.trim();
      if (!path) return;
      status.textContent = "Ouverture...";
      const handler = (e) => {
        if (e.detail.output !== undefined) {
          content.value = e.detail.output.startsWith("cat:") ? "" : e.detail.output;
          status.textContent = "Ouvert : " + path;
          document.removeEventListener("apex-msg", handler);
        }
      };
      document.addEventListener("apex-msg", handler);
      sendCmd("cat " + path);
    };
  }
};
