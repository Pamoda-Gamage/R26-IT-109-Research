"use client";

/**
 * Minimal client-side session helper. Auth is served by the Provider Match
 * backend (`:8001/auth/*`); tokens are demo stubs today. The signed-in
 * `user_id` is also what Servio's chat calls key off — see
 * `getOrCreateUserId()` in components/Usechatsession.tsx, which prefers
 * `user_id` and falls back to a per-browser guest id.
 */

export interface AuthSession {
  access_token: string;
  role: string;
  user_id?: string;
}

const TOKEN_KEY = "auth_token";
const ROLE_KEY = "auth_role";
const USER_ID_KEY = "user_id";

export function storeSession(session: AuthSession): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, session.access_token);
  localStorage.setItem(ROLE_KEY, session.role);
  if (session.user_id) localStorage.setItem(USER_ID_KEY, session.user_id);
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(USER_ID_KEY);
}

export function getToken(): string | null {
  return typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY);
}

export function getRole(): string | null {
  return typeof window === "undefined" ? null : localStorage.getItem(ROLE_KEY);
}

export function isAuthed(): boolean {
  return getToken() != null;
}
