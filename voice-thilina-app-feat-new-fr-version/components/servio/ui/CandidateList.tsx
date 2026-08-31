import type { Candidate } from "../types";
import ConfidenceBar from "./ConfidenceBar";

/** A ranked {label, confidence}[] distribution — the top entry is emphasized.
 * Renders nothing when `items` is absent/empty (e.g. an older persisted
 * message, or a Gemini-fallback vision result where candidates were
 * intentionally dropped — see reconcile() in image_recognition_service.py). */
export default function CandidateList({ items }: { items?: Candidate[] | null }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="flex flex-col gap-1.5">
      {items.map((c, i) => (
        <ConfidenceBar key={c.label} label={c.label} value={c.confidence} emphasize={i === 0} />
      ))}
    </div>
  );
}
