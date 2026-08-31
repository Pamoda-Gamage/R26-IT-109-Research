import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { BanditState } from "@/lib/match-api";

export default function BanditStateTable({ state }: { state: BanditState | null }) {
  if (!state) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Bandit state</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Arm</TableHead>
              <TableHead>Observations</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Object.entries(state).map(([arm, info]) => (
              <TableRow key={arm}>
                <TableCell>{arm}</TableCell>
                <TableCell>{info.observation_count}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
