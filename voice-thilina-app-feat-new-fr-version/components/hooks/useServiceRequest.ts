"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  useChatSession,
  createChat,
  getOrCreateUserId,
  type Message,
} from "../Usechatsession";
import { SERVIO_API_BASE as API_BASE } from "../../lib/servio-api";
import { useRequestLocale } from "../servio/request-i18n";

/**
 * Drives the single-shot "Speak Your Request" flow on top of the existing
 * chat backend: one input -> live stage stepper -> result card, with at most
 * one inline clarifying question. Not a chat UI.
 */

export type InputKind = "text" | "audio" | "image";

export type SubmitPayload =
  | { kind: "text"; text: string }
  | { kind: "audio"; blob: Blob }
  | { kind: "image"; file: File; caption?: string };

export type Phase = "compose" | "working" | "clarify" | "result" | "error";

export type StepStatus = "pending" | "active" | "done" | "error";

export interface Step {
  key: string;
  label: string;
  status: StepStatus;
  soon?: boolean;
  note?: string | null;
}

/** One observed stage transition, for the research panel's timing view. Uses
 * the server's `stage.ts` when available (also covers a reconnect replay,
 * which resends the same cached stage event), falling back to client
 * receive-time against an older backend that predates that field. */
export interface StageTiming {
  stage: string;
  state: string;
  ts: number;
}

/** Builds the per-input-kind pipeline using the currently active locale. */
function buildPipeline(
  t: (key: import("../servio/request-i18n").RequestStringKey) => string,
): Record<InputKind, { key: string; label: string }[]> {
  const understanding = t("stepUnderstanding");
  const classifying = t("stepClassifying");
  const finalising = t("stepFinalising");
  return {
    audio: [
      { key: "transcribing", label: t("stepTranscribing") },
      { key: "understanding", label: understanding },
      { key: "classifying", label: classifying },
      { key: "finalising", label: finalising },
    ],
    text: [
      { key: "translating", label: t("stepTranslating") },
      { key: "understanding", label: understanding },
      { key: "classifying", label: classifying },
      { key: "finalising", label: finalising },
    ],
    image: [
      { key: "analysing_photo", label: t("stepAnalysingPhoto") },
      { key: "understanding", label: understanding },
      { key: "classifying", label: classifying },
      { key: "finalising", label: finalising },
    ],
  };
}

