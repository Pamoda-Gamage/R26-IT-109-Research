"use client";
import { useState } from "react";
import {
  Mic,
  Send,
  Square,
  Trash2,
  Play,
  Pause,
  Paperclip,
  AlertCircle,
} from "lucide-react";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { useImagePicker } from "../hooks/useImagePicker";
import type { SubmitPayload } from "../hooks/useServiceRequest";
import { useRequestLocale } from "./request-i18n";

function fmt(sec: number) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const btn =
  "servio-focus flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition active:scale-95 disabled:opacity-40";

export default function RequestComposer({
  onSubmit,
  disabled = false,
  compact = false,
}: {
  onSubmit: (p: SubmitPayload) => void;
  disabled?: boolean;
  /** compact hides the photo attachment (used for clarifying replies). */
  compact?: boolean;
}) {
  const rec = useAudioRecorder();
  const pic = useImagePicker();
  const [text, setText] = useState("");
  const { t } = useRequestLocale();

  const sendText = () => {
    const val = text.trim();
    if (!val) return;
    setText("");
    onSubmit({ kind: "text", text: val });
  };
  const sendAudio = () => {
    if (!rec.blob) return;
    const blob = rec.blob;
    rec.discard();
    onSubmit({ kind: "audio", blob });
  };
  const sendImage = () => {
    if (!pic.file) return;
    const file = pic.file;
    const caption = text.trim();
    setText("");
    pic.discard();
    onSubmit({ kind: "image", file, caption });
  };

  return (
    <div>
      {rec.permissionError && (
        <div className="mb-2 flex items-center gap-2 rounded-xl border border-(--servio-danger)/30 bg-(--servio-danger)/5 px-3 py-2 text-xs text-(--servio-danger)">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {t("micPermissionDenied")}
        </div>
      )}

      <input {...pic.inputProps} />

      <div className="rounded-2xl border border-(--servio-border) bg-(--servio-surface) p-2 shadow-(--servio-shadow)">
        {/* ---- image selected ---- */}
        {pic.file ? (
          <div className="flex items-center gap-2">
            <button
              onClick={pic.discard}
              aria-label={t("ariaRemovePhoto")}
              className={`${btn} border border-(--servio-border) text-(--servio-muted)`}
            >
              <Trash2 className="h-4.5 w-4.5" />
            </button>
            {pic.previewUrl && (
              <span className="relative h-11 w-11 shrink-0 overflow-hidden rounded-lg border border-(--servio-border)">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={pic.previewUrl}
                  alt="Selected"
                  className="h-full w-full object-cover"
                />
              </span>
            )}
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendImage()}
              placeholder={t("placeholderPhotoNote")}
              className="servio-focus min-w-0 flex-1 rounded-lg bg-transparent px-2 py-2.5 text-sm text-(--servio-text) outline-none placeholder:text-(--servio-muted)"
            />
            <button
              onClick={sendImage}
              disabled={disabled}
              aria-label={t("ariaSendPhoto")}
              className={`${btn} bg-(--servio-primary) text-white`}
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        ) : rec.state === "recording" ? (
          /* ---- recording ---- */
          <div className="flex items-center gap-2">
            <button
              onClick={() => rec.stop(false)}
              aria-label={t("ariaCancelRecording")}
              className={`${btn} border border-(--servio-border) text-(--servio-muted)`}
            >
              <Trash2 className="h-4.5 w-4.5" />
            </button>
            <div className="flex h-9 min-w-0 flex-1 items-center gap-[3px] overflow-hidden px-1">
              {rec.bars.map((v, i) => (
                <span
                  key={i}
                  className="w-[3px] shrink-0 origin-center rounded-full bg-(--servio-primary)"
                  style={{ transform: `scaleY(${v})` }}
                />
              ))}
            </div>
            <span className="shrink-0 font-mono text-xs tabular-nums text-(--servio-muted)">
              {fmt(rec.elapsed)}
            </span>
            <button
              onClick={() => rec.stop(true)}
              aria-label={t("ariaStopRecording")}
              className={`${btn} bg-(--servio-primary) text-white`}
            >
              <Square className="h-4 w-4 fill-white" />
            </button>
          </div>
        ) : rec.state === "preview" ? (
          /* ---- audio preview ---- */
          <div className="flex items-center gap-2">
            <button
              onClick={rec.discard}
              aria-label={t("ariaDiscardRecording")}
              className={`${btn} border border-(--servio-border) text-(--servio-muted)`}
            >
              <Trash2 className="h-4.5 w-4.5" />
            </button>
            <button
              onClick={rec.togglePlay}
              aria-label={rec.isPlaying ? t("ariaPause") : t("ariaPlay")}
              className={`${btn} border border-(--servio-border) text-(--servio-text)`}
            >
              {rec.isPlaying ? (
                <Pause className="h-4.5 w-4.5" />
              ) : (
                <Play className="h-4.5 w-4.5 pl-0.5" />
              )}
            </button>
            <span className="flex-1 text-sm text-(--servio-muted)">
              {t("voiceNote", { time: fmt(rec.elapsed) })}
            </span>
            <button
              onClick={sendAudio}
              disabled={disabled}
              aria-label={t("ariaSendVoice")}
              className={`${btn} bg-(--servio-primary) text-white`}
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        ) : (
          /* ---- idle ---- */
          <div className="flex items-center gap-2">
            {!compact && (
              <button
                onClick={pic.pick}
                disabled={disabled}
                aria-label={t("ariaAttachPhoto")}
                className={`${btn} border border-(--servio-border) text-(--servio-text)`}
              >
                <Paperclip className="h-4.5 w-4.5" />
              </button>
            )}
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendText()}
              placeholder={
                compact ? t("placeholderAnswer") : t("placeholderDescribe")
              }
              disabled={disabled}
              className="servio-focus min-w-0 flex-1 rounded-lg bg-transparent px-3 py-2.5 text-sm text-(--servio-text) outline-none placeholder:text-(--servio-muted) disabled:opacity-50"
            />
            {text.trim() ? (
              <button
                onClick={sendText}
                disabled={disabled}
                aria-label={t("ariaSendRequest")}
                className={`${btn} bg-(--servio-primary) text-white`}
              >
                <Send className="h-5 w-5" />
              </button>
            ) : (
              <button
                onClick={rec.start}
                disabled={disabled}
                aria-label={t("ariaRecordVoice")}
                className={`${btn} bg-(--servio-primary) text-white`}
              >
                <Mic className="h-5 w-5" />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
