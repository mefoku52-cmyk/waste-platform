"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { http } from "@/lib/api/http";

const GOLD = "#c9a84c";
const MUTED = "#9a8f7c";

type Review = {
  id: string;
  rating: number;
  title?: string | null;
  body?: string | null;
  createdAt?: string | null;
  authorName?: string | null;
};

type ReviewsResponse = {
  items: Review[];
  averageRating?: number | null;
  totalCount?: number | null;
};

function Stars({ value }: { value: number }) {
  const full = Math.floor(value);
  const hasHalf = value - full >= 0.5;
  return (
    <span style={{ color: GOLD }}>
      {"★".repeat(full)}
      {hasHalf ? "⯨" : ""}
      {"☆".repeat(5 - full - (hasHalf ? 1 : 0))}
    </span>
  );
}

export default function CompanyReviewsPage() {
  const params = useParams<{ id: string }>();
  const companyId = String(params?.id || "");

  const reviewsQuery = useQuery({
    queryKey: ["company-reviews", companyId],
    queryFn: () => http.get<ReviewsResponse>(`/companies/${companyId}/reviews`),
    enabled: Boolean(companyId),
  });

  const data = reviewsQuery.data;
  const reviews = data?.items || [];
  const average = data?.averageRating ?? 0;
  const total = data?.totalCount ?? reviews.length;

  return (
    <div>
      <h1 className="mb-6 font-serif text-3xl" style={{ color: GOLD }}>
        Recenzie
      </h1>

      <div className="mb-6 flex items-center gap-4 rounded-xl border p-4" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
        <div className="text-4xl font-bold" style={{ color: GOLD }}>
          {average.toFixed(1)}
        </div>
        <div>
          <Stars value={average} />
          <p className="text-sm" style={{ color: MUTED }}>
            {total} hodnotení
          </p>
        </div>
      </div>

      {reviewsQuery.isLoading ? (
        <p style={{ color: MUTED }}>Načítavam recenzie...</p>
      ) : reviews.length === 0 ? (
        <p style={{ color: MUTED }}>Zatiaľ žiadne recenzie.</p>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div
              key={review.id}
              className="rounded-xl border p-4"
              style={{ borderColor: "rgba(201,168,76,0.25)" }}
            >
              <div className="flex items-center justify-between">
                <Stars value={review.rating} />
                <span className="text-xs" style={{ color: MUTED }}>
                  {review.createdAt
                    ? new Date(review.createdAt).toLocaleDateString("sk-SK")
                    : ""}
                </span>
              </div>
              {review.title && (
                <p className="mt-2 font-semibold">{review.title}</p>
              )}
              {review.body && (
                <p className="mt-1 text-sm" style={{ color: MUTED }}>
                  {review.body}
                </p>
              )}
              {review.authorName && (
                <p className="mt-2 text-xs" style={{ color: MUTED }}>
                  — {review.authorName}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
