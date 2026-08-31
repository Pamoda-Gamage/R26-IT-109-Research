"use client";
import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Microphone capture + live level meter + preview playback, with no UI opinion.
 * Extracted from the capture logic in VoiceRecorder.tsx so the Servio request
 * flow can reuse it without the chat dock. VoiceRecorder keeps its own copy.
 */

export const BAR_COUNT = 28;
export const MAX_RECORD_SECONDS = 120;

export type RecorderState = "idle" | "recording" | "preview";

export interface UseAudioRecorder {
  state: RecorderState;
  /** Seconds elapsed while recording, or the final clip length once stopped. */
  elapsed: number;
  /** BAR_COUNT values in [0.12, 1] for a waveform; static while not recording. */
  bars: number[];
  blob: Blob | null;
  isPlaying: boolean;
  permissionError: string | null;
  start: () => Promise<void>;
  /** Stop recording. keep=false discards the clip (treated as a cancel). */
  stop: (keep?: boolean) => void;
  discard: () => void;
  togglePlay: () => void;
}

const IDLE_BARS = Array.from({ length: BAR_COUNT }, () => 0.12);

export function useAudioRecorder(): UseAudioRecorder {
  const [state, setState] = useState<RecorderState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [bars, setBars] = useState<number[]>(IDLE_BARS);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const urlRef = useRef<string | null>(null);
  const audioElRef = useRef<HTMLAudioElement | null>(null);

  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const teardownMeter = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (timerRef.current) clearInterval(timerRef.current);
    rafRef.current = null;
    timerRef.current = null;
    ctxRef.current?.close().catch(() => {});
    ctxRef.current = null;
    analyserRef.current = null;
  }, []);

  useEffect(() => {
    return () => {
      teardownMeter();
      streamRef.current?.getTracks().forEach((t) => t.stop());
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      audioElRef.current?.pause();
    };
  }, [teardownMeter]);

  // Plain hoisted declaration (not useCallback) so the recursive rAF
  // self-reference is legal and `start` can call it without a dep cycle.
  function drawFrame() {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    const step = Math.floor(data.length / BAR_COUNT) || 1;
    setBars(
      Array.from({ length: BAR_COUNT }, (_, i) =>
        Math.max(0.12, (data[i * step] ?? 0) / 255),
      ),
    );
    rafRef.current = requestAnimationFrame(drawFrame);
  }

  const stop = useCallback(
    (keep = true) => {
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      teardownMeter();
      setBars(IDLE_BARS);
      const finalDuration = (Date.now() - startTimeRef.current) / 1000;
      if (keep && finalDuration > 0.4) {
        setElapsed(finalDuration);
        setState("preview");
      } else {
        setBlob(null);
        setState("idle");
      }
    },
    [teardownMeter],
  );

  const start = useCallback(async () => {
    setPermissionError(null);
    if (recorderRef.current?.state === "recording") return;

    let stream: MediaStream;
    try {
      stream =
        streamRef.current ??
        (streamRef.current = await navigator.mediaDevices.getUserMedia({
          audio: true,
        }));
    } catch {
      setPermissionError(
        "Microphone access denied. Enable it in your browser settings.",
      );
      return;
    }

    chunksRef.current = [];
    const rec = new MediaRecorder(stream);
    recorderRef.current = rec;
    rec.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    rec.onstop = () => {
      const b = new Blob(chunksRef.current, { type: "audio/webm" });
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      urlRef.current = URL.createObjectURL(b);
      setBlob(b);
    };
    rec.start();

    const AudioCtx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext;
    const ctx: AudioContext = new AudioCtx();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 64;
    ctx.createMediaStreamSource(stream).connect(analyser);
    ctxRef.current = ctx;
    analyserRef.current = analyser;
    rafRef.current = requestAnimationFrame(drawFrame);

    startTimeRef.current = Date.now();
    setElapsed(0);
    timerRef.current = setInterval(() => {
      const secs = (Date.now() - startTimeRef.current) / 1000;
      setElapsed(secs);
      if (secs >= MAX_RECORD_SECONDS) stop(true);
    }, 200);

    setState("recording");
    // drawFrame is a stable hoisted fn; only `stop` needs tracking.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stop]);

  const discard = useCallback(() => {
    audioElRef.current?.pause();
    audioElRef.current = null;
    setIsPlaying(false);
    setBlob(null);
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
    setElapsed(0);
    setState("idle");
  }, []);

  const togglePlay = useCallback(() => {
    if (!urlRef.current) return;
    if (!audioElRef.current) {
      audioElRef.current = new Audio(urlRef.current);
      audioElRef.current.onended = () => setIsPlaying(false);
    }
    if (isPlaying) {
      audioElRef.current.pause();
      setIsPlaying(false);
    } else {
      void audioElRef.current.play();
      setIsPlaying(true);
    }
  }, [isPlaying]);

  return {
    state,
    elapsed,
    bars,
    blob,
    isPlaying,
    permissionError,
    start,
    stop,
    discard,
    togglePlay,
  };
}
