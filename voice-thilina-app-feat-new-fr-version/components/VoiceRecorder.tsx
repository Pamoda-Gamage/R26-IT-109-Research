"use client";
import { useRef, useState, useEffect, useCallback } from "react";
import {
  Mic,
  Send,
  Play,
  Pause,
  Trash2,
  Square,
  AlertCircle,
  RotateCcw,
  Paperclip,
  X,
  WifiOff,
  Eye,
} from "lucide-react";
import {
  ClassificationBadge,
  type Classification,
} from "./Classificationbadge";
import { useChatSession, API_BASE, type Message } from "./Usechatsession";

type DockState = "idle" | "recording" | "audio-preview" | "image-preview";

interface VoiceRecorderProps {
  /** The active case/conversation. Nothing can be sent without one — the
   * component renders an empty state until a chat is selected/created
   * upstream (e.g. from a sidebar calling createChat/listChats). */
  chatId: string | null;
  variant?: "fixed" | "inline";
  placeholder?: string;
  selectedModel?: string;
  /** Fires whenever this chat's messages change — handy for a sidebar that
   * wants to show a last-message preview without re-fetching. */
  onMessagesChange?: (msgs: Message[]) => void;
}

const BAR_COUNT = 28;
const MAX_RECORD_SECONDS = 120;
const WARNING_AT_SECONDS = 105; // last 15s turns the waveform amber->red

// Shared dock control styles.
const ICON_BTN =
  "flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-(--servio-border) bg-(--servio-surface-2) text-(--servio-text) transition hover:bg-(--servio-primary-soft) active:scale-90 disabled:opacity-40";
const SEND_BTN =
  "flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-(--servio-primary) text-white shadow-sm transition hover:bg-(--servio-primary-hover) active:scale-90 disabled:opacity-40";

