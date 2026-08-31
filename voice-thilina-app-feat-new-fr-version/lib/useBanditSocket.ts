"use client";
import { useEffect, useState } from "react";

import type { BanditState } from "./match-api";

const WS_BASE = (process.env.NEXT_PUBLIC_MATCH_API_BASE ?? "http://localhost:8001").replace("http", "ws");

export function useBanditSocket(): BanditState | null {
  const [state, setState] = useState<BanditState | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/bandit`);
    ws.onmessage = (event) => setState(JSON.parse(event.data));
    return () => ws.close();
  }, []);

  return state;
}
