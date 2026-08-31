"use client";
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

/**
 * Lightweight, dependency-free i18n for the "Speak Your Request" flow only
 * (see plan — a full message-catalog layer for the whole site is out of
 * scope for now, same call already made in the old LanguageMenu comment).
 * English + Sinhala today; Tamil stays visible in the menu as "coming soon".
 */

export type RequestLocale = "en" | "si";

const STORAGE_KEY = "servio_request_locale";

// Static, ordered "what happens next" steps shown before a request starts.
export const INTRO_STEPS: Record<RequestLocale, string[]> = {
  en: [
    "Transcribe & translate what you send",
    "Understand the situation and urgency",
    "Route it to the right nearby provider",
  ],
  si: [
    "ඔබ එවන දේ පිටපත් කර පරිවර්තනය කිරීම",
    "තත්ත්වය සහ හදිසි බව තේරුම් ගැනීම",
    "ළඟම ඇති සුදුසු සේවා සපයන්නා වෙත යොමු කිරීම",
  ],
};

const REQUEST_STRINGS = {
  en: {
    progress: "Progress",
    reconnecting: "Reconnecting…",
    whatHappensNext: "What happens next",
    introFooter: "You’ll see each step run here in real time.",
    statusWorking: "Working…",
    statusClarify: "Needs one detail",
    statusResult: "Ready",
    statusError: "Stopped",
    heading: "Speak your request",
    subheading:
      "Say or type what you need in Sinhala, Tamil, English or a mix — or attach a photo. Every turn shows in both languages, and the panel tracks exactly where your request is headed.",
    clarifyBanner:
      "Answer to continue — your request stays on track (see the panel).",
    newRequest: "New request",
    tryAgain: "Try again",

    stepTranscribing: "Transcribing your voice",
    stepTranslating: "Understanding your message",
    stepAnalysingPhoto: "Analysing your photo",
    stepUnderstanding: "Reading the situation",
    stepClassifying: "Working out the service & urgency",
    stepFinalising: "Preparing your result",
    stepMatching: "Matching a nearby provider",
    stepSoonBadge: "soon",
    errRequestFailed: "Request failed ({status}).",
    errGeneric: "Something went wrong.",
    errNetwork:
      "Couldn’t send your request. Check your connection and try again.",
    detected: "Detected: {bits}",

    micPermissionDenied:
      "Microphone access denied. Enable it in your browser settings.",
    ariaRemovePhoto: "Remove photo",
    placeholderPhotoNote: "Add a note about the photo (optional)",
    ariaSendPhoto: "Send photo",
    ariaCancelRecording: "Cancel recording",
    ariaStopRecording: "Stop recording",
    ariaDiscardRecording: "Discard recording",
    ariaPause: "Pause",
    ariaPlay: "Play",
    voiceNote: "Voice note · {time}",
    ariaSendVoice: "Send voice request",
    ariaAttachPhoto: "Attach photo",
    placeholderAnswer: "Type your answer…",
    placeholderDescribe: "Describe what you need…",
    ariaSendRequest: "Send request",
    ariaRecordVoice: "Record voice",

    whatWeKnow: "What we know so far",
    round: "Round {n}",
    yourNote: "Your note",
    youSaid: "You said",
    inEnglish: "In English",
    inThePhoto: "In the photo",
    service: "Service",
    urgency: "Urgency",
    type: "Type",
    detailsPlaceholder:
      "Details appear here as the assistant works through your request.",
    clarifyHint:
      "Answering the question won’t change course — it just sharpens the match.",
    routingWorkingOut: "Working out who to send…",
    routingResult: "Routing to a {service} near you",
    routingClarify: "Likely a {service} — confirming one detail",
    routingWorking: "Looks like a {service}…",

    couldntRead: "We couldn’t read that clearly",
    emergencyFlag: "Flagged as urgent — treat as an emergency",
    recommendedService: "Recommended service",
    whatWeSawPhoto: "What we saw in the photo",
    confidence: "Confidence",
    confServiceType: "Service type",
    confIntent: "Intent",
    geminiDoubleChecked: "Photo double-checked with Gemini",
    onDeviceRecognised: "Photo recognised on-device",

    voiceBadge: "Voice",
    failedMessage: "Couldn’t process this — try again.",
    whatWeSaw: "What we saw",

    // The research panel is a technical/debug view (raw field names,
    // percentages, JSON) that intentionally stays English-only even in
    // Sinhala mode — only this heading/toggle is translated.
    researchData: "Research data",
  },
  si: {
    progress: "ප්‍රගතිය",
    reconnecting: "නැවත සම්බන්ධ වෙමින්…",
    whatHappensNext: "ඊළඟට සිදුවන්නේ මෙයයි",
    introFooter: "සෑම පියවරක්ම මෙහි සජීවීව දකින්නට ලැබේවි.",
    statusWorking: "සකසමින්…",
    statusClarify: "එක් විස්තරයක් අවශ්‍යයි",
    statusResult: "සූදානම්",
    statusError: "නැවතුණි",
    heading: "ඔබේ ඉල්ලීම කියන්න",
    subheading:
      "ඔබට අවශ්‍ය දේ සිංහල, දෙමළ, ඉංග්‍රීසි හෝ මිශ්‍රව කියන්න, නැත්නම් ටයිප් කරන්න — නැත්නම් ෆොටෝවක් අමුණන්න. සෑම වාරයක්ම භාෂා දෙකෙන්ම පෙන්වයි, ඔබේ ඉල්ලීම හරියටම කොහාටද යන්නේ කියා පැනලය පෙන්වයි.",
    clarifyBanner:
      "ඉදිරියට යාමට පිළිතුරු දෙන්න — ඔබේ ඉල්ලීම නිවැරදි මාර්ගයේම පවතී (පැනලය බලන්න).",
    newRequest: "අලුත් ඉල්ලීමක්",
    tryAgain: "නැවත උත්සාහ කරන්න",

    stepTranscribing: "ඔබේ හඬ පිටපත් කරමින්",
    stepTranslating: "ඔබේ පණිවිඩය තේරුම් ගනිමින්",
    stepAnalysingPhoto: "ඔබේ ෆොටෝව විශ්ලේෂණය කරමින්",
    stepUnderstanding: "තත්ත්වය කියවමින්",
    stepClassifying: "සේවාව සහ හදිසි බව සොයමින්",
    stepFinalising: "ඔබේ ප්‍රතිඵලය සකසමින්",
    stepMatching: "ළඟම ඇති සේවා සපයන්නෙකු සොයමින්",
    stepSoonBadge: "ඉක්මණින්",
    errRequestFailed: "ඉල්ලීම අසාර්ථක විය ({status}).",
    errGeneric: "යමක් වැරදුණි.",
    errNetwork:
      "ඔබේ ඉල්ලීම යැවීමට නොහැකි විය. ඔබේ සම්බන්ධතාවය පරීක්ෂා කර නැවත උත්සාහ කරන්න.",
    detected: "හඳුනාගත්තේ: {bits}",

    micPermissionDenied:
      "මයික්‍රෆෝන් ප්‍රවේශය ප්‍රතික්ෂේප විය. ඔබේ බ්‍රවුසර සැකසුම්වල එය සක්‍රීය කරන්න.",
    ariaRemovePhoto: "ෆොටෝව ඉවත් කරන්න",
    placeholderPhotoNote: "ෆොටෝව ගැන සටහනක් එක් කරන්න (විකල්ප)",
    ariaSendPhoto: "ෆොටෝව යවන්න",
    ariaCancelRecording: "පටිගත කිරීම අවලංගු කරන්න",
    ariaStopRecording: "පටිගත කිරීම නවත්වන්න",
    ariaDiscardRecording: "පටිගත කිරීම ඉවත දමන්න",
    ariaPause: "විරාමය",
    ariaPlay: "වාදනය",
    voiceNote: "හඬ සටහන · {time}",
    ariaSendVoice: "හඬ ඉල්ලීම යවන්න",
    ariaAttachPhoto: "ෆොටෝවක් අමුණන්න",
    placeholderAnswer: "ඔබේ පිළිතුර ටයිප් කරන්න…",
    placeholderDescribe: "ඔබට අවශ්‍ය දේ විස්තර කරන්න…",
    ariaSendRequest: "ඉල්ලීම යවන්න",
    ariaRecordVoice: "හඬ පටිගත කරන්න",

    whatWeKnow: "අප දැනට දන්නා දේ",
    round: "වටය {n}",
    yourNote: "ඔබේ සටහන",
    youSaid: "ඔබ පැවසුවේ",
    inEnglish: "ඉංග්‍රීසියෙන්",
    inThePhoto: "ෆොටෝවේ",
    service: "සේවාව",
    urgency: "හදිසි බව",
    type: "වර්ගය",
    detailsPlaceholder:
      "සහායක ඔබේ ඉල්ලීම හරහා වැඩ කරන විට විස්තර මෙහි දිස් වේ.",
    clarifyHint:
      "ප්‍රශ්නයට පිළිතුරු දීමෙන් මාර්ගය වෙනස් නොවේ — එය ගැලපීම වඩාත් නිවැරදි කරයි.",
    routingWorkingOut: "කාට යැවිය යුතුද යන්න සොයමින්…",
    routingResult: "ළඟම ඇති {service} වෙත යොමු කරමින්",
    routingClarify: "බොහෝදුරට {service} කෙනෙක් — එක් විස්තරයක් තහවුරු කරමින්",
    routingWorking: "පේනවා {service} කෙනෙක් වගේ…",

    couldntRead: "අපට ඒක පැහැදිලිව කියවාගත නොහැකි විය",
    emergencyFlag: "හදිසි ලෙස සලකුණු කර ඇත — හදිසි අවස්ථාවක් ලෙස සලකන්න",
    recommendedService: "නිර්දේශිත සේවාව",
    whatWeSawPhoto: "ෆොටෝවේ අප දුටුවේ",
    confidence: "විශ්වාසනීයත්වය",
    confServiceType: "සේවා වර්ගය",
    confIntent: "අභිප්‍රාය",
    geminiDoubleChecked: "ෆොටෝව Gemini සමඟ දෙවරක් පරීක්ෂා කරන ලදී",
    onDeviceRecognised: "ෆොටෝව උපාංගයේදීම හඳුනාගන්නා ලදී",

    voiceBadge: "හඬ",
    failedMessage: "මෙය සැකසීමට නොහැකි විය — නැවත උත්සාහ කරන්න.",
    whatWeSaw: "අප දුටුවේ",

    researchData: "පර්යේෂණ දත්ත",
  },
} as const;