function formatTime(totalSeconds: number) {
  const m = Math.floor(totalSeconds / 60);
  const s = Math.floor(totalSeconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatClock(ts: number) {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

const IMAGE_DESCRIPTION_PREVIEW_LENGTH = 140;

/** Renders the vision model's read of an uploaded photo — kept visually
 * distinct from a spoken/typed-word translation (labeled, truncated) since
 * it's the AI's interpretation of the image, not the user's own words. */
function VisionDescription({ text, isUser }: { text: string; isUser: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = text.length > IMAGE_DESCRIPTION_PREVIEW_LENGTH;
  const shown =
    expanded || !isLong
      ? text
      : `${text.slice(0, IMAGE_DESCRIPTION_PREVIEW_LENGTH).trimEnd()}…`;

  return (
    <div
      className={`mt-1 border-t pt-1 text-[12px] italic ${
        isUser ? "border-white/30 text-white/80" : "border-(--servio-border) text-(--servio-muted)"
      }`}
    >
      <span className="mb-0.5 flex items-center gap-1 font-medium not-italic opacity-80">
        <Eye className="h-3 w-3 shrink-0" /> What I see
      </span>
      <p className="whitespace-pre-wrap wrap-break-word">{shown}</p>
      {isLong && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="mt-0.5 text-[11px] font-medium not-italic underline underline-offset-2 opacity-90"
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      )}
    </div>
  );
}

function VoiceRecorder({
  chatId,
  variant = "fixed",
  placeholder = "Describe your request…",
  selectedModel = "auto",
  onMessagesChange,
}: VoiceRecorderProps) {
  const { messages, connected, sendText, sendAudio, sendImage } =
    useChatSession(chatId);

  useEffect(() => {
    onMessagesChange?.(messages);
  }, [messages, onMessagesChange]);

  const [dockState, setDockState] = useState<DockState>("idle");
  const [text, setText] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [recordedDuration, setRecordedDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [justSent, setJustSent] = useState(false);

  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);

  const recorder = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const urlRef = useRef<string | null>(null);
  const blobRef = useRef<Blob | null>(null);
  const audioElRef = useRef<HTMLAudioElement | null>(null);

  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const barRefs = useRef<(HTMLDivElement | null)[]>([]);

  const startTimeRef = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Tracks the id + payload of the most recent audio/image send so a
  // "failed" status on that specific message can be retried without
  // re-recording/re-picking. Cleared once that message reaches "complete".
  const retryRef = useRef<
    | { messageId: string; kind: "audio"; blob: Blob; duration: number }
    | { messageId: string; kind: "image"; file: File; caption: string }
    | null
  >(null);

  useEffect(() => {
    if (!retryRef.current) return;
    const tracked = messages.find((m) => m.id === retryRef.current!.messageId);
    if (tracked?.status === "complete") retryRef.current = null;
  }, [messages]);

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (timerRef.current) clearInterval(timerRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      audioCtxRef.current?.close().catch(() => {});
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages]);

  const isProcessing = messages.some((m) => m.status === "processing");

  // ---------- recording ----------

  const getStream = async () => {
    if (!streamRef.current) {
      streamRef.current = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
    }
    return streamRef.current;
  };

  const drawFrame = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);

    const nearLimit =
      (Date.now() - startTimeRef.current) / 1000 >= WARNING_AT_SECONDS;
    const step = Math.floor(data.length / BAR_COUNT) || 1;
    for (let i = 0; i < BAR_COUNT; i++) {
      const v = data[i * step] ?? 0;
      const pct = Math.max(0.12, v / 255);
      const el = barRefs.current[i];
      if (el) {
        el.style.transform = `scaleY(${pct})`;
        el.style.background = nearLimit
          ? "linear-gradient(to top, #fb4141, #f5a623)"
          : "linear-gradient(to top, #f5a623, #fde68a)";
      }
    }
    rafRef.current = requestAnimationFrame(drawFrame);
  }, []);

  const startRecording = async () => {
    setPermissionError(null);
    setUploadError(null);
    if (recorder.current?.state === "recording") return;

    let stream: MediaStream;
    try {
      stream = await getStream();
    } catch {
      setPermissionError(
        "Microphone access denied. Enable it in your browser settings.",
      );
      return;
    }

    chunksRef.current = [];
    recorder.current = new MediaRecorder(stream);
    recorder.current.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.current.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      blobRef.current = blob;
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      urlRef.current = URL.createObjectURL(blob);
    };
    recorder.current.start();

    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
    const ctx = new AudioCtx();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);
    audioCtxRef.current = ctx;
    analyserRef.current = analyser;
    rafRef.current = requestAnimationFrame(drawFrame);

    startTimeRef.current = Date.now();
    setElapsed(0);
    timerRef.current = setInterval(() => {
      const secs = (Date.now() - startTimeRef.current) / 1000;
      setElapsed(secs);
      if (secs >= MAX_RECORD_SECONDS) finishRecording(true); // auto-stop safeguard
    }, 200);

    setDockState("recording");
  };

  const finishRecording = (keep: boolean) => {
    if (recorder.current?.state === "recording") recorder.current.stop();
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (timerRef.current) clearInterval(timerRef.current);
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
    analyserRef.current = null;

    const finalDuration = (Date.now() - startTimeRef.current) / 1000;

    if (keep && finalDuration > 0.4) {
      setRecordedDuration(finalDuration);
      setDockState("audio-preview");
    } else {
      blobRef.current = null;
      setDockState("idle");
    }
  };

  const togglePlay = () => {
    if (!urlRef.current) return;
    if (!audioElRef.current) {
      audioElRef.current = new Audio(urlRef.current);
      audioElRef.current.onended = () => setIsPlaying(false);
    }
    if (isPlaying) {
      audioElRef.current.pause();
      setIsPlaying(false);
    } else {
      audioElRef.current.play();
      setIsPlaying(true);
    }
  };

  const discardRecording = () => {
    audioElRef.current?.pause();
    audioElRef.current = null;
    setIsPlaying(false);
    blobRef.current = null;
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
    setDockState("idle");
  };

  // ---------- sending ----------

  const sendVoice = async () => {
    const blob = blobRef.current;
    const duration = recordedDuration;
    if (!blob) return;
    setJustSent(true);
    setTimeout(() => setJustSent(false), 900);
    discardRecording();
    try {
      const res = await sendAudio(blob, selectedModel);
      if (res)
        retryRef.current = {
          messageId: res.message_id,
          kind: "audio",
          blob,
          duration,
        };
    } catch {
      setUploadError(
        "Couldn't send that recording. Check your connection and try again.",
      );
    }
  };

  const sendCurrentText = async () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setText("");
    setJustSent(true);
    setTimeout(() => setJustSent(false), 900);
    inputRef.current?.blur();
    setUploadError(null);
    try {
      await sendText(trimmed, selectedModel);
    } catch {
      setUploadError(
        "Couldn't send that message. Check your connection and try again.",
      );
    }
  };

  const pickImage = () => fileInputRef.current?.click();

  const onImageSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-selecting the same file later
    if (!file) return;
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    setSelectedImage(file);
    setImagePreviewUrl(URL.createObjectURL(file));
    setDockState("image-preview");
  };

  const discardImage = () => {
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    setSelectedImage(null);
    setImagePreviewUrl(null);
    setText("");
    setDockState("idle");
  };

  const sendCurrentImage = async () => {
    if (!selectedImage) return;
    const file = selectedImage;
    const caption = text.trim();
    setJustSent(true);
    setTimeout(() => setJustSent(false), 900);
    discardImage();
    setUploadError(null);
    try {
      const res = await sendImage(file, caption);
      if (res)
        retryRef.current = {
          messageId: res.message_id,
          kind: "image",
          file,
          caption,
        };
    } catch {
      setUploadError(
        "Couldn't send that photo. Check your connection and try again.",
      );
    }
  };

  const retryFailed = async (messageId: string) => {
    const pending = retryRef.current;
    if (!pending || pending.messageId !== messageId) return;
    setUploadError(null);
    try {
      if (pending.kind === "audio") {
        const res = await sendAudio(pending.blob, selectedModel);
        if (res) retryRef.current = { ...pending, messageId: res.message_id };
      } else {
        const res = await sendImage(pending.file, pending.caption);
        if (res) retryRef.current = { ...pending, messageId: res.message_id };
      }
    } catch {
      setUploadError("Retry failed. Check your connection and try again.");
    }
  };

  const nearLimit = dockState === "recording" && elapsed >= WARNING_AT_SECONDS;
  const noChat = !chatId;

  return (
    <div
      className={
        variant === "fixed"
          ? "flex h-dvh min-h-0 flex-col"
          : "flex h-full min-h-0 flex-col"
      }
    >
      {/* ---------- CONNECTION STATUS ---------- */}
      {chatId && !connected && (
        <div className="mx-auto mt-2 flex w-full max-w-md items-center gap-2 rounded-full border border-(--servio-warn)/30 bg-(--servio-warn)/10 px-3 py-1.5 text-xs text-(--servio-warn)">
          <WifiOff className="h-3.5 w-3.5 shrink-0" />
          <span>Reconnecting…</span>
        </div>
      )}

      {/* ---------- MESSAGE LIST ---------- */}
      <div
        className="flex min-h-0 flex-1 flex-col overflow-y-auto px-3 pt-4"
        aria-live="polite"
        aria-busy={isProcessing}
      >
        <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-end gap-3 pb-4">
          {noChat && (
            <p className="mb-2 text-center text-sm text-(--servio-muted)">
              Select or start a case to begin.
            </p>
          )}

          {messages.map((msg) => {
            const isUser = msg.sender === "user";
            const failed = msg.status === "failed";
            const canRetry = failed && retryRef.current?.messageId === msg.id;

            return (
              <div
                key={msg.id}
                className={`flex w-full flex-col ${isUser ? "items-end" : "items-start"}`}
              >
                <div
                  className={`relative max-w-[78%] rounded-2xl px-4 py-2.5 text-[14px] leading-snug shadow-sm ${
                    isUser
                      ? "rounded-br-md bg-(--servio-primary) text-white shadow-(--servio-shadow)"
                      : "rounded-bl-md border border-(--servio-border) bg-(--servio-surface) text-(--servio-text)"
                  } ${failed ? "border border-(--servio-danger)/50" : ""}`}
                >
                  {msg.type === "image" && msg.media_url && (
                    <img
                      src={`${API_BASE}${msg.media_url}`}
                      alt="Attached photo"
                      className="mb-2 max-h-56 w-full rounded-lg object-cover"
                    />
                  )}

                  {msg.status === "processing" ? (
                    <div className="flex items-center gap-1.5 py-0.5">
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current opacity-70 [animation-delay:-0.3s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current opacity-70 [animation-delay:-0.15s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current opacity-70" />
                    </div>
                  ) : (
                    msg.content && (
                      <p className="whitespace-pre-wrap wrap-break-word">
                        {msg.content}
                      </p>
                    )
                  )}

                  {msg.translation &&
                    (msg.type === "image" ? (
                      <VisionDescription text={msg.translation} isUser={isUser} />
                    ) : (
                      <p
                        className={`mt-1 whitespace-pre-wrap wrap-break-word border-t pt-1 text-[12px] italic ${
                          isUser
                            ? "border-white/30 text-white/80"
                            : "border-(--servio-border) text-(--servio-muted)"
                        }`}
                      >
                        {msg.translation}
                      </p>
                    ))}

                  {failed && (
                    <div className="mt-1.5 flex items-center gap-2 text-[12px] text-(--servio-danger)">
                      <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                      <span className="flex-1">Failed to process</span>
                      {canRetry && (
                        <button
                          onClick={() => retryFailed(msg.id)}
                          className="flex items-center gap-1 rounded-full border border-(--servio-danger)/30 px-2 py-0.5 font-medium transition active:scale-95"
                        >
                          <RotateCcw className="h-3 w-3" /> Retry
                        </button>
                      )}
                    </div>
                  )}

                  <span
                    className={`mt-1 block text-[10px] ${isUser ? "text-white/70" : "text-(--servio-muted)"}`}
                  >
                    {formatClock(msg.timestamp)}
                  </span>
                </div>

                {msg.classification && (
                  <div className="mt-1.5 max-w-[78%]">
                    <ClassificationBadge
                      classification={msg.classification as Classification}
                    />
                  </div>
                )}
              </div>
            );
          })}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* ---------- INPUT DOCK ---------- */}
      <div
        className={variant === "fixed" ? "px-3 pb-3" : "w-full px-1"}
        style={
          variant === "fixed"
            ? { paddingBottom: "calc(env(safe-area-inset-bottom, 0px) + 12px)" }
            : undefined
        }
      >
        <div className="mx-auto w-full max-w-md">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={onImageSelected}
          />

          {permissionError && (
            <div className="mb-2 flex items-center gap-2 rounded-2xl border border-(--servio-danger)/30 bg-(--servio-danger)/5 px-3 py-2 text-xs text-(--servio-danger)">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{permissionError}</span>
            </div>
          )}

          {uploadError && (
            <div className="mb-2 flex items-center gap-2 rounded-2xl border border-(--servio-danger)/30 bg-(--servio-danger)/5 px-3 py-2 text-xs text-(--servio-danger)">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span className="flex-1">{uploadError}</span>
            </div>
          )}

          <div className="relative overflow-hidden rounded-3xl border border-(--servio-border) bg-(--servio-surface) shadow-(--servio-shadow)">
            <div className="relative flex items-center gap-2 p-2">
              {dockState === "idle" && (
                <>
                  <button
                    onClick={pickImage}
                    disabled={noChat}
                    aria-label="Attach photo"
                    className={ICON_BTN}
                  >
                    <Paperclip className="h-4.5 w-4.5" />
                  </button>
                  <input
                    ref={inputRef}
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") sendCurrentText();
                    }}
                    placeholder={placeholder}
                    aria-label="Message"
                    disabled={noChat}
                    className="min-w-0 flex-1 bg-transparent px-3 py-2.5 text-[15px] text-(--servio-text) placeholder-(--servio-muted) outline-none disabled:opacity-50"
                  />
                  {text.trim().length > 0 ? (
                    <button
                      onClick={sendCurrentText}
                      disabled={noChat}
                      aria-label="Send request"
                      className={SEND_BTN}
                    >
                      <Send className="h-5 w-5" />
                    </button>
                  ) : (
                    <button
                      onClick={startRecording}
                      disabled={noChat}
                      aria-label="Start recording"
                      className={ICON_BTN}
                    >
                      <Mic className="h-5 w-5" />
                    </button>
                  )}
                </>
              )}

              {dockState === "recording" && (
                <>
                  <button
                    onClick={() => finishRecording(false)}
                    aria-label="Cancel recording"
                    className={ICON_BTN}
                  >
                    <Trash2 className="h-4.5 w-4.5" />
                  </button>

                  <div className="flex min-w-0 flex-1 items-center gap-3 px-1">
                    <span className="relative flex h-2.5 w-2.5 shrink-0">
                      <span
                        className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${nearLimit ? "bg-red-400" : "bg-amber-400"}`}
                      />
                      <span
                        className={`relative inline-flex h-2.5 w-2.5 rounded-full ${nearLimit ? "bg-red-500" : "bg-amber-500"}`}
                      />
                    </span>

                    <div className="flex h-9 flex-1 items-center gap-0.75 overflow-hidden">
                      {Array.from({ length: BAR_COUNT }).map((_, i) => (
                        <div
                          key={i}
                          ref={(el) => {
                            barRefs.current[i] = el;
                          }}
                          className="h-full w-0.75 shrink-0 origin-center rounded-full"
                          style={{
                            transform: "scaleY(0.12)",
                            background:
                              "linear-gradient(to top, #f5a623, #fde68a)",
                          }}
                        />
                      ))}
                    </div>

                    <span
                      className={`shrink-0 font-mono text-xs tabular-nums ${nearLimit ? "text-red-500" : "text-(--servio-muted)"}`}
                    >
                      {formatTime(elapsed)}
                    </span>
                  </div>

                  <button
                    onClick={() => finishRecording(true)}
                    aria-label="Stop recording"
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-(--servio-warn) text-white shadow-sm transition active:scale-90"
                  >
                    <Square className="h-4 w-4 fill-white" />
                  </button>
                </>
              )}

              {dockState === "audio-preview" && (
                <>
                  <button
                    onClick={discardRecording}
                    aria-label="Discard recording"
                    className={ICON_BTN}
                  >
                    <Trash2 className="h-4.5 w-4.5" />
                  </button>

                  <button
                    onClick={togglePlay}
                    aria-label={isPlaying ? "Pause preview" : "Play preview"}
                    className={ICON_BTN}
                  >
                    {isPlaying ? (
                      <Pause className="h-4.5 w-4.5" />
                    ) : (
                      <Play className="h-4.5 w-4.5 pl-0.5" />
                    )}
                  </button>

                  <div className="flex min-w-0 flex-1 items-center gap-3 px-1">
                    <div className="flex h-9 flex-1 items-center gap-0.75 overflow-hidden opacity-60">
                      {Array.from({ length: BAR_COUNT }).map((_, i) => (
                        <div
                          key={i}
                          className="h-full w-0.75 shrink-0 rounded-full bg-(--servio-primary)/50"
                          style={{
                            transform: `scaleY(${0.2 + ((i * 37) % 60) / 100})`,
                          }}
                        />
                      ))}
                    </div>
                    <span className="shrink-0 font-mono text-xs tabular-nums text-(--servio-muted)">
                      {formatTime(recordedDuration)}
                    </span>
                  </div>

                  <button
                    onClick={sendVoice}
                    aria-label="Send voice request"
                    className={SEND_BTN}
                  >
                    <Send className="h-5 w-5" />
                  </button>
                </>
              )}

              {dockState === "image-preview" && (
                <>
                  <button
                    onClick={discardImage}
                    aria-label="Discard photo"
                    className={ICON_BTN}
                  >
                    <Trash2 className="h-4.5 w-4.5" />
                  </button>

                  {imagePreviewUrl && (
                    <div className="relative h-11 w-11 shrink-0 overflow-hidden rounded-xl border border-(--servio-border)">
                      <img
                        src={imagePreviewUrl}
                        alt="Selected photo preview"
                        className="h-full w-full object-cover"
                      />
                      <button
                        onClick={discardImage}
                        aria-label="Remove photo"
                        className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-(--servio-text) text-white"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  )}

                  <input
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") sendCurrentImage();
                    }}
                    placeholder="Add a caption (optional)"
                    aria-label="Photo caption"
                    className="min-w-0 flex-1 bg-transparent px-3 py-2.5 text-[15px] text-(--servio-text) placeholder-(--servio-muted) outline-none"
                  />

                  <button
                    onClick={sendCurrentImage}
                    aria-label="Send photo"
                    className={SEND_BTN}
                  >
                    <Send className="h-5 w-5" />
                  </button>
                </>
              )}
            </div>

            {justSent && (
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center rounded-3xl bg-(--servio-surface)/85 backdrop-blur-sm">
                <span className="text-sm font-medium text-(--servio-success)">
                  Request sent
                </span>
              </div>
            )}
          </div>

          {dockState === "idle" && !noChat && (
            <p className="mt-1.5 px-3 text-center text-[11px] text-(--servio-muted)">
              Type your request, tap the mic to speak, or attach a photo
            </p>
          )}
          {dockState === "recording" && (
            <p className="mt-1.5 px-3 text-center text-[11px] text-(--servio-muted)">
              Tap the square to send, or the trash to cancel
            </p>
          )}
          {dockState === "image-preview" && (
            <p className="mt-1.5 px-3 text-center text-[11px] text-(--servio-muted)">
              Add a caption or send the photo as-is
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default VoiceRecorder;
