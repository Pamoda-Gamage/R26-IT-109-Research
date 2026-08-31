/**
 * Servio dispatch-intake backend base URLs (voice/text/photo classification +
 * chat, REST + WebSocket). Override per-environment with
 * NEXT_PUBLIC_SERVIO_API_BASE / NEXT_PUBLIC_SERVIO_WS_BASE (see .env.example);
 * the literals below are the local dev defaults so the app runs with no env file.
 */
export const SERVIO_API_BASE =
  process.env.NEXT_PUBLIC_SERVIO_API_BASE ?? "http://localhost:8000";

export const SERVIO_WS_BASE =
  process.env.NEXT_PUBLIC_SERVIO_WS_BASE ?? "ws://localhost:8000";
