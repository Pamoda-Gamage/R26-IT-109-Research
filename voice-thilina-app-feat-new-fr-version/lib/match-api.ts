/**
 * Provider Match backend (ranking, providers, bandit dashboard, auth).
 * Override with NEXT_PUBLIC_MATCH_API_BASE; the bandit WebSocket URL is derived
 * by swapping http -> ws (see lib/useBanditSocket.ts).
 */
export const MATCH_API_BASE =
  process.env.NEXT_PUBLIC_MATCH_API_BASE ?? "http://localhost:8001";

export interface TraceEvent {
  node: string;
  started_at: string;
  ended_at: string;
  detail: Record<string, unknown>;
}

export interface RankedCandidate {
  provider_id: string;
  rank: number;
  score: number;
  name: string | null;
  service_type: string | null;
  region: string | null;
  rating: number | null;
  avatar_url: string | null;
  phone: string | null;
  years_experience: number | null;
  bio: string | null;
  eta_minutes: number | null;
  distance_km: number | null;
  acceptance_probability: number | null;
  status: string | null;
}

export interface RequestResponse {
  request_id: string;
  ranked: RankedCandidate[];
  chosen_arm: string;
  arm_index: number;
  context_vector: number[];
  trace: TraceEvent[];
}

export interface BanditArmState {
  theta: number[];
  observation_count: number;
}

export type BanditState = Record<string, BanditArmState>;

export interface SimulationSummary {
  requests_fired: number;
  cumulative_reward_adaptive: number;
  cumulative_reward_static_baseline: number;
}

export async function submitRequest(payload: {
  raw_text: string;
  timestamp: string;
  region: string;
}): Promise<RequestResponse> {
  const res = await fetch(`${MATCH_API_BASE}/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`request failed: ${res.status}`);
  return res.json();
}

export async function submitFeedback(payload: {
  context: number[];
  arm_index: number;
  selected_rank: number | null;
}): Promise<{ reward: number }> {
  const res = await fetch(`${MATCH_API_BASE}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`feedback failed: ${res.status}`);
  return res.json();
}

export async function getBanditState(): Promise<BanditState> {
  const res = await fetch(`${MATCH_API_BASE}/bandit/state`);
  if (!res.ok) throw new Error(`bandit state fetch failed: ${res.status}`);
  return res.json();
}

export async function simulateBatch(n: number): Promise<SimulationSummary> {
  const res = await fetch(`${MATCH_API_BASE}/simulate/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ n }),
  });
  if (!res.ok) throw new Error(`simulate failed: ${res.status}`);
  return res.json();
}
