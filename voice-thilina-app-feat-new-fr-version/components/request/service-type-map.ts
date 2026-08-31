/**
 * Bridges Servio's ~27 fine-grained service-type labels (see
 * app/services/dispatch_service.py) to the Provider Match world.
 *
 * Providers are only ever seeded with one of six categories
 * (backend-find-nearby-service/app/scripts/seed_providers.py):
 *   plumbing · electrical · appliance_repair · cleaning · pest_control · locksmith
 *
 * Two things are derived from a Servio label:
 *   1. `serviceFilterPrefix` — a canonical seeded value for the backend
 *      `[FILTER_SERVICE_TYPE:…]` prefix (gives a dense server-side result set).
 *   2. `serviceFilterTokens` / `providerMatchesTokens` — the accurate client-side
 *      keyword filter over the returned `ranked` list.
 *
 * Mapping is deliberately loose (AC/TV/laptop/phone/computer repair → appliance,
 * CCTV/solar → electrical, water-pump → plumbing). Labels with no seeded
 * category (carpenter, painter, mason, gardener, mechanic, …) get no filter, so
 * their requests just show the full ranked list.
 */

/** Servio `service_type` label → keyword tokens. A provider matches if its
 * normalized `service_type` contains, or is contained by, any token. */
export const SERVICE_TOKENS: Record<string, string[]> = {
  plumber: ["plumb"],
  water_pump_repair_service: ["plumb", "pump"],
  electrician: ["electric"],
  cctv_installer: ["electric", "cctv"],
  solar_technician: ["electric", "solar"],
  appliance_repair_service: ["appliance"],
  air_condition_technician: ["appliance", "hvac", "air condition", "aircon"],
  tv_repair: ["appliance", "tv", "television"],
  computer_repair_service: ["appliance", "computer"],
  laptop_repair: ["appliance", "laptop"],
  mobile_phone_repair: ["appliance", "phone"],
  cleaning_service: ["clean"],
  pest_controller: ["pest"],
  locksmith: ["lock"],
  // No seeded providers for these yet — tokens still let admin-created providers
  // match; otherwise the caller falls back to "show all + note".
  carpenter: ["carpent", "wood"],
  mason: ["mason"],
  painter: ["paint"],
  gardner: ["garden", "landscap"],
};

/** Canonical seeded category for the backend `[FILTER_SERVICE_TYPE:…]` prefix. */
const CANONICAL: Record<string, string> = {
  plumber: "plumbing",
  water_pump_repair_service: "plumbing",
  electrician: "electrical",
  cctv_installer: "electrical",
  solar_technician: "electrical",
  appliance_repair_service: "appliance_repair",
  air_condition_technician: "appliance_repair",
  tv_repair: "appliance_repair",
  computer_repair_service: "appliance_repair",
  laptop_repair: "appliance_repair",
  mobile_phone_repair: "appliance_repair",
  cleaning_service: "cleaning",
  pest_controller: "pest_control",
  locksmith: "locksmith",
};

function normalize(s: string): string {
  return s.toLowerCase().replace(/[_-]+/g, " ").replace(/\s+/g, " ").trim();
}

/** Keyword tokens for a Servio label, or `[]` when it shouldn't be filtered. */
export function serviceFilterTokens(label: string | null | undefined): string[] {
  if (!label) return [];
  return SERVICE_TOKENS[label] ?? [];
}

/** True if a provider's `service_type` matches any of the tokens. An empty
 * token list means "no filter active" and matches everything. */
export function providerMatchesTokens(
  providerServiceType: string | null | undefined,
  tokens: string[],
): boolean {
  if (tokens.length === 0) return true;
  if (!providerServiceType) return false;
  const p = normalize(providerServiceType);
  return tokens.some((token) => {
    const t = normalize(token);
    return t.length > 0 && (p.includes(t) || t.includes(p));
  });
}

/** Canonical seeded category for the backend prefix, or `null` to send none. */
export function serviceFilterPrefix(label: string | null | undefined): string | null {
  if (!label) return null;
  return CANONICAL[label] ?? null;
}
