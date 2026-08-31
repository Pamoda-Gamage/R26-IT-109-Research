/**
 * Single source of truth for urgency "tone" colors (low/medium/high). Used to
 * replace the mix of inline `style={{ background: "var(--servio-warn)" }}`
 * and Tailwind var-classes that had crept into ResultCard/UnderstandingCard.
 */

export type ToneLevel = "low" | "medium" | "high";

const TONE_VAR: Record<ToneLevel, string> = {
  low: "var(--servio-success)",
  medium: "var(--servio-warn)",
  high: "var(--servio-danger)",
};

const TONE_BG_CLASS: Record<ToneLevel, string> = {
  low: "bg-(--servio-success)",
  medium: "bg-(--servio-warn)",
  high: "bg-(--servio-danger)",
};

function isToneLevel(level?: string | null): level is ToneLevel {
  return level === "low" || level === "medium" || level === "high";
}

/** CSS var string, for the rare spot that still needs an inline style. */
export function toneVar(level?: string | null): string {
  return isToneLevel(level) ? TONE_VAR[level] : "var(--servio-muted)";
}

/** Tailwind background-color class for the given urgency level. */
export function toneBgClass(level?: string | null): string {
  return isToneLevel(level) ? TONE_BG_CLASS[level] : "bg-(--servio-muted)";
}
