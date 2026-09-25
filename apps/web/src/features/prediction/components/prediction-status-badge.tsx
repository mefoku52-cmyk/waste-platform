type PredictionStatus =
  | "active"
  | "disabled"
  | "unavailable"
  | "locked"
  | string
  | null
  | undefined;

type Props = {
  status?: PredictionStatus;
  score?: number | null;
  applied?: boolean | null;
  explanation?: string | null;
};

const COPY: Record<string, { label: string; hint: string }> = {
  active: {
    label: "Prediction active",
    hint: "Structured prediction is attached to this match.",
  },
  locked: {
    label: "Prediction locked",
    hint: "Available with PRO. Current match uses the rule score.",
  },
  disabled: {
    label: "Prediction disabled",
    hint: "The service is turned off. Current match uses the rule score.",
  },
  unavailable: {
    label: "Prediction unavailable",
    hint: "Temporarily unavailable. Current match uses the rule score.",
  },
};

export function PredictionStatusBadge({ status, score, applied, explanation }: Props) {
  const key = String(status ?? "unavailable").toLowerCase();
  const copy = COPY[key] ?? COPY.unavailable;
  const showScore =
    key === "active" && applied === true && typeof score === "number";

  return (
    <div className="mt-2 text-xs text-[#9a8b63]" data-prediction-status={key}>
      <p className="font-semibold text-[#d4af37]">{copy.label}</p>
      <p>{copy.hint}</p>
      {explanation && key === "active" ? (
        <p>{explanation}</p>
      ) : null}
      {showScore ? (
        <p>Predicted interest {Math.round(score * 100)}%</p>
      ) : null}
    </div>
  );
}
