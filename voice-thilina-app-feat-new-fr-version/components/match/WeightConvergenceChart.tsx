"use client";
import { useEffect, useState } from "react";
import { Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BanditState } from "@/lib/match-api";

const COLORS = ["#3b82f6", "#f97316", "#10b981", "#a855f7"];

export default function WeightConvergenceChart({ state }: { state: BanditState | null }) {
  const [history, setHistory] = useState<Record<string, number>[]>([]);

  // `state` is a snapshot pushed by an external system (the /ws/bandit socket, via
  // useBanditSocket) -- this is exactly the "subscribe to updates from an external
  // system, call setState when external state changes" case the set-state-in-effect
  // rule itself carves out as correct, so the disable below is deliberate, not a
  // workaround.
  useEffect(() => {
    if (!state) return;
    const point: Record<string, number> = { t: history.length };
    for (const [arm, { theta }] of Object.entries(state)) {
      point[arm] = Math.sqrt(theta.reduce((sum, v) => sum + v * v, 0));
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reacting to an external WebSocket push, not deriving from local state
    setHistory((prev) => [...prev.slice(-49), point]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  const armNames = Object.keys(state ?? {});

  return (
    <Card>
      <CardHeader>
        <CardTitle>Weight-profile convergence (theta norm over time)</CardTitle>
      </CardHeader>
      <CardContent>
        {history.length === 0 ? (
          <p className="text-sm text-muted-foreground">Waiting for bandit updates...</p>
        ) : (
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <LineChart data={history}>
                <XAxis dataKey="t" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Legend />
                {armNames.map((arm, i) => (
                  <Line key={arm} type="monotone" dataKey={arm} stroke={COLORS[i % COLORS.length]} dot={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
