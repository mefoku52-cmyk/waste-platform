import { PredictionStatusBadge } from "@/features/prediction/components/prediction-status-badge";
import type { RecommendationPredictionFields } from "@/features/prediction/types";

type Props = {
  item: RecommendationPredictionFields;
};

export function RecommendationPredictionSlot({ item }: Props) {
  return (
    <PredictionStatusBadge
      status={item.prediction_status}
      score={item.prediction_score}
      applied={item.prediction_applied}
    />
  );
}
