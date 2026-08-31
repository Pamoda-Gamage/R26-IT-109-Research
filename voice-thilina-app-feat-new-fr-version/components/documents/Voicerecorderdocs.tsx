"use client";
import { useState } from "react";
import React from "react";
import { ChevronRight, Zap, Layers, AlertTriangle } from "lucide-react";

type Kind = "handler" | "helper" | "lifecycle";

interface FunctionDoc {
  id: string;
  name: string;
  kind: Kind;
  signature: string;
  summary: string;
  details: string[];
  params?: { name: string; type: string; desc: string }[];
  returns?: string;
  sideEffects?: string[];
  triggeredBy: string;
}

const KIND_LABEL: Record<Kind, string> = {
  handler: "Event handler",
  helper: "Helper",
  lifecycle: "Lifecycle",
};

const KIND_COLOR: Record<Kind, string> = {
  handler: "text-violet-600 bg-violet-50 border-violet-200",
  helper: "text-cyan-700 bg-cyan-50 border-cyan-200",
  lifecycle: "text-amber-700 bg-amber-50 border-amber-200",
};

const FUNCTIONS: FunctionDoc[] = [
  {
    id: "cleanup-effect",
    name: "cleanup effect",
    kind: "lifecycle",
    signature: "useEffect(() => { ... }, [])",
    summary: "Releases every resource the recorder opened, on unmount only.",
    details: [
      "Runs once on mount and returns a cleanup function that fires when the component unmounts.",
      "Prevents three common leaks in recorder components: a mic track left open (the browser's recording indicator stays on), an AudioContext left running, and a stale blob: object URL pinned in memory.",
    ],
    sideEffects: [
      "Cancels any pending requestAnimationFrame loop.",
      "Clears the elapsed-time interval.",
      "Stops every track on the active MediaStream (releases the microphone).",
      "Closes the AudioContext.",
      "Revokes the object URL created for the last recording.",
    ],
    triggeredBy: "Component unmount (e.g. navigating away from the page).",
  },
  {
    id: "get-stream",
    name: "getStream",
    kind: "helper",
    signature: "async () => MediaStream",
    summary: "Lazily requests microphone permission and caches the stream.",
    details: [
      "Only calls getUserMedia the first time it's needed, so the permission prompt doesn't appear until the person actually tries to record.",
      "Reuses the same MediaStream on subsequent recordings within the same mount instead of re-prompting.",
    ],
    returns: "The active MediaStream (existing or newly requested).",
    triggeredBy: "startRecording, on the first pointer-down of the mic button.",
  },
  {
    id: "draw-frame",
    name: "drawFrame",
    kind: "helper",
    signature: "() => void",
    summary: "One animation tick of the live waveform.",
    details: [
      "Reads current frequency-domain data from the AnalyserNode, samples it down to 28 values (one per bar), and writes each bar's height directly via ref.style.transform.",
      "Writes to the DOM directly rather than through React state, so the waveform can update at 60fps without triggering 60 re-renders a second.",
      "Re-schedules itself with requestAnimationFrame, so it keeps running for as long as analyserRef stays set.",
    ],
    sideEffects: ["Mutates each waveform bar's inline transform style."],
    triggeredBy:
      "Started by startRecording; stops when finishRecording cancels the animation frame.",
  },
  {
    id: "start-recording",
    name: "startRecording",
    kind: "handler",
    signature: "async () => void",
    summary:
      "Begins capturing audio and switches the dock into recording mode.",
    details: [
      "Requests the mic stream via getStream; if permission is denied, sets an inline error message and stops.",
      "Creates a fresh MediaRecorder and resets the chunk buffer so a previous recording can't bleed into the new one.",
      "Wires up an AudioContext + AnalyserNode against the live stream so drawFrame has data to read.",
      "Starts a 200ms interval that recomputes elapsed time from a stored start timestamp, rather than incrementing a counter, so the displayed timer stays accurate even if the tab is backgrounded.",
    ],
    sideEffects: [
      "Creates a MediaRecorder and AudioContext.",
      "Starts the waveform animation loop and the elapsed-time interval.",
      "Sets dockState to 'recording'.",
    ],
    triggeredBy: "onPointerDown on the mic button.",
  },
  {
    id: "finish-recording",
    name: "finishRecording",
    kind: "handler",
    signature: "(keep: boolean) => void",
    params: [
      {
        name: "keep",
        type: "boolean",
        desc: "Whether to keep the clip (move to preview) or discard it.",
      },
    ],
    summary:
      "Stops capture and routes to either the preview state or back to idle.",
    details: [
      "Stops the MediaRecorder (which triggers its onstop handler to package the recorded chunks into a Blob), cancels the waveform animation, clears the timer, and closes the AudioContext.",
      "If keep is true and the clip is longer than 0.4s, stores the final duration and moves to the preview state.",
      "If keep is false, or the clip is too short to be intentional (an accidental tap), the blob is discarded and the dock resets to idle.",
    ],
    sideEffects: [
      "Stops the MediaRecorder and AudioContext.",
      "Cancels the animation frame and interval.",
      "Sets dockState to 'preview' or 'idle'.",
    ],
    triggeredBy:
      "onPointerUp / onPointerLeave on the mic button (keep = true) or the cancel/trash button while recording (keep = false).",
  },
  {
    id: "toggle-play",
    name: "togglePlay",
    kind: "handler",
    signature: "() => void",
    summary: "Plays or pauses the recorded preview clip.",
    details: [
      "Lazily creates a single Audio element bound to the recording's object URL the first time it's called, then reuses it.",
      "Listens for the native 'ended' event to reset the play/pause icon automatically when playback finishes.",
    ],
    sideEffects: ["Creates or reuses an HTMLAudioElement; toggles isPlaying."],
    triggeredBy: "Tapping the play/pause button in preview mode.",
  },
  {
    id: "discard-recording",
    name: "discardRecording",
    kind: "handler",
    signature: "() => void",
    summary: "Throws away the current clip and resets to idle.",
    details: [
      "Pauses and detaches the preview audio element, revokes the object URL to free memory, and clears the stored blob.",
    ],
    sideEffects: ["Revokes the object URL.", "Sets dockState to 'idle'."],
    triggeredBy:
      "Tapping the trash icon in preview mode; also called internally after a successful send.",
  },
  {
    id: "send-voice",
    name: "sendVoice",
    kind: "handler",
    signature: "() => void",
    summary: "Hands the recorded blob off to the parent and resets the dock.",
    details: [
      "Calls the onSendVoice(blob, durationSec) prop if one was provided, so the parent (e.g. the ASR pipeline) receives the raw audio/webm blob and its duration.",
      "Shows a brief 'Request sent' confirmation overlay, then calls discardRecording to clean up.",
    ],
    sideEffects: [
      "Invokes onSendVoice.",
      "Shows the sent confirmation for ~900ms.",
    ],
    triggeredBy: "Tapping the send button in preview mode.",
  },
  {
    id: "send-text",
    name: "sendText",
    kind: "handler",
    signature: "() => void",
    summary: "Submits the typed request text.",
    details: [
      "Trims whitespace and ignores empty submissions.",
      "Calls the onSendText(text) prop, clears the input, shows the sent confirmation, and blurs the field (dismisses the mobile keyboard).",
    ],
    sideEffects: [
      "Invokes onSendText.",
      "Clears the text field.",
      "Blurs the input.",
    ],
    triggeredBy:
      "Tapping the send button in idle mode, or pressing Enter in the text field.",
  },
  {
    id: "format-time",
    name: "formatTime",
    kind: "helper",
    signature: "(totalSeconds: number) => string",
    params: [
      {
        name: "totalSeconds",
        type: "number",
        desc: "Elapsed or recorded duration, in seconds.",
      },
    ],
    summary: "Formats a duration as m:ss for the timer and preview label.",
    details: ["Pure function, module-level (not recreated on every render)."],
    returns: "A string like '1:07'.",
    triggeredBy:
      "Rendered inline wherever elapsed or recordedDuration is displayed.",
  },
];

