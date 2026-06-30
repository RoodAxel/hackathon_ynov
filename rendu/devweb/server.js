#!/usr/bin/env node
/**
 * TechCorp Finance Chat — serveur web (filière DEV WEB)
 *
 * - Sert l'interface de chat (dossier public/)
 * - Proxifie les requêtes vers le serveur d'inférence Ollama (évite les soucis CORS)
 * - Expose /health pour l'indicateur "connecté / déconnecté"
 *
 * AUCUNE dépendance externe (modules Node natifs) => lançable en UNE commande :
 *     node server.js        (ou: npm start)
 *
 * Variables d'environnement :
 *     PORT          port d'écoute de l'interface       (défaut 3000)
 *     OLLAMA_HOST   URL du serveur Ollama de l'INFRA   (défaut http://localhost:11434)
 *     MODEL         modèle par défaut proposé dans l'UI (défaut techcorp-finance)
 */

const http = require("http");
const fs = require("fs");
const path = require("path");
const { URL } = require("url");

const PORT = process.env.PORT || 3000;
const OLLAMA_HOST = (process.env.OLLAMA_HOST || "http://localhost:11434").replace(/\/$/, "");
const DEFAULT_MODEL = process.env.MODEL || "techcorp-finance";
const PUBLIC_DIR = path.join(__dirname, "public");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
};

/** Petit helper : requête HTTP vers Ollama, renvoie une Promise<IncomingMessage>. */
function ollamaRequest(method, pathName, body) {
  return new Promise((resolve, reject) => {
    const u = new URL(OLLAMA_HOST + pathName);
    const data = body ? Buffer.from(JSON.stringify(body)) : null;
    const req = http.request(
      {
        hostname: u.hostname,
        port: u.port || 80,
        path: u.pathname + u.search,
        method,
        headers: data
          ? { "Content-Type": "application/json", "Content-Length": data.length }
          : {},
      },
      resolve
    );
    req.on("error", reject);
    req.setTimeout(120000, () => req.destroy(new Error("timeout")));
    if (data) req.write(data);
    req.end();
  });
}

/** GET /health -> état de connexion Ollama + liste des modèles disponibles. */
async function handleHealth(res) {
  try {
    const r = await ollamaRequest("GET", "/api/tags");
    let raw = "";
    r.on("data", (c) => (raw += c));
    r.on("end", () => {
      try {
        const tags = JSON.parse(raw);
        const models = (tags.models || []).map((m) => m.name);
        sendJSON(res, 200, {
          connected: true,
          host: OLLAMA_HOST,
          defaultModel: DEFAULT_MODEL,
          models,
        });
      } catch (e) {
        sendJSON(res, 200, { connected: false, host: OLLAMA_HOST, error: "réponse Ollama illisible" });
      }
    });
  } catch (e) {
    sendJSON(res, 200, { connected: false, host: OLLAMA_HOST, error: e.message });
  }
}

/** POST /api/chat -> proxy streaming vers Ollama /api/chat (NDJSON). */
async function handleChat(req, res) {
  let bodyRaw = "";
  req.on("data", (c) => (bodyRaw += c));
  req.on("end", async () => {
    let payload;
    try {
      payload = JSON.parse(bodyRaw || "{}");
    } catch {
      return sendJSON(res, 400, { error: "JSON invalide" });
    }
    const ollamaBody = {
      model: payload.model || DEFAULT_MODEL,
      messages: payload.messages || [],
      stream: true,
      options: payload.options || {},
    };
    try {
      const upstream = await ollamaRequest("POST", "/api/chat", ollamaBody);
      if (upstream.statusCode >= 400) {
        let err = "";
        upstream.on("data", (c) => (err += c));
        upstream.on("end", () => sendJSON(res, 502, { error: `Ollama ${upstream.statusCode}: ${err}` }));
        return;
      }
      res.writeHead(200, {
        "Content-Type": "application/x-ndjson; charset=utf-8",
        "Cache-Control": "no-cache",
      });
      upstream.pipe(res); // pipe direct du flux NDJSON vers le navigateur
    } catch (e) {
      sendJSON(res, 502, { error: "Serveur d'inférence injoignable : " + e.message });
    }
  });
}

/** Sert un fichier statique depuis public/. */
function serveStatic(req, res) {
  let urlPath = decodeURIComponent(new URL(req.url, "http://x").pathname);
  if (urlPath === "/") urlPath = "/index.html";
  const filePath = path.join(PUBLIC_DIR, path.normalize(urlPath));
  if (!filePath.startsWith(PUBLIC_DIR)) return sendText(res, 403, "Forbidden");
  fs.readFile(filePath, (err, data) => {
    if (err) return sendText(res, 404, "Not found");
    res.writeHead(200, { "Content-Type": MIME[path.extname(filePath)] || "application/octet-stream" });
    res.end(data);
  });
}

function sendJSON(res, code, obj) {
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(obj));
}
function sendText(res, code, txt) {
  res.writeHead(code, { "Content-Type": "text/plain; charset=utf-8" });
  res.end(txt);
}

const server = http.createServer((req, res) => {
  if (req.method === "GET" && req.url === "/health") return handleHealth(res);
  if (req.method === "POST" && req.url === "/api/chat") return handleChat(req, res);
  return serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log("┌────────────────────────────────────────────────────┐");
  console.log("│  TechCorp Finance Chat — DEV WEB                    │");
  console.log("├────────────────────────────────────────────────────┤");
  console.log(`│  Interface : http://localhost:${PORT}`);
  console.log(`│  Ollama    : ${OLLAMA_HOST}`);
  console.log(`│  Modèle    : ${DEFAULT_MODEL}`);
  console.log("└────────────────────────────────────────────────────┘");
  console.log("Ctrl+C pour arrêter.");
});
