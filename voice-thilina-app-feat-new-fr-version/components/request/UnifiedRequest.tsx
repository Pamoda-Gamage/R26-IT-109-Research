"use client";
import { useCallback, useEffect, useState } from "react";
import { MapPin, Loader2, AlertCircle, RotateCcw, Sparkles, Check, Wrench } from "lucide-react";

import { useServiceRequest } from "../hooks/useServiceRequest";
import type { Message } from "../Usechatsession";
import RequestConsole from "../servio/RequestConsole";
import { serviceTypeLabel, urgencyWordLabel } from "../servio/classification-si";
import ProviderCard from "../match/ProviderCard";
import ScoreBreakdownChart from "../match/ScoreBreakdownChart";
import TraceTimeline from "../match/TraceTimeline";
import {
  submitRequest,
  submitFeedback,
  type RankedCandidate,
  type RequestResponse,
} from "@/lib/match-api";
import {
  serviceFilterPrefix,
  serviceFilterTokens,
  providerMatchesTokens,
} from "./service-type-map";

const REGIONS = ["colombo-01", "colombo-02", "dehiwala", "mount-lavinia", "kotte"];
const titleCase = (v: string) =>
  v.split("-").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");

/** Every user turn's best-available English text, joined — the narrative the
 * Provider Match `/request` endpoint is given. */
function buildCaseText(messages: Message[]): string {
  return messages
    .filter((m) => m.sender === "user")
    .map((m) => m.translation || m.content)
    .filter(Boolean)
    .join("\n")
    .trim();
}

type MatchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "done"; data: RequestResponse; note: string | null }
  | { status: "error"; error: string };

