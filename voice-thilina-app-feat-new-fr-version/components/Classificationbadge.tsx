"use client";
import { useState } from "react";
import {
  Wrench,
  AlertCircle,
  Siren,
  ChevronDown,
  Sparkles,
  HelpCircle,
  Tag,
  ScanEye,
} from "lucide-react";

export type IntentCode =
  | "request_service"
  | "report_issue"
  | "emergency_request";
export type UrgencyLevel = "low" | "medium" | "high";

export interface Classification {
  intent: IntentCode;
  service_type: string;
  urgency: UrgencyLevel;
  intent_confidence?: number;
  service_confidence?: number;
  urgency_confidence?: number;
  /** True while the backend is still asking a clarifying question rather
   * than committing to this as a final answer — the badge below is a
   * best-guess-so-far, not a confirmed result. */
  needs_clarification?: boolean;
  /** Image-recognition fields (present only for photo messages). `vision_subtype`
   * is the routing-critical detail — e.g. "lorry_truck" vs "car". */
  vision_object_type?: string;
  vision_subtype?: string | null;
  vision_conditions?: string[];
  /** "clip_zero_shot" (local) or "gemini_fallback". */
  recognition_source?: string;
}

function humanizeLabel(s: string) {
  return s.replace(/_/g, " ");
}

const INTENT_CONFIG: Record<
  IntentCode,
  { label: string; icon: typeof Wrench; classes: string }
> = {
  request_service: {
    label: "Service request",
    icon: Wrench,
    classes: "border-blue-200 bg-blue-50 text-blue-700",
  },
  report_issue: {
    label: "Issue report",
    icon: AlertCircle,
    classes: "border-violet-200 bg-violet-50 text-violet-700",
  },
  emergency_request: {
    label: "Emergency",
    icon: Siren,
    classes: "border-rose-200 bg-rose-50 text-rose-700",
  },
};

const URGENCY_CONFIG: Record<
  UrgencyLevel,
  { label: string; dot: string; classes: string; pulse: boolean }
> = {
  low: {
    label: "Low",
    dot: "bg-emerald-500",
    classes: "border-emerald-200 bg-emerald-50 text-emerald-700",
    pulse: false,
  },
  medium: {
    label: "Medium",
    dot: "bg-amber-500",
    classes: "border-amber-200 bg-amber-50 text-amber-700",
    pulse: false,
  },
  high: {
    label: "High",
    dot: "bg-rose-500",
    classes: "border-rose-200 bg-rose-50 text-rose-700",
    pulse: true,
  },
};

function pct(n: number) {
  return `${Math.round(n * 100)}%`;
}

function ConfidenceRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2 text-[11px]">
      <span className="w-14 shrink-0 text-(--servio-muted)">{label}</span>
      <div className="h-1 flex-1 overflow-hidden rounded-full bg-(--servio-border)">
        <div
          className="h-full rounded-full bg-(--servio-primary)"
          style={{ width: pct(value) }}
        />
      </div>
      <span className="w-8 shrink-0 text-right text-(--servio-muted)">
        {pct(value)}
      </span>
    </div>
  );
}

export function ClassificationBadge({
  classification,
}: {
  classification: Classification;
}) {
  const provisional = !!classification.needs_clarification;
  // Auto-expand so the specific low-confidence field is visible without a
  // click while the answer is still provisional — collapsed is the default
  // once it's a final, confident answer.
  const [open, setOpen] = useState(provisional);
  const intent = INTENT_CONFIG[classification.intent];
  const urgency = URGENCY_CONFIG[classification.urgency];
  const IntentIcon = intent.icon;
  const isEmergency = classification.intent === "emergency_request";
  const hasConfidence =
    classification.intent_confidence !== undefined ||
    classification.service_confidence !== undefined ||
    classification.urgency_confidence !== undefined;

  const conditions = (classification.vision_conditions ?? []).filter(
    (c) => c && c !== "no_visible_problem",
  );
  const hasVisionRow =
    conditions.length > 0 || classification.recognition_source !== undefined;

  return (
    <div
      className={`overflow-hidden rounded-2xl border ${
        provisional
          ? "border-dashed border-(--servio-primary)/40 bg-(--servio-primary-soft)/40"
          : "border-(--servio-border) bg-(--servio-surface)"
      }`}
    >
      {isEmergency && (
        <div className="flex items-center gap-1.5 bg-(--servio-danger) px-3 py-1.5 text-[11px] font-medium text-white">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white opacity-75" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-white" />
          </span>
          Flagged urgent
        </div>
      )}

      {provisional && (
        <div className="flex items-center gap-1.5 bg-(--servio-surface-2) px-3 py-1.5 text-[11px] font-medium text-(--servio-muted)">
          <HelpCircle className="h-3 w-3 shrink-0" />
          Still confirming — best guess so far
        </div>
      )}

      <button
        onClick={() => hasConfidence && setOpen((v) => !v)}
        className={`flex w-full flex-wrap items-center gap-1.5 px-3 py-2 text-left ${
          provisional ? "opacity-70" : ""
        }`}
      >
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${intent.classes}`}
        >
          <IntentIcon className="h-3 w-3" />
          {intent.label}
        </span>

        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${urgency.classes}`}
        >
          <span className="relative flex h-1.5 w-1.5">
            {urgency.pulse && (
              <span
                className={`absolute inline-flex h-full w-full animate-ping rounded-full ${urgency.dot} opacity-75`}
              />
            )}
            <span
              className={`relative inline-flex h-1.5 w-1.5 rounded-full ${urgency.dot}`}
            />
          </span>
          {urgency.label} urgency
        </span>

        <span className="text-[11px] text-(--servio-muted)">
          {classification.service_type}
        </span>

        {classification.vision_subtype && (
          <span className="inline-flex items-center gap-1 rounded-full border border-(--servio-border) bg-(--servio-surface-2) px-2 py-1 text-[11px] font-medium text-(--servio-text)">
            <Tag className="h-3 w-3" />
            {humanizeLabel(classification.vision_subtype)}
          </span>
        )}

        {hasConfidence && (
          <ChevronDown
            className={`ml-auto h-3.5 w-3.5 shrink-0 text-(--servio-muted) transition-transform ${open ? "rotate-180" : ""}`}
          />
        )}
      </button>

      {hasVisionRow && (
        <div className="flex flex-wrap items-center gap-1 border-t border-(--servio-border) px-3 py-2">
          {conditions.map((c) => (
            <span
              key={c}
              className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] text-amber-700"
            >
              {humanizeLabel(c)}
            </span>
          ))}
          {classification.recognition_source && (
            <span className="ml-auto inline-flex items-center gap-1 text-[10px] text-(--servio-muted)">
              <ScanEye className="h-3 w-3" />
              {classification.recognition_source === "gemini_fallback"
                ? "confirmed via Gemini"
                : "recognised locally"}
            </span>
          )}
        </div>
      )}

      {open && hasConfidence && (
        <div className="space-y-1.5 border-t border-(--servio-border) px-3 py-2.5">
          <div className="mb-0.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-(--servio-muted)">
            <Sparkles className="h-3 w-3" /> Confidence
          </div>
          {classification.intent_confidence !== undefined && (
            <ConfidenceRow
              label="Intent"
              value={classification.intent_confidence}
            />
          )}
          {classification.service_confidence !== undefined && (
            <ConfidenceRow
              label="Service"
              value={classification.service_confidence}
            />
          )}
          {classification.urgency_confidence !== undefined && (
            <ConfidenceRow
              label="Urgency"
              value={classification.urgency_confidence}
            />
          )}
        </div>
      )}
    </div>
  );
}
