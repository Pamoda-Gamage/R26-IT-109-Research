"use client";
import { useState } from "react";
import {
  FlaskConical,
  ChevronDown,
  Copy,
  Check,
  ArrowLeftRight,
  Clock,
  History,
  Code2,
} from "lucide-react";
import type { Message } from "../Usechatsession";
import type { Classification } from "./types";
import type { StageTiming } from "../hooks/useServiceRequest";
import { useRequestLocale } from "./request-i18n";
import Card from "./ui/Card";
import ConfidenceBar from "./ui/ConfidenceBar";
import CandidateList from "./ui/CandidateList";

/**
 * Technical/debug companion to UnderstandingCard — full confidence
 * distributions, provenance, clarification-round history, per-stage timing,
 * and a raw-JSON export. Collapsed by default so it doesn't clutter the
 * friendly end-user flow; opt in by researchers/developers only. Its content
 * intentionally stays English-only (raw field names, percentages, JSON) even
 * in Sinhala mode — see request-i18n.tsx's `researchData` key, the one string
 * here that IS translated.
 */

function titleize(s?: string | null) {
  return (s ?? "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function SectionHeading({
  icon: Icon,
  children,
}: {
  icon: typeof FlaskConical;
  children: React.ReactNode;
}) {
  return (
    <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-(--servio-muted)">
      <Icon className="h-3.5 w-3.5" /> {children}
    </p>
  );
}

