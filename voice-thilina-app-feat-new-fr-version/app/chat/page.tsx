"use client";
import { useEffect, useState, useCallback } from "react";
import {
  Plus,
  PanelLeft,
  X,
  MessageSquare,
  AlertCircle,
  RotateCcw,
} from "lucide-react";
import VoiceRecorder from "../../components/VoiceRecorder";
import ChatHero from "../../components/ChatHero";
import ModelSelector from "../../components/ModelSelector";
import {
  listChats,
  createChat,
  getOrCreateUserId,
  type ChatSummary,
  type Message,
} from "../../components/Usechatsession";

export default function Page() {
  const [userId] = useState(getOrCreateUserId);
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedModel, setSelectedModel] = useState("auto");
  const [serverError, setServerError] = useState<string | null>(null);

  const refreshChats = useCallback(async () => {
    try {
      const list = await listChats(userId);
      setChats(list);
      setServerError(null);
      return list;
    } catch (err) {
      // Most common cause: the FastAPI backend isn't running, or isn't
      // reachable from wherever this page is loaded (e.g. a hosted preview
      // that can't see your localhost). Surface it instead of throwing.
      setServerError(
        err instanceof Error ? err.message : "Couldn't load your cases.",
      );
      return [];
    }
  }, [userId]);

  // Land on the most recent case on load, if the user has one. First-time
  // users get an empty state (ChatHero) with nothing to select yet.
  useEffect(() => {
    (async () => {
      const list = await refreshChats();
      if (list.length > 0) setActiveChatId(list[0].id);
    })();
  }, [refreshChats]);

  const handleNewChat = async () => {
    try {
      const chat = await createChat(userId);
      setServerError(null);
      await refreshChats();
      setActiveChatId(chat.id);
      setMessages([]);
      setSidebarOpen(false);
    } catch (err) {
      setServerError(
        err instanceof Error ? err.message : "Couldn't start a new case.",
      );
    }
  };

  const handleSelectChat = (id: string) => {
    if (id === activeChatId) {
      setSidebarOpen(false);
      return;
    }
    setActiveChatId(id);
    setMessages([]); // cleared until the socket replays history for the new chat
    setSidebarOpen(false);
  };

  return (
    <div className="relative flex h-dvh flex-col overflow-hidden bg-(--servio-bg) text-(--servio-text)">
      <header className="relative z-30 flex items-center justify-between border-b border-(--servio-border) bg-(--servio-surface)/80 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setSidebarOpen(true)}
            aria-label="Open cases"
            className="servio-focus flex h-9 w-9 items-center justify-center rounded-full text-(--servio-muted) transition hover:bg-(--servio-primary-soft) active:scale-90"
          >
            <PanelLeft className="h-4.5 w-4.5" />
          </button>
          <span className="text-sm font-semibold text-(--servio-primary)">
            Servio
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleNewChat}
            aria-label="New case"
            className="servio-focus flex h-9 w-9 items-center justify-center rounded-full text-(--servio-muted) transition hover:bg-(--servio-primary-soft) active:scale-90"
          >
            <Plus className="h-4.5 w-4.5" />
          </button>
          <ModelSelector selected={selectedModel} onChange={setSelectedModel} />
        </div>
      </header>

      {serverError && (
        <div className="relative z-30 mx-auto mt-2 flex w-full max-w-md items-center gap-2 rounded-full border border-(--servio-danger)/30 bg-(--servio-danger)/5 px-3 py-1.5 text-xs text-(--servio-danger)">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span className="flex-1">{serverError}</span>
          <button
            onClick={() => refreshChats()}
            aria-label="Retry connecting"
            className="servio-focus flex items-center gap-1 rounded-full border border-(--servio-danger)/30 px-2 py-1 font-medium transition active:scale-95"
          >
            <RotateCcw className="h-3 w-3" /> Retry
          </button>
        </div>
      )}

      <ChatHero visible={messages.length === 0} />

      <VoiceRecorder
        chatId={activeChatId}
        onMessagesChange={setMessages}
        selectedModel={selectedModel}
      />

      {/* ---------- CASE SWITCHER (slide-over) ---------- */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 flex">
          <div className="flex w-72 shrink-0 flex-col border-r border-(--servio-border) bg-(--servio-surface)">
            <div className="flex items-center justify-between px-3 py-3">
              <span className="text-sm font-medium text-(--servio-text)">
                Your cases
              </span>
              <button
                onClick={() => setSidebarOpen(false)}
                aria-label="Close"
                className="servio-focus flex h-8 w-8 items-center justify-center rounded-full text-(--servio-muted) transition hover:bg-(--servio-primary-soft) active:scale-90"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="px-3 pb-3">
              <button
                onClick={handleNewChat}
                className="servio-focus flex w-full items-center justify-center gap-2 rounded-xl bg-(--servio-primary) px-3 py-2.5 text-sm font-medium text-white shadow-(--servio-shadow) transition hover:bg-(--servio-primary-hover) active:scale-95"
              >
                <Plus className="h-4 w-4" /> New case
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-2 pb-2">
              {chats.length === 0 && (
                <p className="px-2 py-4 text-center text-xs text-(--servio-muted)">
                  No cases yet — start one above.
                </p>
              )}
              {chats.map((chat) => (
                <button
                  key={chat.id}
                  onClick={() => handleSelectChat(chat.id)}
                  className={`servio-focus mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                    chat.id === activeChatId
                      ? "bg-(--servio-primary-soft) text-(--servio-primary)"
                      : "text-(--servio-muted) hover:bg-(--servio-primary-soft) hover:text-(--servio-text)"
                  }`}
                >
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate">{chat.title}</span>
                </button>
              ))}
            </div>
          </div>

          <div
            className="flex-1 bg-black/30"
            onClick={() => setSidebarOpen(false)}
          />
        </div>
      )}
    </div>
  );
}
