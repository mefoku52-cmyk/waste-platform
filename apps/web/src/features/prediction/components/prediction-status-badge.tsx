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
};

const COPY: Record<string, { label: string; hint: string }> = {
  active: {
    label: "Prediction active",
    hint: "Structured prediction is attached to this recommendation.",
  },
  locked: {
    label: "Prediction locked",
    hint: "Available with PRO. Current match uses the existing rule score.",
  },
  disabled: {
    label: "Prediction disabled",
    hint: "The service is turned off. Current match uses the existing rule score.",
  },
  unavailable: {
    label: "Prediction unavailable",
    hint: "Temporarily unavailable. Current match uses the existing rule score.",
  },
};

export function PredictionStatusBadge({ status, score, applied }: Props) {
  const key = String(status ?? "unavailable").toLowerCase();
  const copy = COPY[key] ?? COPY.unavailable;
  const showScore =
    key === "active" && applied === true && typeof score === "number";

  return (
    <div data-prediction-status={key}>
      <strong>{copy.label}</strong>
      <p>{copy.hint}</p>
      {showScore ? <p>Predicted interest {Math.round(score * 100)}%</p> : null}
    </div>
  );
}
