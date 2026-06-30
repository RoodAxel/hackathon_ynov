/* TechCorp Finance Chat — logique front (vanilla JS, sans dépendance) */

const els = {
  messages: document.getElementById("messages"),
  placeholder: document.getElementById("placeholder"),
  input: document.getElementById("input"),
  sendBtn: document.getElementById("sendBtn"),
  clearBtn: document.getElementById("clearBtn"),
  status: document.getElementById("status"),
  statusText: document.getElementById("statusText"),
  modelSelect: document.getElementById("modelSelect"),
};

let history = [];        // [{role:'user'|'assistant', content:string}]
let busy = false;
let connected = false;

/* ---------- Indicateur de connexion (polling /health) ---------- */
async function refreshHealth() {
  try {
    const r = await fetch("/health");
    const h = await r.json();
    connected = !!h.connected;
    setStatus(connected, connected ? "Connecté" : "Déconnecté");
    if (connected) populateModels(h.models, h.defaultModel);
  } catch {
    connected = false;
    setStatus(false, "Déconnecté");
  }
  updateSendState();
}

function setStatus(on, text) {
  els.status.classList.toggle("status--on", on);
  els.status.classList.toggle("status--off", !on);
  els.statusText.textContent = text;
}

function populateModels(models, def) {
  const current = els.modelSelect.value;
  if (!models || !models.length) {
    els.modelSelect.innerHTML = `<option value="${def || ""}">${def || "(aucun modèle)"}</option>`;
    return;
  }
  // évite de reconstruire si déjà à jour
  const wanted = models.join("|");
  if (els.modelSelect.dataset.list === wanted) return;
  els.modelSelect.dataset.list = wanted;
  els.modelSelect.innerHTML = models
    .map((m) => `<option value="${m}">${m}</option>`)
    .join("");
  // sélectionne le modèle par défaut s'il existe, sinon garde le choix courant
  if (models.includes(current)) els.modelSelect.value = current;
  else if (def && models.includes(def)) els.modelSelect.value = def;
}

/* ---------- Rendu des messages ---------- */
function addMessage(role, content) {
  if (els.placeholder) els.placeholder.remove();
  const wrap = document.createElement("div");
  wrap.className = `msg msg--${role}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "🧑" : "🤖";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content;
  wrap.append(avatar, bubble);
  els.messages.appendChild(wrap);
  els.messages.scrollTop = els.messages.scrollHeight;
  return bubble;
}

/* ---------- Envoi + streaming NDJSON ---------- */
async function send() {
  const text = els.input.value.trim();
  if (!text || busy || !connected) return;

  addMessage("user", text);
  history.push({ role: "user", content: text });
  els.input.value = "";
  autoGrow();

  busy = true;
  updateSendState();

  const bubble = addMessage("assistant", "");
  bubble.classList.add("cursor");
  let answer = "";

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: els.modelSelect.value, messages: history }),
    });

    if (!resp.ok) {
      const e = await resp.json().catch(() => ({}));
      throw new Error(e.error || `Erreur serveur (${resp.status})`);
    }

    // Lecture du flux NDJSON renvoyé par Ollama via notre proxy
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let nl;
      while ((nl = buffer.indexOf("\n")) >= 0) {
        const line = buffer.slice(0, nl).trim();
        buffer = buffer.slice(nl + 1);
        if (!line) continue;
        try {
          const obj = JSON.parse(line);
          const piece = obj.message?.content || obj.response || "";
          if (piece) {
            answer += piece;
            bubble.textContent = answer;
            els.messages.scrollTop = els.messages.scrollHeight;
          }
        } catch { /* ligne partielle, on attend la suite */ }
      }
    }
    bubble.classList.remove("cursor");
    if (!answer) bubble.textContent = "(réponse vide)";
    history.push({ role: "assistant", content: answer });
  } catch (err) {
    bubble.classList.remove("cursor");
    bubble.classList.add("error");
    bubble.textContent = "⚠️ " + err.message;
    // on retire le tour utilisateur en échec pour ne pas polluer le contexte
    history.pop();
  } finally {
    busy = false;
    updateSendState();
    els.input.focus();
  }
}

/* ---------- UI helpers ---------- */
function updateSendState() {
  els.sendBtn.disabled = busy || !connected || !els.input.value.trim();
  els.sendBtn.textContent = busy ? "…" : "Envoyer";
}
function autoGrow() {
  els.input.style.height = "auto";
  els.input.style.height = Math.min(els.input.scrollHeight, 160) + "px";
}
function clearConversation() {
  history = [];
  els.messages.innerHTML = "";
  const p = document.createElement("div");
  p.className = "placeholder";
  p.id = "placeholder";
  p.innerHTML = '<p>💬 Conversation effacée. Posez une nouvelle question.</p>';
  els.messages.appendChild(p);
  els.placeholder = p;
}

/* ---------- Événements ---------- */
els.input.addEventListener("input", () => { autoGrow(); updateSendState(); });
els.input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
});
els.sendBtn.addEventListener("click", send);
els.clearBtn.addEventListener("click", clearConversation);

/* ---------- Init ---------- */
refreshHealth();
setInterval(refreshHealth, 5000);   // re-vérifie l'état toutes les 5 s
