// ApexOS Calculator Addon
window.ApexApps = window.ApexApps || {};
window.ApexApps.calculator = {
  open(createWindow, sendCmd) {
    const { win, body } = createWindow("Calculatrice", "🧮", 320, 460);
    body.innerHTML = `
      <div style="height:100%;display:flex;flex-direction:column;background:#0d1219;padding:12px;gap:10px;font-family:system-ui">
        <div id="calc-display" style="background:#0a0f14;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:16px;font-size:28px;text-align:right;color:#11ff55;font-family:monospace;min-height:56px;overflow:hidden">0</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;flex:1">
          ${["C","±","%","÷","7","8","9","×","4","5","6","-","1","2","3","+","0",".","="].map((b,i)=>`
            <button data-k="${b}" style="
              border:none;border-radius:10px;font-size:18px;font-weight:600;cursor:pointer;
              background:${['÷','×','-','+','='].includes(b)?'#0072ff':b==='C'?'#ff5f57':'#1a2435'};
              color:white;transition:filter .12s;
              ${b==='0'?'grid-column:span 2':''}
            ">${b}</button>
          `).join("")}
        </div>
      </div>
    `;
    let current = "0", operator = null, previous = null, reset = false;
    const display = body.querySelector("#calc-display");
    const update = () => display.textContent = current;

    body.querySelectorAll("button").forEach(btn => {
      btn.onmouseenter = () => btn.style.filter = "brightness(1.15)";
      btn.onmouseleave = () => btn.style.filter = "";
      btn.onclick = () => {
        const k = btn.dataset.k;
        if (k >= "0" && k <= "9" || k === ".") {
          if (reset) { current = "0"; reset = false; }
          if (k === "." && current.includes(".")) return;
          current = current === "0" && k !== "." ? k : current + k;
        } else if (k === "C") {
          current = "0"; operator = previous = null;
        } else if (k === "±") {
          current = String(parseFloat(current) * -1);
        } else if (k === "%") {
          current = String(parseFloat(current) / 100);
        } else if (["+","-","×","÷"].includes(k)) {
          previous = parseFloat(current);
          operator = k;
          reset = true;
        } else if (k === "=") {
          if (operator && previous !== null) {
            const a = previous, b = parseFloat(current);
            let r = 0;
            if (operator === "+") r = a + b;
            if (operator === "-") r = a - b;
            if (operator === "×") r = a * b;
            if (operator === "÷") r = b !== 0 ? a / b : "Err";
            current = String(r);
            operator = previous = null;
            reset = true;
          }
        }
        update();
      };
    });
  }
};
