const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status}: ${text}`);
  }
  return response.json();
}

export function health() {
  return request("/health");
}

export function analyzeIntent(payload) {
  return request("/api/analyze-intent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function matchService(payload) {
  return request("/api/match-service", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function registerProvider(payload) {
  return request("/api/providers/register-voice", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function voiceLogin(payload) {
  return request("/api/auth/voice-login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function listProviders() {
  return request("/api/providers");
}

export function listRequests() {
  return request("/api/requests");
}
