export type PredictionStatus =
  | "active"
  | "disabled"
  | "unavailable"
  | "locked";

export type RecommendationPredictionFields = {
  score?: number | null;
  rule_score?: number | null;
  prediction_score?: number | null;
  prediction_status?: PredictionStatus | string | null;
  prediction_applied?: boolean | null;
  prediction_explanation?: string | null;
};
