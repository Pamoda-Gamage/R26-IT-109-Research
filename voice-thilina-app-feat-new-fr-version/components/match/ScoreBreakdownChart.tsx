"use client";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RankedCandidate } from "@/lib/match-api";

export default function ScoreBreakdownChart({ ranked }: { ranked: RankedCandidate[] }) {
  const data = ranked.slice(0, 10).map((c) => ({ name: c.provider_id.slice(0, 8), score: c.score }));
  return (
    <Card>
      <CardHeader>
        <CardTitle>Score breakdown (top 10)</CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{ width: "100%", height: 260 }}>
          <ResponsiveContainer>
            <BarChart data={data}>
              <XAxis dataKey="name" fontSize={11} />
              <YAxis domain={[0, 1]} fontSize={11} />
              <Tooltip />
              <Bar dataKey="score" fill="var(--color-primary, #3b82f6)" radius={4} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
