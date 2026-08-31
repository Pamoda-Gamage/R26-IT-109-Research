/** A single ranked candidate from a classifier head, e.g. one row of the
 * runner-up guesses behind a top-1 label. */
export interface Candidate {
  label: string;
  confidence: number;
}

/** Which gates/limits produced a given result — surfaced for research review. */
export interface ConfidenceThresholds {
  intent_urgency_service?: number;
  image_object_type?: number;
  image_subtype?: number;
  image_service_type?: number;
  image_top2_margin?: number;
}

export interface ClarificationLimits {
  used?: number;
  max?: number;
}

export interface ModelInfo {
  embedder?: string;
  classifier?: string;
  vision_primary?: string;
  vision_fallback?: string | null;
}

/** The subset of the backend `classification` payload the Servio views read.
 * Every field is optional: older persisted messages predate the research-data
 * additions below, and vision fields are only ever present on image messages
 * (and some are intentionally dropped by the backend on a Gemini fallback —
 * see `reconcile()` in image_recognition_service.py). */
export interface Classification {
  intent?: string;
  service_type?: string;
  urgency?: string;
  intent_confidence?: number;
  service_confidence?: number;
  urgency_confidence?: number;
  needs_clarification?: boolean;
  /** Which check drove a clarifying question ("service" | "urgency" | "intent" | vision reasons). */
  clarification_reason?: string | null;
  /** Set when the user's answer to the "how urgent?" question overrode the model's urgency. */
  urgency_resolved_from_answer?: boolean;
  vision_object_type?: string;
  vision_subtype?: string;
  vision_conditions?: string[];
  recognition_source?: string;

  // Previously sent by the backend but never typed on the frontend.
  vision_suggested_service_type?: string | null;
  clarification_round?: number;
  vision_subtype_confidence?: number;
  vision_service_type?: string | null;
  fallback_reasons?: string[] | null;

  // Research-grade additions: ranked candidate distributions, provenance,
  // and the gates/model that produced this result.
  intent_candidates?: Candidate[];
  service_candidates?: Candidate[];
  urgency_candidates?: Candidate[];
  model_info?: ModelInfo;
  confidence_thresholds?: ConfidenceThresholds;
  clarification_limits?: ClarificationLimits;
  vision_object_type_confidence?: number;
  vision_object_type_top2_margin?: number;
  vision_service_type_confidence?: number;
  vision_condition_scores?: Record<string, number>;
  vision_description?: string;
  vision_object_type_candidates?: Candidate[];
  vision_subtype_candidates?: Candidate[];
  vision_service_type_candidates?: Candidate[];
}
