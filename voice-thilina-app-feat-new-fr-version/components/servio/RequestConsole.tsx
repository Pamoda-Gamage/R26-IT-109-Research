"use client";
import { useEffect, useState } from "react";
import {
  RotateCcw,
  WifiOff,
  AlertCircle,
  Mic,
  Languages,
  Compass,
} from "lucide-react";
import type { useServiceRequest } from "../hooks/useServiceRequest";
import { useRequestLocale } from "./request-i18n";
import RequestComposer from "./RequestComposer";
import RequestMessage from "./RequestMessage";
import StepTree from "./StepTree";
import UnderstandingCard from "./UnderstandingCard";
import ResultCard from "./ResultCard";
import ResearchPanel from "./ResearchPanel";
import Card from "./ui/Card";

function PanelHeader({
  progress,
  status,
  connected,
}: {
  progress: number;
  status: string;
  connected: boolean;
}) {
  const { t } = useRequestLocale();
  return (
    <div>
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-(--servio-muted)">
          {t("progress")}
        </p>
        <span className="text-[11px] font-medium text-(--servio-primary)">
          {status}
        </span>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-(--servio-border)">
        <div
          className={`h-full rounded-full transition-[width] duration-500 ease-out ${
            progress >= 1 ? "bg-(--servio-success)" : "servio-sheen"
          }`}
          style={{ width: `${Math.max(6, progress * 100)}%` }}
        />
      </div>
      {!connected && (
        <p className="mt-2 flex items-center gap-1.5 text-[11px] text-(--servio-warn)">
          <WifiOff className="h-3 w-3" /> {t("reconnecting")}
        </p>
      )}
    </div>
  );
}

type LaneTab = "progress" | "known" | "research";

function LaneTabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`servio-focus -mb-px border-b-2 px-2.5 py-1.5 text-[11px] font-semibold uppercase tracking-wide transition ${
        active
          ? "border-(--servio-primary) text-(--servio-primary)"
          : "border-transparent text-(--servio-muted) hover:text-(--servio-text)"
      }`}
    >
      {children}
    </button>
  );
}