type Dict = typeof REQUEST_STRINGS.en;
export type RequestStringKey = keyof Dict;

interface RequestLocaleCtxValue {
  locale: RequestLocale;
  setLocale: (locale: RequestLocale) => void;
  t: (key: RequestStringKey, vars?: Record<string, string | number>) => string;
  introSteps: string[];
}

const RequestLocaleCtx = createContext<RequestLocaleCtxValue | null>(null);

export function RequestLocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<RequestLocale>("en");

  // Restore the last choice. This has to run post-mount, not during the
  // initial render, since SSR has no localStorage and reading it eagerly
  // would mismatch the server-rendered "en" markup.
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      // Restoring a persisted choice after mount is exactly what this is for.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (saved === "en" || saved === "si") setLocaleState(saved);
    } catch {
      // ignore
    }
  }, []);

  const setLocale = (next: RequestLocale) => {
    setLocaleState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore
    }
  };

  const value = useMemo<RequestLocaleCtxValue>(() => {
    const dict = REQUEST_STRINGS[locale];
    const t: RequestLocaleCtxValue["t"] = (key, vars) => {
      let str: string = dict[key];
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          str = str.replace(`{${k}}`, String(v));
        }
      }
      return str;
    };
    return { locale, setLocale, t, introSteps: INTRO_STEPS[locale] };
  }, [locale]);

  return (
    <RequestLocaleCtx.Provider value={value}>
      {children}
    </RequestLocaleCtx.Provider>
  );
}

export function useRequestLocale(): RequestLocaleCtxValue {
  const ctx = useContext(RequestLocaleCtx);
  if (!ctx) {
    throw new Error(
      "useRequestLocale must be used within a RequestLocaleProvider",
    );
  }
  return ctx;
}
