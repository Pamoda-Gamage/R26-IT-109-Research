"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { RankedCandidate } from "@/lib/match-api";

interface Props {
  candidate: RankedCandidate;
  onSelect: (candidate: RankedCandidate) => void;
  selected: boolean;
  disabled: boolean;
}

export default function ProviderCard({ candidate, onSelect, selected, disabled }: Props) {
  const { rank, name, service_type, region, rating, avatar_url, phone, years_experience, bio, eta_minutes, distance_km, score, status } =
    candidate;

  return (
    <Card className={selected ? "border-primary" : undefined}>
      <CardContent className="flex gap-3 pt-6">
        {avatar_url && (
          // Unsplash-hosted URLs -- plain img avoids configuring next/image remote patterns for a demo dataset.
          // eslint-disable-next-line @next/next/no-img-element
          <img src={avatar_url} alt={name ?? "Provider"} className="h-16 w-16 shrink-0 rounded-full object-cover" />
        )}
        <div className="flex flex-1 flex-col gap-1">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-medium leading-none">{name ?? "Unknown provider"}</p>
              <p className="text-xs text-muted-foreground">
                {service_type?.replace("_", " ")} · {region}
              </p>
            </div>
            <div className="flex items-center gap-1">
              {status && (
                <Badge variant={status === "online" ? "default" : "secondary"} className="capitalize">
                  {status}
                </Badge>
              )}
              <Badge variant="outline">#{rank}</Badge>
            </div>
          </div>

          <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
            {rating != null && <span>★ {rating.toFixed(1)}</span>}
            {years_experience != null && <span>{years_experience} yrs exp</span>}
            {eta_minutes != null && <span>{eta_minutes.toFixed(0)} min ETA</span>}
            {distance_km != null && <span>{distance_km} km away</span>}
            <span>score {score.toFixed(3)}</span>
          </div>

          {bio && <p className="line-clamp-2 text-xs text-muted-foreground">{bio}</p>}
          {phone && <p className="text-xs text-muted-foreground">{phone}</p>}

          <Button
            size="sm"
            variant={selected ? "secondary" : "default"}
            className="mt-1 w-fit"
            disabled={disabled}
            onClick={() => onSelect(candidate)}
          >
            {selected ? "Selected ✓" : "Select this provider"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
