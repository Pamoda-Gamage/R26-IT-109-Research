"use client";
import { Check, Loader2, AlertTriangle } from "lucide-react";
import type { Step } from "../hooks/useServiceRequest";
import type { Message } from "../Usechatsession";
import type { Classification } from "./types";
import { useRequestLocale } from "./request-i18n";

function titleize(s?: string | null) {
  return (s ?? "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/** A short one-liner shown under a finished step. */
function stepValue(
  key: string,
  ctx: { userMessage?: Message; classification: Classification | null },
): string | null {
  const { userMessage, classification: c } = ctx;
  if (
    (key === "transcribing" || key === "translating") &&
    userMessage?.translation
  ) {
    return userMessage.translation;
  }
  if (key === "classifying" && c?.service_type) {
    return [
      titleize(c.service_type),
      c.urgency ? `${titleize(c.urgency)} urgency` : null,
    ]
      .filter(Boolean)
      .join(" · ");
  }
  return null;
}

function Bullet({ status }: { status: Step["status"] }) {
  const base =
    "relative flex h-6 w-6 shrink-0 items-center justify-center rounded-full";
  if (status === "done")
    return (
      <span className={`${base} bg-(--servio-success) text-white`}>
        <Check className="h-3.5 w-3.5" />
      </span>
    );
  if (status === "active")
    return (
      <span className={`${base} servio-ping bg-(--servio-primary) text-white`}>
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      </span>
    );
  if (status === "error")
    return (
      <span className={`${base} bg-(--servio-danger) text-white`}>
        <AlertTriangle className="h-3.5 w-3.5" />
      </span>
    );
  return (
    <span
      className={`${base} border-2 border-(--servio-border) bg-(--servio-surface)`}
    />
  );
}

export default function StepTree({
  steps,
  userMessage,
  classification,
}: {
  steps: Step[];
  userMessage?: Message;
  classification: Classification | null;
}) {
  const { t } = useRequestLocale();
  return (
    <ol className="flex flex-col">
      {steps.map((step, i) => {
        const isLast = i === steps.length - 1;
        const muted = step.status === "pending" || step.soon;
        const val =
          step.status === "done"
            ? stepValue(step.key, { userMessage, classification })
            : null;

        const box =
          step.status === "active"
            ? "border-(--servio-primary)/40 bg-(--servio-primary-soft)"
            : step.status === "done"
              ? "border-(--servio-border) bg-(--servio-surface)"
              : step.status === "error"
                ? "border-(--servio-danger)/40 bg-(--servio-danger)/5"
                : "border-transparent";

        return (
          <li key={step.key} className="flex gap-2.5">
            <div className="flex flex-col items-center">
              <Bullet status={step.status} />
              {!isLast && (
                <span
                  className={`mt-1 w-[3px] flex-1 rounded-full transition-colors duration-500 ${
                    step.status === "done"
                      ? "bg-(--servio-primary)"
                      : "bg-(--servio-border)"
                  }`}
                />
              )}
            </div>

            <div
              className={`servio-node-in mb-1.5 min-w-0 flex-1 rounded-xl border p-2.5 transition-all duration-300 ${box}`}
              style={{ animationDelay: `${i * 55}ms` }}
            >
              <p
                className={`flex items-center gap-1.5 text-[13px] font-medium leading-tight ${
                  muted ? "text-(--servio-muted)" : "text-(--servio-text)"
                }`}
              >
                {step.label}
                {step.soon && (
                  <span className="rounded-full bg-(--servio-surface-2) px-1.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-(--servio-muted)">
                    {t("stepSoonBadge")}
                  </span>
                )}
              </p>
              {step.note && (
                <p className="mt-0.5 truncate text-[11px] text-(--servio-muted)">
                  {step.note}
                </p>
              )}
              {val && (
                <p
                  className="mt-1 line-clamp-2 text-[11px] text-(--servio-muted)"
                  title={val}
                >
                  {val}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