function Chip({ tone = "default", children }: { tone?: "default" | "warn"; children: React.ReactNode }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
        tone === "warn"
          ? "bg-(--servio-danger)/10 text-(--servio-danger)"
          : "bg-(--servio-surface-2) text-(--servio-muted)"
      }`}
    >
      {children}
    </span>
  );
}

function ConfidenceSection({ c }: { c: Classification }) {
  const agreement =
    c.service_type && c.vision_service_type
      ? c.service_type === c.vision_service_type
      : null;

  return (
    <div className="flex flex-col gap-3.5">
      <div className="flex flex-col gap-1.5">
        <SectionHeading icon={FlaskConical}>Intent</SectionHeading>
        {c.intent_candidates?.length ? (
          <CandidateList items={c.intent_candidates} />
        ) : (
          <ConfidenceBar label={c.intent ?? "—"} value={c.intent_confidence} emphasize />
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <SectionHeading icon={FlaskConical}>Service type</SectionHeading>
        {c.service_candidates?.length ? (
          <CandidateList items={c.service_candidates} />
        ) : (
          <ConfidenceBar label={c.service_type ?? "—"} value={c.service_confidence} emphasize />
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <SectionHeading icon={FlaskConical}>Urgency</SectionHeading>
        {c.urgency_candidates?.length ? (
          <CandidateList items={c.urgency_candidates} />
        ) : (
          <ConfidenceBar label={c.urgency ?? "—"} value={c.urgency_confidence} emphasize />
        )}
      </div>

      <div className="flex flex-wrap gap-1.5">
        {c.recognition_source && <Chip>source: {c.recognition_source}</Chip>}
        {c.needs_clarification !== undefined && (
          <Chip>needs_clarification: {String(c.needs_clarification)}</Chip>
        )}
        {(c.fallback_reasons ?? []).map((r) => (
          <Chip key={r} tone="warn">
            {r}
          </Chip>
        ))}
      </div>

      {(c.vision_service_type ||
        c.vision_object_type_confidence !== undefined ||
        c.vision_service_type_confidence !== undefined) && (
        <div className="rounded-lg bg-(--servio-surface-2) p-2.5">
          <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold text-(--servio-muted)">
            <ArrowLeftRight className="h-3 w-3" /> Text vs vision service_type
            {agreement !== null && (
              <Chip tone={agreement ? "default" : "warn"}>
                {agreement ? "agree" : "disagree"}
              </Chip>
            )}
          </p>
          <div className="flex flex-col gap-1 text-[11px] text-(--servio-text)">
            <span>text: {titleize(c.service_type) || "—"}</span>
            <span>vision: {titleize(c.vision_service_type) || "—"}</span>
            {c.vision_suggested_service_type && (
              <span>vision suggested: {titleize(c.vision_suggested_service_type)}</span>
            )}
          </div>
          <div className="mt-1.5 flex flex-col gap-1">
            <ConfidenceBar label="vision object_type" value={c.vision_object_type_confidence} />
            <ConfidenceBar label="vision service_type" value={c.vision_service_type_confidence} />
          </div>
          {c.vision_object_type_top2_margin !== undefined && (
            <p className="mt-1 text-[11px] text-(--servio-muted)">
              object_type top2_margin: {c.vision_object_type_top2_margin.toFixed(3)}
            </p>
          )}
        </div>
      )}

      {(c.model_info || c.confidence_thresholds || c.clarification_limits) && (
        <div className="flex flex-col gap-1 border-t border-(--servio-border) pt-2.5 text-[11px] text-(--servio-muted)">
          {c.model_info && (
            <p>
              model: {c.model_info.embedder} · {c.model_info.classifier}
              {c.model_info.vision_primary ? ` · vision: ${c.model_info.vision_primary}` : ""}
              {c.model_info.vision_fallback ? ` (fallback: ${c.model_info.vision_fallback})` : ""}
            </p>
          )}
          {c.confidence_thresholds && (
            <p>
              thresholds:{" "}
              {Object.entries(c.confidence_thresholds)
                .map(([k, v]) => `${k}=${v}`)
                .join(", ")}
            </p>
          )}
          {c.clarification_limits && (
            <p>
              clarification rounds: {c.clarification_limits.used} / {c.clarification_limits.max}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

interface RoundEntry {
  round: number;
  backendRound?: number;
  question: string | null;
  questionTranslation: string | null;
  classification: Classification;
}

function buildRoundHistory(messages: Message[]): RoundEntry[] {
  const rounds: RoundEntry[] = [];
  let seq = 0;
  for (const m of messages) {
    if (m.sender !== "assistant") continue;
    const c = m.classification as Classification | null;
    if (!c?.needs_clarification) continue;
    seq += 1;
    rounds.push({
      round: seq,
      backendRound: c.clarification_round,
      question: m.content,
      questionTranslation: m.translation ?? null,
      classification: c,
    });
  }
  return rounds;
}

function RoundHistorySection({ messages }: { messages: Message[] }) {
  const rounds = buildRoundHistory(messages);
  if (rounds.length === 0) {
    return (
      <p className="text-[12px] text-(--servio-muted)">
        No clarifying rounds in this case yet.
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-2.5">
      {rounds.map((r) => (
        <div key={r.round} className="rounded-lg border border-(--servio-border) p-2.5">
          <p className="text-[11px] font-semibold text-(--servio-muted)">
            Round {r.round}
            {r.backendRound !== undefined && ` (backend clarification_round: ${r.backendRound})`}
          </p>
          {r.question && (
            <p className="mt-1 text-[12px] text-(--servio-text)">{r.question}</p>
          )}
          {r.questionTranslation && r.questionTranslation !== r.question && (
            <p className="mt-0.5 text-[12px] italic text-(--servio-muted)">
              {r.questionTranslation}
            </p>
          )}
          <p className="mt-1 text-[11px] text-(--servio-muted)">
            at that point: {titleize(r.classification.service_type) || "—"} ·{" "}
            {titleize(r.classification.urgency) || "—"} ·{" "}
            {titleize(r.classification.intent) || "—"}
          </p>
        </div>
      ))}
    </div>
  );
}

function TimingSection({ timings }: { timings: StageTiming[] }) {
  if (timings.length === 0) {
    return (
      <p className="text-[12px] text-(--servio-muted)">
        No stage events recorded for this case yet.
      </p>
    );
  }
  const total = timings[timings.length - 1].ts - timings[0].ts;
  return (
    <div className="flex flex-col gap-1">
      {timings.map((ev, i) => {
        const prev = timings[i - 1];
        const deltaMs = prev ? ev.ts - prev.ts : 0;
        return (
          <div key={i} className="flex items-center justify-between text-[12px]">
            <span className="text-(--servio-text)">
              {ev.stage} <span className="text-(--servio-muted)">· {ev.state}</span>
            </span>
            <span className="tabular-nums text-(--servio-muted)">
              {i === 0 ? "—" : `+${deltaMs}ms`}
            </span>
          </div>
        );
      })}
      <div className="mt-1 flex items-center justify-between border-t border-(--servio-border) pt-1 text-[12px] font-semibold">
        <span className="text-(--servio-text)">Total</span>
        <span className="tabular-nums text-(--servio-text)">{total}ms</span>
      </div>
    </div>
  );
}

function RawJsonSection({ classification }: { classification: Classification | null }) {
  const [copied, setCopied] = useState(false);
  if (!classification) {
    return <p className="text-[12px] text-(--servio-muted)">No classification yet.</p>;
  }
  const json = JSON.stringify(classification, null, 2);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API unavailable (permissions/non-HTTPS) — button just won't confirm.
    }
  };
  return (
    <div>
      <button
        type="button"
        onClick={copy}
        className="servio-focus mb-1.5 inline-flex items-center gap-1.5 rounded-md border border-(--servio-border) px-2 py-1 text-[11px] font-medium text-(--servio-muted) transition hover:text-(--servio-text)"
      >
        {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
        {copied ? "Copied" : "Copy JSON"}
      </button>
      <pre className="max-h-64 overflow-auto rounded-lg bg-(--servio-surface-2) p-2.5 text-[11px] leading-relaxed text-(--servio-text)">
        {json}
      </pre>
    </div>
  );
}

export default function ResearchPanel({
  classification,
  messages,
  stageTimings,
  embedded = false,
}: {
  classification: Classification | null;
  messages: Message[];
  stageTimings: StageTiming[];
  /** Rendered as a dedicated tab panel — drop the collapse toggle and show the
   * body expanded. */
  embedded?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const { t } = useRequestLocale();
  const showBody = embedded || open;

  const body = (
    <div className={`flex flex-col gap-5 px-1.5 pb-1 ${embedded ? "" : "mt-3"}`}>
      {classification ? (
        <ConfidenceSection c={classification} />
      ) : (
        <p className="text-[12px] text-(--servio-muted)">No classification yet.</p>
      )}

      <div className="flex flex-col gap-1.5">
        <SectionHeading icon={History}>Clarification round history</SectionHeading>
        <RoundHistorySection messages={messages} />
      </div>

      <div className="flex flex-col gap-1.5">
        <SectionHeading icon={Clock}>Timing</SectionHeading>
        <TimingSection timings={stageTimings} />
      </div>

      <div className="flex flex-col gap-1.5">
        <SectionHeading icon={Code2}>Raw data</SectionHeading>
        <RawJsonSection classification={classification} />
      </div>
    </div>
  );

  return (
    <Card padding="tight">
      {embedded ? (
        <div className="flex items-center gap-1.5 px-1.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-(--servio-muted)">
          <FlaskConical className="h-3.5 w-3.5" /> {t("researchData")}
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="servio-focus flex w-full items-center justify-between rounded-lg px-1.5 py-1 text-left"
        >
          <span className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-(--servio-muted)">
            <FlaskConical className="h-3.5 w-3.5" /> {t("researchData")}
          </span>
          <ChevronDown
            className={`h-3.5 w-3.5 text-(--servio-muted) transition-transform ${open ? "rotate-180" : ""}`}
          />
        </button>
      )}

      {showBody && body}
    </Card>
  );
}
