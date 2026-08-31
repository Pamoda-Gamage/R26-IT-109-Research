export function pct(n?: number): string | null {
  return n === undefined ? null : `${Math.round(n * 100)}%`;
}

/** One labelled confidence gauge — shared by ResultCard's top-1 confidence
 * disclosure and ResearchPanel's ranked candidate lists. Renders nothing when
 * `value` is absent so callers can map over optional fields without guarding. */
export default function ConfidenceBar({
  label,
  value,
  /** Bolds the label/value — used for a list's top-ranked candidate. */
  emphasize = false,
}: {
  label: string;
  value?: number;
  emphasize?: boolean;
}) {
  if (value === undefined) return null;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span
        className={`w-28 shrink-0 truncate ${emphasize ? "font-semibold text-(--servio-text)" : "text-(--servio-muted)"}`}
        title={label}
      >
        {label}
      </span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-(--servio-border)">
        <div
          className={`h-full rounded-full ${emphasize ? "bg-(--servio-primary)" : "bg-(--servio-muted)"}`}
          style={{ width: pct(value) ?? "0%" }}
        />
      </div>
      <span
        className={`w-9 shrink-0 text-right tabular-nums ${emphasize ? "font-semibold text-(--servio-text)" : "text-(--servio-muted)"}`}
      >
        {pct(value)}
      </span>
    </div>
  );
}
