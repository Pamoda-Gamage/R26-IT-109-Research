"use client";
import { useState, useRef, useEffect } from "react";
import { ChevronDown, Sparkles, Zap } from "lucide-react";

export interface ModelOption {
  id: string;
  label: string;
  description: string;
  icon?: React.ReactNode;
}

const DEFAULT_MODELS: ModelOption[] = [
  {
    id: "auto",
    label: "Auto",
    description: "Gemini first, falls back to OpenAI automatically",
    icon: <Sparkles className="h-3.5 w-3.5" />,
  },
  {
    id: "gemini",
    label: "Gemini",
    description: "Prefer Google Gemini for this request",
    icon: <Zap className="h-3.5 w-3.5" />,
  },
  {
    id: "openai",
    label: "OpenAI",
    description: "Prefer OpenAI for this request",
    icon: <Zap className="h-3.5 w-3.5" />,
  },
];

export default function ModelSelector({
  models = DEFAULT_MODELS,
  selected,
  onChange,
}: {
  models?: ModelOption[];
  selected: string;
  onChange: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const active = models.find((m) => m.id === selected) ?? models[0];

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node))
        setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div ref={rootRef} className="relative z-30">
      <button
        onClick={() => setOpen((o) => !o)}
        className="servio-focus flex items-center gap-1.5 rounded-full border border-(--servio-border) bg-(--servio-surface) px-3 py-1.5 text-xs font-medium text-(--servio-text) transition hover:bg-(--servio-primary-soft) active:scale-95"
      >
        {active.icon}
        {active.label}
        <ChevronDown
          className={`h-3 w-3 opacity-70 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="absolute right-0 z-30 mt-2 w-56 overflow-hidden rounded-2xl border border-(--servio-border) bg-(--servio-surface) shadow-(--servio-shadow)">
          {models.map((m) => (
            <button
              key={m.id}
              onClick={() => {
                onChange(m.id);
                setOpen(false);
              }}
              className={`flex w-full items-start gap-2 px-3 py-2.5 text-left text-xs transition hover:bg-(--servio-primary-soft) ${
                m.id === selected ? "bg-(--servio-primary-soft)" : ""
              }`}
            >
              <span
                className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${
                  m.id === selected
                    ? "bg-(--servio-primary) text-white"
                    : "bg-(--servio-surface-2) text-(--servio-muted)"
                }`}
              >
                {m.icon}
              </span>
              <span className="flex flex-col">
                <span className="text-(--servio-text)">{m.label}</span>
                <span className="text-[10px] text-(--servio-muted)">
                  {m.description}
                </span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