function FunctionCard({ fn }: { fn: FunctionDoc }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      id={fn.id}
      className="scroll-mt-24 rounded-2xl border border-slate-200 bg-white"
    >
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3.5 text-left"
      >
        <ChevronRight
          className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${open ? "rotate-90" : ""}`}
        />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <code className="text-[15px] font-semibold text-slate-900">
              {fn.name}
            </code>
            <span
              className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${KIND_COLOR[fn.kind]}`}
            >
              {KIND_LABEL[fn.kind]}
            </span>
          </div>
          <p className="mt-0.5 text-sm text-slate-500">{fn.summary}</p>
        </div>
      </button>

      {open && (
        <div className="space-y-4 border-t border-slate-100 px-4 py-4">
          <pre className="overflow-x-auto rounded-lg bg-slate-900 px-3 py-2 text-xs text-slate-100">
            <code>{fn.signature}</code>
          </pre>

          <ul className="space-y-1.5 text-sm text-slate-600">
            {fn.details.map((d, i) => (
              <li key={i} className="flex gap-2">
                <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-slate-300" />
                <span>{d}</span>
              </li>
            ))}
          </ul>

          {fn.params && fn.params.length > 0 && (
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Parameters
              </p>
              <div className="overflow-hidden rounded-lg border border-slate-200">
                {fn.params.map((p, i) => (
                  <div
                    key={p.name}
                    className={`flex flex-col gap-0.5 px-3 py-2 text-sm sm:flex-row sm:items-baseline sm:gap-3 ${
                      i > 0 ? "border-t border-slate-100" : ""
                    }`}
                  >
                    <code className="shrink-0 font-semibold text-slate-800">
                      {p.name}
                    </code>
                    <code className="shrink-0 text-xs text-cyan-700">
                      {p.type}
                    </code>
                    <span className="text-slate-500">{p.desc}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {fn.returns && (
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Returns
              </p>
              <p className="text-sm text-slate-600">{fn.returns}</p>
            </div>
          )}

          {fn.sideEffects && fn.sideEffects.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5">
              <div className="mb-1 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-amber-700">
                <Zap className="h-3.5 w-3.5" /> Side effects
              </div>
              <ul className="space-y-1 text-sm text-amber-800">
                {fn.sideEffects.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex items-start gap-1.5 text-xs text-slate-500">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" />
            <span>
              <span className="font-medium text-slate-600">Triggered by: </span>
              {fn.triggeredBy}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default function VoiceRecorderDocs() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <header className="mb-8">
        <div className="mb-2 flex items-center gap-2 text-sm font-medium text-violet-600">
          <Layers className="h-4 w-4" /> Component reference
        </div>
        <h1 className="text-2xl font-bold text-slate-900">VoiceRecorder</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">
          Mobile-first voice + text input dock for service requests. Morphs
          between three states — idle, recording, and preview — and streams a
          live, audio-reactive waveform via the Web Audio API while capturing.
        </p>
      </header>

      <section className="mb-8 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Props</h2>
        <div className="space-y-2 text-sm">
          <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
            <code className="shrink-0 font-semibold text-slate-800">
              variant
            </code>
            <code className="shrink-0 text-xs text-cyan-700">
              &quot;fixed&quot; | &quot;inline&quot;
            </code>
            <span className="text-slate-500">
              Default &quot;fixed&quot;. Fixed docks to the viewport bottom with
              safe-area padding; inline sits in normal page flow.
            </span>
          </div>
          <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
            <code className="shrink-0 font-semibold text-slate-800">
              onSendText
            </code>
            <code className="shrink-0 text-xs text-cyan-700">
              (text: string) =&gt; void
            </code>
            <span className="text-slate-500">
              Called with the trimmed text when a typed request is sent.
            </span>
          </div>
          <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
            <code className="shrink-0 font-semibold text-slate-800">
              onSendVoice
            </code>
            <code className="shrink-0 text-xs text-cyan-700">
              (blob: Blob, durationSec: number) =&gt; void
            </code>
            <span className="text-slate-500">
              Called with the recorded audio/webm blob and its duration when a
              voice request is sent.
            </span>
          </div>
          <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
            <code className="shrink-0 font-semibold text-slate-800">
              placeholder
            </code>
            <code className="shrink-0 text-xs text-cyan-700">string</code>
            <span className="text-slate-500">
              Placeholder text for the idle-state input field.
            </span>
          </div>
        </div>
      </section>

      <h2 className="mb-3 text-sm font-semibold text-slate-700">Functions</h2>
      <div className="space-y-2">
        {FUNCTIONS.map((fn) => (
          <FunctionCard key={fn.id} fn={fn} />
        ))}
      </div>
    </div>
  );
}
