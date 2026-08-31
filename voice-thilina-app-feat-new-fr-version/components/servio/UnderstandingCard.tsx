"use client";
import type { ReactNode } from "react";
import { MapPin, Quote, Languages, Eye, Wrench, Gauge, Tag } from "lucide-react";
import type { Message } from "../Usechatsession";
import type { Classification } from "./types";
import type { Phase } from "../hooks/useServiceRequest";
import { useRequestLocale } from "./request-i18n";
import {
  serviceTypeLabel,
  visionObjectTypeLabel,
  visionSubtypeLabel,
  visionConditionLabel,
  urgencyWordLabel,
  intentLabel,
} from "./classification-si";
import { toneBgClass } from "./ui/tone";
import Card from "./ui/Card";

/** Joins the English and Sinhala forms of a classification value, e.g.
 * "Hospital Service · රෝහල් සේවාව" — shown together regardless of the
 * selected UI locale, same idea as the "You said"/"In English" rows below. */
function bilingual(en: string | null, si: string | null): string | null {
  if (!en) return si;
  if (!si || si === en) return en;
  return `${en} · ${si}`;
}

function Row({
  icon: Icon,
  label,
  children,
}: {
  icon: typeof MapPin;
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="servio-row-in flex gap-2.5">
      <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-(--servio-muted)" />
      <div className="min-w-0 flex-1">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-(--servio-muted)">
          {label}
        </p>
        <div className="mt-0.5 text-[13px] leading-snug text-(--servio-text)">
          {children}
        </div>
      </div>
    </div>
  );
}

export default function UnderstandingCard({
  firstUserMessage,
  classification,
  phase,
  round,
}: {
  firstUserMessage?: Message;
  classification: Classification | null;
  phase: Phase;
  round: number;
}) {
  const { t } = useRequestLocale();
  const c = classification;
  const original = firstUserMessage?.content ?? null;
  const english = firstUserMessage?.translation ?? null;
  const isImage = firstUserMessage?.type === "image";

  // Classification values (service/urgency/intent/vision) are shown in both
  // languages at once, regardless of the UI locale toggle — same idea as the
  // "You said"/"In English" rows, which are always bilingual too.
  const service = c?.service_type
    ? bilingual(
        serviceTypeLabel("en", c.service_type),
        serviceTypeLabel("si", c.service_type),
      )
    : null;

  const visionBitsFor = (loc: "en" | "si") =>
    [visionObjectTypeLabel(loc, c?.vision_object_type), visionSubtypeLabel(loc, c?.vision_subtype)]
      .filter(Boolean)
      .join(" · ");
  const condsFor = (loc: "en" | "si") =>
    (c?.vision_conditions ?? [])
      .filter((x) => x && x !== "no_visible_problem")
      .map((x) => visionConditionLabel(loc, x));
  const visionLine = (loc: "en" | "si") => {
    const bits = visionBitsFor(loc);
    const conds = condsFor(loc);
    return bits ? bits + (conds.length ? ` — ${conds.join(", ")}` : "") : null;
  };
  const vision = bilingual(visionLine("en"), visionLine("si"));

  const routing = !service
    ? t("routingWorkingOut")
    : phase === "result"
      ? t("routingResult", { service })
      : phase === "clarify"
        ? t("routingClarify", { service })
        : t("routingWorking", { service });

  const hasAny = original || english || vision || service || c?.urgency;

  return (
    <Card>
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-(--servio-muted)">
          {t("whatWeKnow")}
        </p>
        {round > 1 && (
          <span className="rounded-full bg-(--servio-primary-soft) px-2 py-0.5 text-[11px] font-semibold text-(--servio-primary)">
            {t("round", { n: round })}
          </span>
        )}
      </div>

      <div className="mt-2.5 flex items-start gap-2 rounded-xl bg-(--servio-primary-soft) p-2.5">
        <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-(--servio-primary)" />
        <p className="text-[13px] font-semibold text-(--servio-primary)">
          {routing}
        </p>
      </div>

      {hasAny ? (
        <div className="mt-3.5 flex flex-col gap-3">
          {original && (
            <Row
              key={`orig:${original}`}
              icon={Quote}
              label={isImage ? t("yourNote") : t("youSaid")}
            >
              {original}
            </Row>
          )}
          {english && english !== original && (
            <Row key={`en:${english}`} icon={Languages} label={t("inEnglish")}>
              {english}
            </Row>
          )}
          {vision && (
            <Row key={`vis:${vision}`} icon={Eye} label={t("inThePhoto")}>
              {vision}
            </Row>
          )}
          {service && (
            <Row key={`svc:${service}`} icon={Wrench} label={t("service")}>
              <span className="inline-block rounded-full bg-(--servio-primary-soft) px-2 py-0.5 text-[13px] font-medium text-(--servio-primary)">
                {service}
              </span>
            </Row>
          )}
          {c?.urgency && (
            <Row key={`urg:${c.urgency}`} icon={Gauge} label={t("urgency")}>
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-[13px] font-medium text-white ${toneBgClass(c.urgency)}`}
              >
                {bilingual(
                  urgencyWordLabel("en", c.urgency),
                  urgencyWordLabel("si", c.urgency),
                )}
              </span>
            </Row>
          )}
          {c?.intent && (
            <Row key={`int:${c.intent}`} icon={Tag} label={t("type")}>
              {bilingual(intentLabel("en", c.intent), intentLabel("si", c.intent))}
            </Row>
          )}
        </div>
      ) : (
        <p className="mt-3 text-[13px] leading-relaxed text-(--servio-muted)">
          {t("detailsPlaceholder")}
        </p>
      )}

      {phase === "clarify" && service && (
        <p className="mt-3 rounded-lg border border-dashed border-(--servio-primary)/40 bg-(--servio-primary-soft)/50 px-2.5 py-2 text-[13px] text-(--servio-primary)">
          {t("clarifyHint")}
        </p>
      )}
    </Card>
  );
}
