import type { RequestLocale } from "./request-i18n";

/**
 * Sinhala labels for backend classification *values* (service_type, urgency,
 * intent, vision object/subtype/conditions) — distinct from the static UI
 * chrome in request-i18n.tsx. The closed-vocabulary maps below are mirrored
 * from the backend so labels stay consistent with what the classifier was
 * trained on:
 *  - service_type   -> backend/app/services/dispatch_service.py `_SERVICE_TYPE_SI`
 *  - vision_object_type/vision_subtype/vision_conditions ->
 *      backend/app/services/image_taxonomy.py `_OBJECT_TYPE_SI` / `_SUBTYPE_SI` / `_CONDITION_SI`
 * urgency/intent aren't in the backend (only 3- and 4-way sets) so they're
 * defined here directly. Anything not listed falls back to the humanized
 * English label, same graceful-degradation behavior as the backend helpers.
 */

function titleize(s?: string | null): string {
  return (s ?? "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const SERVICE_TYPE_SI: Record<string, string> = {
  air_condition_technician: "ඒසී තාක්ෂණිකයා",
  ambulance_service: "ගිලන්රථ සේවාව",
  appliance_repair_service: "උපකරණ අලුත්වැඩියා සේවාව",
  battery_jump_start_service: "බැටරි ජම්ප් ස්ටාර්ට් සේවාව",
  car_care: "කාර් රැකවරණය",
  carpenter: "වඩුකාරයා",
  cctv_installer: "CCTV සවි කරන්නා",
  cleaning_service: "පිරිසිදු කිරීමේ සේවාව",
  computer_repair_service: "පරිගණක අලුත්වැඩියා සේවාව",
  electrician: "විදුලි කාර්මිකයා",
  gardner: "උයන්පල්ලා",
  hospital_service: "රෝහල් සේවාව",
  laptop_repair: "ලැප්ටොප් අලුත්වැඩියාව",
  locksmith: "යතුරු පණ්ඩිතයා",
  mason: "ගොඩනැගිලි කාර්මිකයා",
  mechanic: "මිස්ත්‍රි",
  mobile_phone_repair: "ජංගම දුරකථන අලුත්වැඩියාව",
  movers: "ගෙදර මාරු කිරීමේ සේවාව",
  network_operator: "ජාල ක්‍රියාකරු",
  nursing_assistance: "හෙදියා සහාය",
  painter: "සායම්කරු",
  pest_controller: "පළිබෝධ පාලකයා",
  plumber: "නළ කාර්මිකයා",
  request_service: "සේවා ඉල්ලීම",
  solar_technician: "සූර්ය බල තාක්ෂණිකයා",
  tv_repair: "රූපවාහිනී අලුත්වැඩියාව",
  water_pump_repair_service: "ජල පොම්ප අලුත්වැඩියා සේවාව",
};

const OBJECT_TYPE_SI: Record<string, string> = {
  vehicle: "වාහනයක්",
  appliance: "ගෘහ උපකරණයක්",
  electronic_device: "ඉලෙක්ට්‍රොනික උපකරණයක්",
  plumbing_fixture: "ජල නල උපකරණයක්",
  electrical_fixture: "විදුලි උපකරණයක්",
  structure_surface: "ගොඩනැගිලි කොටසක්",
  outdoor_area: "එළිමහන් ප්‍රදේශයක්",
  security_equipment: "ආරක්ෂක උපකරණයක්",
  person_medical: "රෝගී පුද්ගලයෙක්",
  other: "වෙනත් දෙයක්",
};

const SUBTYPE_SI: Record<string, string> = {
  car: "කාර් එකක්",
  van: "වෑන් එකක්",
  suv_jeep: "ජීප් රථයක්",
  pickup: "පිකප් එකක්",
  lorry_truck: "ලොරියක්",
  bus: "බස් එකක්",
  motorcycle: "මෝටර් සයිකලයක්",
  scooter: "ස්කූටර් එකක්",
  three_wheeler: "ත්‍රිරෝද රථයක්",
  bicycle: "බයිසිකලයක්",
  tractor: "ට්‍රැක්ටරයක්",
  heavy_equipment: "බර යන්ත්‍රෝපකරණයක්",
  refrigerator: "ශීතකරණයක්",
  washing_machine: "රෙදි සෝදන යන්ත්‍රයක්",
  air_conditioner: "වායු සමීකරණයක්",
  water_pump: "ජල පොම්පයක්",
  television: "රූපවාහිනියක්",
  laptop: "ලැප්ටොප් එකක්",
  desktop_computer: "පරිගණකයක්",
  mobile_phone: "ජංගම දුරකථනයක්",
};

const CONDITION_SI: Record<string, string> = {
  water_leak: "වතුර ලීක් වීම",
  burst_pipe: "නළයක් පිපිරීම",
  clog_blockage: "අවහිර වීම",
  flooding_standing_water: "වතුර පිරී තිබීම",
  no_power_dead: "විදුලිය නොමැති වීම",
  sparking_short_circuit: "විදුලි ෂෝට් එකක්",
  overheating_or_smoke: "අධික උණුසුම හෝ දුම",
  active_fire: "ගින්නක්",
  physical_break_broken: "කැඩීමක්",
  crack: "පැළීමක්",
  collision_dent_damage: "හැප්පීමේ හානි",
  flat_or_damaged_tyre: "ටයරයක් පැත්තට වීම",
  will_not_start: "ස්ටාට් නොවීම",
  cracked_or_shattered_screen: "තිරය පැළී තිබීම",
  pest_infestation: "පළිබෝධ උවදුරක්",
  dirty_needs_cleaning: "පිරිසිදු කිරීම අවශ්‍යයි",
  no_visible_problem: "පෙනෙන ගැටලුවක් නැත",
};

// Not a closed vocabulary in the backend (only 3/4-way sets) — defined here.
const URGENCY_WORD_SI: Record<string, string> = {
  low: "අඩු",
  medium: "මධ්‍යම",
  high: "ඉහළ",
};
const URGENCY_PHRASE_SI: Record<string, string> = {
  low: "අඩු හදිසිතාවය",
  medium: "මධ්‍යම හදිසිතාවය",
  high: "ඉහළ හදිසිතාවය",
};
const INTENT_SI: Record<string, string> = {
  request_service: "සේවා ඉල්ලීමක්",
  report_issue: "ගැටලු වාර්තාවක්",
  emergency_request: "හදිසි අවස්ථාවක්",
  emergency: "හදිසි අවස්ථාවක්",
};

function pick(locale: RequestLocale, map: Record<string, string>, value?: string | null) {
  if (!value) return "";
  if (locale === "si") return map[value] ?? titleize(value);
  return titleize(value);
}

export function serviceTypeLabel(locale: RequestLocale, value?: string | null) {
  return pick(locale, SERVICE_TYPE_SI, value);
}
export function visionObjectTypeLabel(locale: RequestLocale, value?: string | null) {
  return pick(locale, OBJECT_TYPE_SI, value);
}
export function visionSubtypeLabel(locale: RequestLocale, value?: string | null) {
  return pick(locale, SUBTYPE_SI, value);
}
export function visionConditionLabel(locale: RequestLocale, value?: string | null) {
  return pick(locale, CONDITION_SI, value);
}
/** Bare urgency word — "Low"/"අඩු" — for compact badges. */
export function urgencyWordLabel(locale: RequestLocale, value?: string | null) {
  return pick(locale, URGENCY_WORD_SI, value);
}
/** Full "Low urgency" phrase — for ResultCard's headline badge. */
export function urgencyPhraseLabel(locale: RequestLocale, value?: string | null) {
  if (!value) return "";
  if (locale === "si") return URGENCY_PHRASE_SI[value] ?? `${titleize(value)} urgency`;
  return `${titleize(value)} urgency`;
}
export function intentLabel(locale: RequestLocale, value?: string | null) {
  if (!value) return "";
  if (locale === "si") return INTENT_SI[value] ?? titleize(value);
  const EN: Record<string, string> = {
    request_service: "Service request",
    report_issue: "Issue report",
    emergency_request: "Emergency",
    emergency: "Emergency",
  };
  return EN[value] ?? titleize(value);
}