async function postRequest(chatId: string, p: SubmitPayload): Promise<void> {
  let res: Response;
  if (p.kind === "text") {
    res = await fetch(`${API_BASE}/api/chats/${chatId}/messages/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: p.text, model: "auto" }),
    });
  } else if (p.kind === "audio") {
    const form = new FormData();
    form.append("file", p.blob, "recording.webm");
    form.append("model", "auto");
    res = await fetch(`${API_BASE}/api/chats/${chatId}/messages/audio`, {
      method: "POST",
      body: form,
    });
  } else {
    const form = new FormData();
    form.append("file", p.file);
    form.append("caption", p.caption ?? "");
    res = await fetch(`${API_BASE}/api/chats/${chatId}/messages/image`, {
      method: "POST",
      body: form,
    });
  }
  if (!res.ok) throw new RequestFailedError(res.status);
}

class RequestFailedError extends Error {
  status: number;
  constructor(status: number) {
    super(`Request failed (${status}).`);
    this.status = status;
  }
}

export function useServiceRequest() {
  const { t } = useRequestLocale();
  const PIPELINE = useMemo(() => buildPipeline(t), [t]);
  const TRAILING = useMemo(
    () => ({ key: "matching", label: t("stepMatching") }),
    [t],
  );

  const [chatId, setChatId] = useState<string | null>(null);
  const { messages, connected, stage } = useChatSession(chatId);
  const [inputKind, setInputKind] = useState<InputKind>("audio");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // How many assistant turns existed when the user last answered a clarifying
  // question — the next assistant turn after that is the resolution.
  const [clarifyBaseline, setClarifyBaseline] = useState(0);
  // Only the latest `stage` is retained upstream (useChatSession) — accumulate
  // every transition we see here so the research panel can show per-stage
  // timing. useState (not a ref): the panel needs a reactive re-render.
  const [stageTimings, setStageTimings] = useState<StageTiming[]>([]);

  useEffect(() => {
    if (!stage) return;
    // Accumulating an external event stream (each incoming `stage` update)
    // into local history is exactly what this effect is for.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setStageTimings((prev) => [
      ...prev,
      { stage: stage.stage, state: stage.state, ts: stage.ts ?? Date.now() },
    ]);
  }, [stage]);

  const assistantMsgs = useMemo(
    () => messages.filter((m) => m.sender === "assistant"),
    [messages],
  );
  const lastAssistant: Message | undefined =
    assistantMsgs[assistantMsgs.length - 1];
  const userMsgs = useMemo(
    () => messages.filter((m) => m.sender === "user"),
    [messages],
  );
  const firstUserMessage = userMsgs[0];
  const userMessage = userMsgs[userMsgs.length - 1];
  const failedUser = useMemo(
    () => messages.find((m) => m.sender === "user" && m.status === "failed"),
    [messages],
  );

  const needsClarify =
    !!lastAssistant?.classification?.needs_clarification &&
    assistantMsgs.length > clarifyBaseline;

  let phase: Phase = "compose";
  if (submitError || failedUser) phase = "error";
  else if (lastAssistant && !needsClarify && lastAssistant.classification)
    phase = "result";
  else if (lastAssistant && !needsClarify && !lastAssistant.classification)
    phase = "result"; // "couldn't understand" fallback message
  else if (needsClarify) phase = "clarify";
  else if (busy || chatId) phase = "working";

  const steps: Step[] = useMemo(() => {
    const defs = PIPELINE[inputKind];
    const done = phase === "result" || phase === "clarify";
    const curIdx = stage ? defs.findIndex((d) => d.key === stage.stage) : -1;

    const rows: Step[] = defs.map((d, i) => {
      let status: StepStatus = "pending";
      if (done) status = "done";
      else if (phase === "error") {
        status = i < Math.max(curIdx, 0) ? "done" : i === Math.max(curIdx, 0) ? "error" : "pending";
      } else if (curIdx === -1) {
        status = i === 0 ? "active" : "pending";
      } else if (i < curIdx) status = "done";
      else if (i === curIdx) status = stage?.state === "done" ? "done" : "active";

      let note: string | null = null;
      if (d.key === "analysing_photo" && stage?.detail && stage.stage === "analysing_photo") {
        const bits = [stage.detail.object_type, stage.detail.subtype].filter(Boolean);
        if (bits.length) note = t("detected", { bits: bits.join(" · ") });
        else if (stage.detail.stage_note) note = String(stage.detail.stage_note);
      }
      return { ...d, status, note };
    });

    rows.push({
      ...TRAILING,
      soon: true,
      status: "pending",
    });
    return rows;
  }, [inputKind, stage, phase, PIPELINE, TRAILING, t]);

  // 0..1 across the real (non-"coming soon") steps, for the tree's growing spine.
  const progress = useMemo(() => {
    const real = steps.filter((s) => !s.soon);
    const done = real.filter((s) => s.status === "done").length;
    return real.length ? done / real.length : 0;
  }, [steps]);

  const round = userMsgs.length; // 1 on the first turn, 2+ after answering a question

  const errorText =
    submitError ??
    failedUser?.error ??
    (stage?.stage === "failed" ? String(stage.detail?.error ?? "") : null) ??
    t("errGeneric");

  const reset = useCallback(() => {
    setClarifyBaseline(0);
    setSubmitError(null);
    setBusy(false);
    setChatId(null);
    setStageTimings([]);
  }, []);

  const submit = useCallback(
    async (payload: SubmitPayload) => {
      setSubmitError(null);
      setInputKind(payload.kind);
      setBusy(true);
      try {
        let id = chatId;
        if (!id) {
          const chat = await createChat(getOrCreateUserId());
          id = chat.id;
          setChatId(id);
        }
        await postRequest(id, payload);
      } catch (e) {
        const message =
          e instanceof RequestFailedError
            ? t("errRequestFailed", { status: e.status })
            : e instanceof Error
              ? e.message
              : t("errNetwork");
        setSubmitError(message);
      } finally {
        setBusy(false);
      }
    },
    [chatId, t],
  );

  // When a clarifying answer is submitted, remember how many assistant turns
  // existed so the *next* one is treated as the resolution.
  const answerClarification = useCallback(
    async (payload: SubmitPayload) => {
      setClarifyBaseline(assistantMsgs.length);
      await submit(payload);
    },
    [assistantMsgs.length, submit],
  );

  return {
    phase,
    steps,
    progress,
    round,
    inputKind,
    connected,
    messages,
    stageTimings,
    userMessage,
    firstUserMessage,
    // The most recent prediction — available during `clarify` too, so the
    // "classifying" step can show what was worked out so far.
    classification: lastAssistant?.classification ?? null,
    result: phase === "result" ? lastAssistant : undefined,
    clarification: needsClarify ? lastAssistant : undefined,
    errorText: phase === "error" ? errorText : null,
    submit,
    answerClarification,
    reset,
  };
}
