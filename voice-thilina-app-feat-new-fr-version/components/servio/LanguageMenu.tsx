"use client";
import { useEffect, useRef, useState } from "react";
import { Globe, Check, ChevronDown } from "lucide-react";
import { useRequestLocale, type RequestLocale } from "./request-i18n";

// EN/Sinhala are wired to the Speak Your Request flow (see request-i18n.tsx).
// Tamil stays visible as a "Soon" option — not translated yet.
const LANGS: { code: RequestLocale | "ta"; label: string }[] = [
  { code: "en", label: "English" },
  { code: "si", label: "සිංහල" },
  { code: "ta", label: "தமிழ்" },
];

export default function LanguageMenu() {
  const [open, setOpen] = useState(false);
  const { locale, setLocale } = useRequestLocale();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  const current = LANGS.find((l) => l.code === locale) ?? LANGS[0];

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="servio-focus flex items-center gap-1.5 rounded-lg px-2.5 py-2 text-sm font-medium text-(--servio-muted) transition hover:text-(--servio-text)"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <Globe className="h-4 w-4" />
        {current.label}
        <ChevronDown
          className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <ul
          role="listbox"
          className="absolute right-0 z-50 mt-1 w-44 overflow-hidden rounded-xl border border-(--servio-border) bg-(--servio-surface) py-1 shadow-(--servio-shadow)"
        >
          {LANGS.map((l) => {
            const soon = l.code === "ta";
            return (
              <li key={l.code}>
                <button
                  type="button"
                  disabled={soon}
                  aria-disabled={soon}
                  onClick={() => {
                    if (l.code === "ta") return;
                    setLocale(l.code);
                    setOpen(false);
                  }}
                  className={`servio-focus flex w-full items-center justify-between px-3 py-2 text-left text-sm transition ${
                    soon
                      ? "cursor-not-allowed text-(--servio-muted)/60"
                      : "text-(--servio-text) hover:bg-(--servio-primary-soft)"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    {l.label}
                    {soon && (
                      <span className="rounded-full bg-(--servio-surface-2) px-1.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-(--servio-muted)">
                        Soon
                      </span>
                    )}
                  </span>
                  {l.code === locale && (
                    <Check className="h-4 w-4 text-(--servio-primary)" />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
