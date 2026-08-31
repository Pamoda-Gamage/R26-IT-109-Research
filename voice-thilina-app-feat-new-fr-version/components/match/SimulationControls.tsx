"use client";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { simulateBatch, type SimulationSummary } from "@/lib/match-api";

export default function SimulationControls() {
  const [summary, setSummary] = useState<SimulationSummary | null>(null);
  const [running, setRunning] = useState(false);

  const fire = async (n: number) => {
    setRunning(true);
    try {
      setSummary(await simulateBatch(n));
    } finally {
      setRunning(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Simulation controls</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex gap-2">
          <Button onClick={() => fire(100)} disabled={running} variant="outline">
            Fire 100 simulated users
          </Button>
          <Button onClick={() => fire(500)} disabled={running} variant="outline">
            Fire 500 simulated users
          </Button>
        </div>
        {summary && (
          <p className="text-sm">
            Adaptive cumulative reward: <strong>{summary.cumulative_reward_adaptive.toFixed(1)}</strong> vs static
            baseline: <strong>{summary.cumulative_reward_static_baseline.toFixed(1)}</strong>
          </p>
        )}
      </CardContent>
    </Card>
  );
}
