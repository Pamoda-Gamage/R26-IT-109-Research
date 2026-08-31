import { useEffect, useRef, useState, useCallback } from "react";
import {
  SERVIO_API_BASE as API_BASE,
  SERVIO_WS_BASE as WS_BASE,
} from "../lib/servio-api";

// Re-exported so existing importers (VoiceRecorder, etc.) keep working.
export { API_BASE };

export interface Message {
  id: string;
  chat_id: string;
  sender: "user" | "assistant";
  type: "text" | "audio" | "image";
  status: "processing" | "complete" | "failed";
  content: string | null;
  translation?: string | null;
  media_url?: string | null;
  classification?: any;
  error?: string | null;
  timestamp: number;
}

/** Live "what is the backend doing right now" event. Additive — the chat UI
 * ignores it; the guided request flow renders it as a progress stepper. */
export interface StageEvent {
  type: "stage";
  chat_id: string;
  message_id: string | null;
  stage:
    | "transcribing"
    | "translating"
    | "analysing_photo"
    | "understanding"
    | "classifying"
    | "finalising"
    | "failed";
  state: "start" | "done" | "error";
  detail?: Record<string, unknown> | null;
  /** Server epoch-ms when this stage event was broadcast — absent on stage
   * events from a backend that predates this field. */
  ts?: number;
}

/**
 * One instance of this hook == one open chat/case. To support multiple
 * concurrent chats (a sidebar of cases, like ChatGPT), mount one of these
 * per active chat_id, or lift chatId into state at the page level and only
 * keep a socket open for whichever chat is currently in view — don't hold
 * a websocket per chat in the sidebar simultaneously unless you actually
 * need live updates on background chats too.
 */
export function useChatSession(chatId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [connected, setConnected] = useState(false);
  const [stage, setStage] = useState<StageEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!chatId) return;
    setStage(null);

    const ws = new WebSocket(`${WS_BASE}/ws/chats/${chatId}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false); // onclose still fires after this; nothing further to do here

    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "history") {
        setMessages(payload.messages);
      } else if (payload.type === "message") {
        setMessages((prev) => [...prev, payload.message]);
        // An assistant message is the terminal event of a pipeline run.
        if (payload.message?.sender === "assistant") setStage(null);
      } else if (payload.type === "message_update") {
        setMessages((prev) =>
          prev.map((m) => (m.id === payload.message.id ? payload.message : m)),
        );
        if (payload.message?.status === "failed") setStage(null);
      } else if (payload.type === "stage") {
        setStage(payload as StageEvent);
      }
      // payload.type === "error" -> surface via your existing uploadError state
    };

    return () => ws.close();
  }, [chatId]);

  const sendText = useCallback(
    async (
      text: string,
      model: string,
    ): Promise<{ message_id: string } | null> => {
      if (!chatId) return null;
      const res = await fetch(`${API_BASE}/api/chats/${chatId}/messages/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, model }),
      });
      if (!res.ok) throw new Error(`Send failed: ${res.status}`);
      // The actual message content still arrives via the socket broadcast —
      // this return value is only so the caller can track "which message
      // did I just send" for retry/error UI against the right bubble.
      return res.json();
    },
    [chatId],
  );

  const sendAudio = useCallback(
    async (
      blob: Blob,
      model: string,
    ): Promise<{ message_id: string } | null> => {
      if (!chatId) return null;
      const form = new FormData();
      form.append("file", blob, "recording.webm");
      form.append("model", model);
      const res = await fetch(
        `${API_BASE}/api/chats/${chatId}/messages/audio`,
        {
          method: "POST",
          body: form,
        },
      );
      if (!res.ok) throw new Error(`Send failed: ${res.status}`);
      return res.json();
    },
    [chatId],
  );

  const sendImage = useCallback(
    async (
      file: File,
      caption = "",
    ): Promise<{ message_id: string } | null> => {
      if (!chatId) return null;
      const form = new FormData();
      form.append("file", file);
      form.append("caption", caption);
      const res = await fetch(
        `${API_BASE}/api/chats/${chatId}/messages/image`,
        {
          method: "POST",
          body: form,
        },
      );
      if (!res.ok) throw new Error(`Send failed: ${res.status}`);
      return res.json();
    },
    [chatId],
  );

  return { messages, connected, stage, sendText, sendAudio, sendImage };
}

export interface ChatSummary {
  id: string;
  title: string;
  status: "open" | "closed";
  updated_at: string;
}

/** Sidebar data: list of a user's chats/cases. Throws a plain Error with a
 * user-presentable message on failure — callers should catch this rather
 * than let it become an unhandled rejection. */
export async function listChats(userId: string): Promise<ChatSummary[]> {
  const res = await fetchOrThrow(`${API_BASE}/api/chats?user_id=${userId}`);
  return res.json();
}

export async function createChat(
  userId: string,
  title?: string,
): Promise<ChatSummary> {
  const res = await fetchOrThrow(`${API_BASE}/api/chats`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, title }),
  });
  return res.json();
}

/** fetch() throws a bare "Failed to fetch" TypeError when the server is
 * simply unreachable (not running, wrong host/port, no network) — that
 * message is accurate but not something to show a user as-is. Normalize
 * both that case and non-2xx responses into one Error type so callers can
 * do a single try/catch and display err.message directly. */
async function fetchOrThrow(
  url: string,
  init?: RequestInit,
): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(url, init);
  } catch {
    throw new Error(
      "Can't reach the server. Server may be down or unreachable from this network. Please check your connection and try again.",
    );
  }
  if (!res.ok) {
    throw new Error(`Server error (${res.status}). Please try again.`);
  }
  return res;
}

/**
 * There's no real auth yet (see the README note in routers/chats.py), so
 * this stands in for "who is asking": a random id minted once per browser
 * and persisted in localStorage. Swap the body of this function for the
 * logged-in user's real id as soon as auth exists — every caller (listChats,
 * createChat, the chat-ownership check server-side) already keys off
 * user_id, so nothing else has to change.
 */
export function getOrCreateUserId(): string {
  if (typeof window === "undefined") return "";
  // A signed-in user (Provider Match auth stores `user_id`) takes precedence,
  // so their chats/cases follow the real account. Guests get a stable
  // per-browser id.
  const authedId = localStorage.getItem("user_id");
  if (authedId) return authedId;
  const key = "dispatch_user_id";
  let id = localStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(key, id);
  }
  return id;
}
