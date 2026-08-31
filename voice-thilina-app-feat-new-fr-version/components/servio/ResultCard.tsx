"use client";
import { useState } from "react";
import {
  Wrench,
  Siren,
  AlertCircle,
  ChevronDown,
  Eye,
  Sparkles,
  ShieldCheck,
} from "lucide-react";
import type { Message } from "../Usechatsession";
import type { Classification } from "./types";
import { useRequestLocale } from "./request-i18n";
import {
  serviceTypeLabel,
  visionObjectTypeLabel,
  visionSubtypeLabel,
  visionConditionLabel,
  urgencyPhraseLabel,
  intentLabel,
} from "./classification-si";
import { toneVar } from "./ui/tone";
import Card from "./ui/Card";
import ConfidenceBar from "./ui/ConfidenceBar";

export default function ResultCard({ message }: { message: Message }) {
  const [open, setOpen] = useState(false);
  const { t, locale } = useRequestLocale();
  const c = message.classification as Classification | null;

  // "Couldn't understand" fallback — no classification was produced.
  if (!c) {
    return (
      <Card>
        <div className="flex items-center gap-2 text-(--servio-warn)">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm font-semibold">{t("couldntRead")}</span>
        </div>
        <p className="mt-2 text-sm text-(--servio-text)">{message.content}</p>
        {message.translation && (
          <p className="mt-1 text-sm text-(--servio-muted)">
            {message.translation}
          </p>
        )}
      </Card>
    );
  }

  const isEmergency =
    c.intent === "emergency_request" || c.intent === "emergency";
  const urgencyLabel = urgencyPhraseLabel(locale, c.urgency);
  const urgencyTone = toneVar(c.urgency);
  const conditions: string[] = (c.vision_conditions ?? []).filter(
    (x) => x && x !== "no_visible_problem",
  );
  const hasVision = !!c.vision_object_type || !!c.vision_subtype;
  const hasConf =
    c.intent_confidence !== undefined ||
    c.service_confidence !== undefined ||
    c.urgency_confidence !== undefined;

  return (
    <div className="overflow-hidden rounded-2xl border border-(--servio-border) bg-(--servio-surface) shadow-(--servio-shadow)">
      {isEmergency && (
        <div className="flex items-center gap-2 bg-(--servio-danger) px-5 py-2 text-xs font-semibold text-white">
          <Siren className="h-3.5 w-3.5" /> {t("emergencyFlag")}
        </div>
      )}

      <div className="p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-(--servio-muted)">
          {t("recommendedService")}
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 text-xl font-bold text-(--servio-text)">
            <Wrench className="h-5 w-5 text-(--servio-primary)" />
            {serviceTypeLabel(locale, c.service_type)}
          </span>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          <span
            className="rounded-full px-2.5 py-1 text-xs font-medium text-white"
            style={{ background: urgencyTone }}
          >
            {urgencyLabel}
          </span>
          <span className="rounded-full border border-(--servio-border) bg-(--servio-surface-2) px-2.5 py-1 text-xs font-medium text-(--servio-text)">
            {intentLabel(locale, c.intent)}
          </span>
          {c.vision_subtype && (
            <span className="rounded-full border border-(--servio-border) bg-(--servio-surface-2) px-2.5 py-1 text-xs font-medium text-(--servio-text)">
              {visionSubtypeLabel(locale, c.vision_subtype)}
            </span>
          )}
        </div>

        {hasVision && (
          <div className="mt-4 rounded-xl bg-(--servio-surface-2) p-3">
            <p className="flex items-center gap-1.5 text-xs font-semibold text-(--servio-muted)">
              <Eye className="h-3.5 w-3.5" /> {t("whatWeSawPhoto")}
            </p>
            <p className="mt-1 text-sm text-(--servio-text)">
              {[
                visionObjectTypeLabel(locale, c.vision_object_type),
                visionSubtypeLabel(locale, c.vision_subtype),
              ]
                .filter(Boolean)
                .join(" · ") || "—"}
            </p>
            {conditions.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {conditions.map((cond) => (
                  <span
                    key={cond}
                    className="rounded-full bg-(--servio-primary-soft) px-2 py-0.5 text-[11px] text-(--servio-primary)"
                  >
                    {visionConditionLabel(locale, cond)}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {hasConf && (
          <button
            onClick={() => setOpen((v) => !v)}
            className="servio-focus mt-4 flex items-center gap-1.5 rounded-md text-xs font-medium text-(--servio-muted) transition hover:text-(--servio-text)"
          >
            <Sparkles className="h-3.5 w-3.5" />
            {t("confidence")}
            <ChevronDown
              className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`}
            />
          </button>
        )}
        {open && hasConf && (
          <div className="mt-2 flex flex-col gap-1.5">
            <ConfidenceBar label={t("confServiceType")} value={c.service_confidence} emphasize />
            <ConfidenceBar label={t("urgency")} value={c.urgency_confidence} emphasize />
            <ConfidenceBar label={t("confIntent")} value={c.intent_confidence} emphasize />
          </div>
        )}

        {c.recognition_source && (
          <p className="mt-4 flex items-center gap-1.5 text-[11px] text-(--servio-muted)">
            <ShieldCheck className="h-3 w-3" />
            {c.recognition_source === "gemini_fallback"
              ? t("geminiDoubleChecked")
              : t("onDeviceRecognised")}
          </p>
        )}
      </div>
    </div>
  );
}