function IntroCard() {
  const { t, introSteps } = useRequestLocale();
  const icons = [Mic, Languages, Compass];
  return (
    <Card>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-(--servio-muted)">
        {t("whatHappensNext")}
      </p>
      <ol className="mt-3 flex flex-col gap-3">
        {introSteps.map((label, i) => {
          const Icon = icons[i];
          return (
            <li key={label} className="flex items-start gap-2.5">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-(--servio-primary-soft) text-[11px] font-bold text-(--servio-primary)">
                {i + 1}
              </span>
              <span className="flex min-w-0 flex-1 items-start gap-2 pt-0.5 text-[13px] text-(--servio-muted)">
                {Icon && <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 opacity-70" />}
                {label}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="mt-3 text-[13px] text-(--servio-muted)">{t("introFooter")}</p>
    </Card>
  );
}

export default function RequestConsole({
  sr,
}: {
  sr: ReturnType<typeof useServiceRequest>;
}) {
  const { t } = useRequestLocale();
  const active =
    sr.phase === "working" || sr.phase === "clarify" || sr.phase === "result";

  const [tab, setTab] = useState<LaneTab>("progress");
  const [autoSwitched, setAutoSwitched] = useState(false);

  // Once a run first reaches a result / clarifying question, bring the outcome
  // forward. Re-arm while a fresh request is composed or re-working.
  useEffect(() => {
    if ((sr.phase === "result" || sr.phase === "clarify") && !autoSwitched) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTab("known");
      setAutoSwitched(true);
    } else if ((sr.phase === "compose" || sr.phase === "working") && autoSwitched) {
      setAutoSwitched(false);
    }
  }, [sr.phase, autoSwitched]);

  const statusText: Record<string, string> = {
    working: t("statusWorking"),
    clarify: t("statusClarify"),
    result: t("statusResult"),
    error: t("statusError"),
  };

  return (
    <div className="mx-auto max-w-5xl px-5 py-12">
      <h1 className="text-3xl font-bold tracking-tight text-(--servio-text)">
        {t("heading")}
      </h1>
      <p className="mt-2 max-w-xl text-sm leading-relaxed text-(--servio-muted)">
        {t("subheading")}
      </p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        {/* ---------- conversation lane ---------- */}
        <div className="order-2 flex min-w-0 flex-col gap-4 lg:order-1">
          {sr.messages.length > 0 && (
            <div className="flex flex-col gap-3">
              {sr.messages.map((m) => (
                <RequestMessage key={m.id} message={m} />
              ))}
            </div>
          )}

          {sr.phase === "result" && sr.result?.classification && (
            <ResultCard message={sr.result} />
          )}

          {sr.phase === "compose" && <RequestComposer onSubmit={sr.submit} />}

          {sr.phase === "clarify" && (
            <div className="rounded-2xl border border-dashed border-(--servio-primary)/40 bg-(--servio-primary-soft)/40 p-3">
              <p className="mb-2 text-xs font-medium text-(--servio-primary)">
                {t("clarifyBanner")}
              </p>
              <RequestComposer onSubmit={sr.answerClarification} compact />
            </div>
          )}

          {sr.phase === "result" && (
            <button
              onClick={sr.reset}
              className="servio-focus inline-flex items-center gap-2 self-start rounded-xl border border-(--servio-border) bg-(--servio-surface) px-4 py-2.5 text-sm font-semibold text-(--servio-primary) transition hover:bg-(--servio-primary-soft)"
            >
              <RotateCcw className="h-4 w-4" /> {t("newRequest")}
            </button>
          )}

          {sr.phase === "error" && (
            <div className="rounded-2xl border border-(--servio-danger)/30 bg-(--servio-danger)/5 p-6">
              <p className="flex items-center gap-2 text-sm font-semibold text-(--servio-danger)">
                <AlertCircle className="h-4 w-4" /> {sr.errorText}
              </p>
              <button
                onClick={sr.reset}
                className="servio-focus mt-4 inline-flex items-center gap-2 rounded-xl bg-(--servio-primary) px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-(--servio-primary-hover)"
              >
                <RotateCcw className="h-4 w-4" /> {t("tryAgain")}
              </button>
            </div>
          )}
        </div>

        {/* ---------- progress lane ---------- */}
        <aside className="order-1 lg:order-2">
          <div className="flex flex-col gap-4 lg:sticky lg:top-24">
            {active ? (
              <>
                <Card>
                  <PanelHeader
                    progress={sr.progress}
                    status={statusText[sr.phase] ?? ""}
                    connected={sr.connected}
                  />
                  <div className="mt-3 flex gap-1 border-b border-(--servio-border)">
                    <LaneTabButton active={tab === "progress"} onClick={() => setTab("progress")}>
                      {t("progress")}
                    </LaneTabButton>
                    <LaneTabButton active={tab === "known"} onClick={() => setTab("known")}>
                      {t("whatWeKnow")}
                    </LaneTabButton>
                    <LaneTabButton active={tab === "research"} onClick={() => setTab("research")}>
                      {t("researchData")}
                    </LaneTabButton>
                  </div>
                </Card>

                {tab === "progress" && (
                  <Card>
                    <StepTree
                      steps={sr.steps}
                      userMessage={sr.userMessage}
                      classification={sr.classification}
                    />
                  </Card>
                )}
                {tab === "known" && (
                  <UnderstandingCard
                    firstUserMessage={sr.firstUserMessage}
                    classification={sr.classification}
                    phase={sr.phase}
                    round={sr.round}
                  />
                )}
                {tab === "research" && (
                  <ResearchPanel
                    classification={sr.classification}
                    messages={sr.messages}
                    stageTimings={sr.stageTimings}
                    embedded
                  />
                )}
              </>
            ) : (
              <IntroCard />
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
