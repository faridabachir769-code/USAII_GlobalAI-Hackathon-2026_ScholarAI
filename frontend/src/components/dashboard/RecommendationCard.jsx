import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BadgeDollarSign,
  Building2,
  CalendarDays,
  CheckCircle2,
  MapPin,
} from "lucide-react";

import Card from "../ui/Card";
import Button from "../ui/Button";

export default function RecommendationCard({ scheme }) {
  const navigate = useNavigate();

  const handleCompare = () => {
    navigate("/comparison", {
      state: {
        scheme,
      },
    });
  };

  return (
    <Card className="flex h-full flex-col p-6">
      <div className="flex items-start justify-between">
        <div className="rounded-xl bg-blue-100 p-3">
          <Building2
            className="text-blue-600"
            size={26}
          />
        </div>

        <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
          {scheme.match_score ?? 95}% Match
        </span>
      </div>

      <h2 className="mt-5 text-xl font-bold text-slate-900 line-clamp-2">
        {scheme.title}
      </h2>

      <p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-500">
        {scheme.description}
      </p>

      <div className="mt-6 space-y-3">
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <MapPin
            size={18}
            className="text-blue-600"
          />

          <span>
            {scheme.state || scheme.country}
          </span>
        </div>

        <div className="flex items-center gap-3 text-sm text-slate-600">
          <BadgeDollarSign
            size={18}
            className="text-blue-600"
          />

          <span>
            {scheme.amount || "Not specified"}
          </span>
        </div>

        <div className="flex items-center gap-3 text-sm text-slate-600">
          <CalendarDays
            size={18}
            className="text-blue-600"
          />

          <span>
            Deadline:{" "}
            {scheme.deadline || "Open"}
          </span>
        </div>

        <div className="flex items-center gap-3 text-sm text-slate-600">
          <CheckCircle2
            size={18}
            className="text-green-600"
          />

          <span>
            {scheme.study_level}
          </span>
        </div>
      </div>

      <div className="mt-8 flex gap-3">
        <Button
          className="flex-1"
          onClick={handleCompare}
        >
          Compare
        </Button>

        <Button
          variant="secondary"
          onClick={() =>
            window.open(
              scheme.source_url,
              "_blank"
            )
          }
        >
          <ArrowRight size={18} />
        </Button>
      </div>
    </Card>
  );
}