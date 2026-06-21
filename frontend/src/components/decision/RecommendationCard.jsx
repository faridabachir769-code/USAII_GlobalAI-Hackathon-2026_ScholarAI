import { CheckCircle2 } from "lucide-react";

export default function RecommendationCard({
  recommendation,
}) {
  return (
    <div className="rounded-2xl border border-green-200 bg-green-50 p-6">
      <div className="flex items-center gap-3">
        <CheckCircle2
          className="text-green-600"
          size={28}
        />

        <div>
          <h2 className="text-xl font-semibold text-slate-900">
            Recommended Scheme
          </h2>

          <p className="text-slate-600">
            {recommendation}
          </p>
        </div>
      </div>
    </div>
  );
}