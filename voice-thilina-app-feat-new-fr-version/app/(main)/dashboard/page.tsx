"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, LayoutDashboard, LogOut, UserRound } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { listChats, getOrCreateUserId } from "@/components/Usechatsession";
import { useBanditSocket } from "@/lib/useBanditSocket";
import { clearSession, getRole } from "@/lib/auth";
import BanditStateTable from "@/components/match/BanditStateTable";
import SimulationControls from "@/components/match/SimulationControls";
import WeightConvergenceChart from "@/components/match/WeightConvergenceChart";

type Tab = "account" | "bandit";

export default function DashboardPage() {
  const [tab, setTab] = useState<Tab>("account");
  const [requestCount, setRequestCount] = useState<number | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const banditState = useBanditSocket();

  useEffect(() => {
    // localStorage-backed values aren't available at render — read them on mount.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setRole(getRole());
    listChats(getOrCreateUserId())
      .then((chats) => setRequestCount(chats.length))
      .catch(() => setRequestCount(0));
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-5 py-12">
      <h1 className="text-3xl font-bold tracking-tight text-[#082454]">Your Servio dashboard</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Manage your account and inspect the adaptive ranking model.
      </p>

      <div className="mt-6 flex gap-2 border-b border-slate-200">
        <TabButton active={tab === "account"} onClick={() => setTab("account")} icon={UserRound}>
          Account
        </TabButton>
        <TabButton active={tab === "bandit"} onClick={() => setTab("bandit")} icon={Activity}>
          Ranking bandit
        </TabButton>
      </div>

      {tab === "account" ? (
        <div className="mt-6 grid gap-6 md:grid-cols-[220px_1fr]">
          <Card className="h-fit p-2">
            <nav className="flex flex-col gap-1">
              <span className="flex items-center gap-2.5 rounded-xl bg-secondary px-3 py-2.5 text-sm font-medium text-secondary-foreground">
                <LayoutDashboard className="h-4 w-4" /> Dashboard
              </span>
              <Link
                href="/request"
                className="flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition hover:bg-muted"
              >
                <UserRound className="h-4 w-4" /> New request
              </Link>
              <button
                type="button"
                onClick={() => {
                  clearSession();
                  window.location.href = "/";
                }}
                className="mt-1 flex w-full items-center gap-2.5 rounded-xl border border-destructive/30 px-3 py-2.5 text-sm font-semibold text-destructive transition hover:bg-destructive/5"
              >
                <LogOut className="h-4 w-4" /> Logout
              </button>
            </nav>
          </Card>

          <div className="flex flex-col gap-5">
            <Card>
              <CardContent className="pt-6">
                <h2 className="text-lg font-bold text-[#082454]">
                  Welcome{role ? `, ${role}` : ""} 👋
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {role === "admin"
                    ? "You have admin access — manage the provider directory from Providers."
                    : "Describe a problem by voice, text or photo and Servio will classify it and match you to a nearby provider."}
                </p>
              </CardContent>
            </Card>

            <div className="grid gap-4 sm:grid-cols-3">
              <Stat value={role ? "Signed in" : "Guest"} label="Account status" />
              <Stat value={role === "admin" ? "Admin" : "User"} label="Role" />
              <Stat value={requestCount === null ? "…" : String(requestCount)} label="Service requests" />
            </div>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-bold text-[#082454]">Quick start</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  Head to{" "}
                  <Link href="/request" className="font-medium text-primary hover:underline">
                    Speak Your Request
                  </Link>{" "}
                  to describe a problem and see it classified and matched step by step.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        <div className="mt-6 flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            Live view of the LinUCB contextual bandit that picks a weight profile for provider
            ranking. Fire simulated users to watch it learn.
          </p>
          <SimulationControls />
          <WeightConvergenceChart state={banditState} />
          <BanditStateTable state={banditState} />
        </div>
      )}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon: Icon,
  children,
}: {
  active: boolean;
  onClick: () => void;
  icon: typeof Activity;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`-mb-px flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold transition ${
        active
          ? "border-primary text-primary"
          : "border-transparent text-muted-foreground hover:text-foreground"
      }`}
    >
      <Icon className="h-4 w-4" /> {children}
    </button>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-2xl font-bold text-primary">{value}</p>
        <p className="mt-1 text-xs text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  );
}
