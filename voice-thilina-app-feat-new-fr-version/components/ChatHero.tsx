"use client";
import { useRef, useLayoutEffect, useState } from "react";
import { Mic } from "lucide-react";

export default function ChatHero({ visible }: { visible: boolean }) {
  const contentRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState<number | undefined>(undefined);

  useLayoutEffect(() => {
    if (contentRef.current) setHeight(contentRef.current.scrollHeight);
  }, []);

  return (
    <div
      className="overflow-hidden transition-[max-height,opacity] duration-500 ease-out"
      style={{
        maxHeight: visible ? (height ?? 300) : 0,
        opacity: visible ? 1 : 0,
      }}
    >
      <div
        ref={contentRef}
        className="mx-auto flex w-full max-w-md flex-col items-center gap-3 px-4 pt-8 pb-4 text-center"
      >
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-(--servio-primary) shadow-(--servio-shadow)">
          <Mic className="h-6 w-6 text-white" />
        </div>
        <h1 className="text-lg font-semibold text-(--servio-text)">
          What service do you need?
        </h1>

        <p className="text-sm text-(--servio-muted)">
          Speak or type in Sinhala, English, or Singlish — we&apos;ll figure out the
          rest.
        </p>
      </div>
    </div>
  );
}