export default function UnifiedRequest() {
  const sr = useServiceRequest();
  const [region, setRegion] = useState(REGIONS[0]);
  const [match, setMatch] = useState<MatchState>({ status: "idle" });
  const [selectedRank, setSelectedRank] = useState<number | null>(null);
  const [feedbackPending, setFeedbackPending] = useState(false);

  const runMatch = useCallback(
    async (caseText: string, serviceType?: string) => {
      setMatch({ status: "loading" });
      setSelectedRank(null);
      const prefix = serviceFilterPrefix(serviceType);
      const raw_text = prefix ? `[FILTER_SERVICE_TYPE:${prefix}] ${caseText}` : caseText;
      try {
        const data = await submitRequest({
          raw_text,
          timestamp: new Date().toISOString(),
          region,
        });

        // Keyword-filter the returned providers down to the detected service —
        // the backend prefix isn't reliable for every category. If that removes
        // everything, fall back to the full list with a note.
        const tokens = serviceFilterTokens(serviceType);
        const matched = tokens.length
          ? data.ranked.filter((c) => providerMatchesTokens(c.service_type, tokens))
          : data.ranked;
        const usedFallback = tokens.length > 0 && matched.length === 0;
        const shown = (matched.length ? matched : data.ranked).map((c, i) => ({
          ...c,
          rank: i + 1,
        }));

        const label =
          (serviceType && serviceTypeLabel("en", serviceType)) ||
          serviceType?.replace(/_/g, " ") ||
          "this service";
        let note: string | null = null;
        if (usedFallback) {
          note = `No exact ${label} providers nearby — showing all closest matches.`;
        } else if (shown.length < data.ranked.length) {
          note = `Showing ${shown.length} of ${data.ranked.length} nearby — filtered to ${label}.`;
        }

        setMatch({ status: "done", data: { ...data, ranked: shown }, note });
      } catch (e) {
        setMatch({
          status: "error",
          error: e instanceof Error ? e.message : "Provider matching is unavailable right now.",
        });
      }
    },
    [region],
  );

  // The user confirmed the detected intent is correct — now search for providers.
  const confirmAndMatch = useCallback(() => {
    const c = sr.result?.classification;
    if (!c) return;
    const caseText = buildCaseText(sr.messages);
    if (!caseText) return;
    void runMatch(caseText, c.service_type);
  }, [sr.result, sr.messages, runMatch]);

  const retryMatch = confirmAndMatch;

  // When the Servio console is reset back to the composer (its own "New request"
  // button, or "Not right" below), drop any provider results too.
  useEffect(() => {
    if (sr.phase !== "compose") return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMatch((m) => (m.status === "idle" ? m : { status: "idle" }));
    setSelectedRank(null);
  }, [sr.phase]);

  const handleSelect = useCallback(
    async (candidate: RankedCandidate) => {
      if (match.status !== "done" || feedbackPending) return;
      setFeedbackPending(true);
      try {
        await submitFeedback({
          context: match.data.context_vector,
          arm_index: match.data.arm_index,
          selected_rank: candidate.rank,
        });
        setSelectedRank(candidate.rank);
      } catch {
        // Non-fatal: the pick still stands, only the reward signal was lost.
        setSelectedRank(candidate.rank);
      } finally {
        setFeedbackPending(false);
      }
    },
    [match, feedbackPending],
  );

  const classification = sr.result?.classification;
  const showConfirm =
    sr.phase === "result" && !!classification && match.status === "idle";
  const serviceText = classification?.service_type
    ? serviceTypeLabel("en", classification.service_type)
    : null;
  const urgencyText = classification?.urgency
    ? urgencyWordLabel("en", classification.urgency)
    : null;
  const caseReady = buildCaseText(sr.messages).length > 0;

  return (
    <div className="flex flex-col">
      <RequestConsole sr={sr} />

      {/* ---- Confirm the detected intent before searching ---- */}
      {showConfirm && (
        <section className="mx-auto w-full max-w-5xl px-5 pb-6">
          <div className="rounded-2xl border border-(--servio-border) bg-(--servio-surface) p-5 shadow-(--servio-shadow)">
            <p className="flex items-center gap-2 text-sm font-bold text-[#082454]">
              <Check className="h-4 w-4 text-primary" /> Is this right?
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              We understood your request as{" "}
              <span className="inline-flex items-center gap-1.5 font-semibold text-[#082454]">
                <Wrench className="h-3.5 w-3.5 text-primary" />
                {serviceText ?? classification?.service_type?.replace(/_/g, " ") ?? "a service request"}
              </span>
              {urgencyText ? <> · {urgencyText} urgency</> : null}. Confirm to find nearby providers.
            </p>

            <label className="mt-4 mb-2 flex items-center gap-2 text-sm font-bold text-[#082454]">
              <MapPin size={15} className="text-primary" /> Service location
            </label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="h-12 w-full max-w-sm rounded-xl border border-slate-200 bg-white px-3.5 text-sm font-semibold text-slate-700 shadow-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            >
              {REGIONS.map((r) => (
                <option key={r} value={r}>
                  {titleCase(r)}
                </option>
              ))}
            </select>

            <div className="mt-5 flex flex-wrap gap-3">
              <button
                onClick={confirmAndMatch}
                disabled={!caseReady}
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-[#004fae] disabled:opacity-50"
              >
                <Sparkles className="h-4 w-4" /> Yes, find providers
              </button>
              <button
                onClick={sr.reset}
                className="inline-flex items-center gap-2 rounded-xl border border-(--servio-border) bg-(--servio-surface) px-5 py-2.5 text-sm font-semibold text-(--servio-primary) transition hover:bg-(--servio-primary-soft)"
              >
                <RotateCcw className="h-4 w-4" /> Not right — start over
              </button>
            </div>
          </div>
        </section>
      )}

      {/* ---- Provider matching results ---- */}
      {match.status !== "idle" && (
        <section className="mx-auto w-full max-w-5xl px-5 pb-16">
          <div className="mb-4 flex items-center gap-2 border-t border-slate-200 pt-8">
            <Sparkles className="h-4 w-4 text-primary" />
            <h2 className="text-lg font-bold tracking-tight text-[#082454]">
              Nearby providers in {titleCase(region)}
            </h2>
          </div>

          {match.status === "loading" && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Ranking providers…
            </p>
          )}

          {match.status === "error" && (
            <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-5">
              <p className="flex items-center gap-2 text-sm font-semibold text-destructive">
                <AlertCircle className="h-4 w-4" /> {match.error}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Your request was understood — only the matching step failed.
              </p>
              <button
                onClick={retryMatch}
                className="mt-3 inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-[#004fae]"
              >
                <RotateCcw className="h-4 w-4" /> Retry matching
              </button>
            </div>
          )}

          {match.status === "done" && match.note && (
            <p className="mb-3 flex items-center gap-2 rounded-lg border border-(--servio-warn)/30 bg-(--servio-warn)/5 px-3 py-2 text-xs font-medium text-(--servio-warn)">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" /> {match.note}
            </p>
          )}

          {match.status === "done" && (
            <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
              <div className="flex flex-col gap-3">
                {match.data.ranked.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No available providers matched this request in {titleCase(region)}. Try a
                    different location or add more detail.
                  </p>
                )}
                {match.data.ranked.map((candidate) => (
                  <ProviderCard
                    key={candidate.provider_id}
                    candidate={candidate}
                    onSelect={handleSelect}
                    selected={selectedRank === candidate.rank}
                    disabled={feedbackPending || selectedRank !== null}
                  />
                ))}
              </div>
              <aside className="flex flex-col gap-4">
                <ScoreBreakdownChart ranked={match.data.ranked} />
                <TraceTimeline trace={match.data.trace} chosenArm={match.data.chosen_arm} />
              </aside>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
