import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TraceEvent } from "@/lib/match-api";

export default function TraceTimeline({ trace, chosenArm }: { trace: TraceEvent[]; chosenArm: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Pipeline trace</span>
          <Badge variant="secondary">{chosenArm}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="flex flex-col gap-2">
          {trace.map((event, i) => {
            const durationMs = new Date(event.ended_at).getTime() - new Date(event.started_at).getTime();
            return (
              <li key={i} className="rounded-md border p-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{event.node}</span>
                  <span className="text-muted-foreground">{durationMs}ms</span>
                </div>
                <pre className="mt-1 overflow-x-auto text-xs text-muted-foreground">
                  {JSON.stringify(event.detail)}
                </pre>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
