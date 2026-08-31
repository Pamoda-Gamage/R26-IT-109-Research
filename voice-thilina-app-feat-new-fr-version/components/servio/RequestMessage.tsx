"use client";
import { Eye } from "lucide-react";
import { API_BASE, type Message } from "../Usechatsession";
import { useRequestLocale } from "./request-i18n";

// Sinhala Unicode block.
const hasSinhala = (s: string) => /[඀-෿]/.test(s);

function Dots() {
  return (
    <span className="inline-flex gap-1 py-1">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current opacity-60 [animation-delay:-0.3s]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current opacity-60 [animation-delay:-0.15s]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current opacity-60" />
    </span>
  );
}

/**
 * One turn in the request thread — mirrors the chat view: the original text,
 * then the other-language version (English under a user's Sinhala/Tamil, සිංහල
 * under the assistant's English), and the photo + vision read for images.
 */
export default function RequestMessage({ message }: { message: Message }) {
  const { t } = useRequestLocale();
  const isUser = message.sender === "user";
  const isImage = message.type === "image";
  const processing = message.status === "processing";
  const failed = message.status === "failed";
  // Labels the actual language of `message.content`/`message.translation` —
  // genuinely bilingual backend content, distinct from the static UI chrome
  // handled by request-i18n.tsx, so this stays fixed regardless of locale.
  const translationLabel = isUser ? "English" : "සිංහල";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl border px-4 py-3 text-sm ${
          isUser
            ? "rounded-br-sm border-(--servio-primary) bg-(--servio-primary) text-white"
            : "rounded-bl-sm border-(--servio-border) bg-(--servio-surface) text-(--servio-text)"
        } ${failed ? "border-(--servio-danger)" : ""}`}
      >
        {isImage && message.media_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={`${API_BASE}${message.media_url}`}
            alt="Attached"
            className="mb-2 max-h-56 w-full rounded-lg object-cover"
          />
        )}

        {processing ? (
          <Dots />
        ) : (
          message.content && (
            <>
              {isUser && (
                <span className="mb-0.5 inline-block rounded bg-white/15 px-1 py-0.5 text-[11px] font-semibold tracking-wide">
                  {hasSinhala(message.content)
                    ? "සිංහල"
                    : message.type === "audio"
                      ? t("voiceBadge")
                      : t("youSaid")}
                </span>
              )}
              <p className="whitespace-pre-wrap break-words">
                {message.content}
              </p>
            </>
          )
        )}

        {message.translation &&
          (isImage ? (
            <div
              className={`mt-2 border-t pt-2 text-[13px] ${
                isUser
                  ? "border-white/25 text-white/85"
                  : "border-(--servio-border) text-(--servio-muted)"
              }`}
            >
              <span className="mb-0.5 flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide opacity-80">
                <Eye className="h-3 w-3" /> {t("whatWeSaw")}
              </span>
              <p className="whitespace-pre-wrap break-words">
                {message.translation}
              </p>
            </div>
          ) : (
            <p
              className={`mt-2 whitespace-pre-wrap break-words border-t pt-2 text-[13px] italic ${
                isUser
                  ? "border-white/25 text-white/85"
                  : "border-(--servio-border) text-(--servio-muted)"
              }`}
            >
              <span className="mr-1.5 rounded bg-black/10 px-1 py-0.5 text-[11px] font-semibold uppercase not-italic tracking-wide">
                {translationLabel}
              </span>
              {message.translation}
            </p>
          ))}

        {failed && (
          <p className="mt-1.5 text-[13px] text-(--servio-danger)">
            {t("failedMessage")}
          </p>
        )}
      </div>
    </div>
  );
}
