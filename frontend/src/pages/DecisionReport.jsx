import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  BadgeCheck,
  TriangleAlert,
  TrendingUp,
  CircleDollarSign,
  CalendarDays,
} from "lucide-react";

import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import { ReportSkeleton } from "../components/ui/Skeleton";
import DashboardLayout from "../layouts/DashboardLayout";

import { generateDecisionReport } from "../services/decision.service";

export default function DecisionReport() {
  const navigate = useNavigate();
  const { state } = useLocation();

  const scheme = state?.scheme;

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!scheme) return;
    setLoading(true);
    generateDecisionReport({ scheme_id: scheme.id, user_query: "" })
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load decision report");
        setLoading(false);
      });
  }, [scheme]);

  if (!scheme) {
    return (
      <DashboardLayout>
      <div className="flex min-h-[60vh] items-center justify-center">
        <Card className="max-w-md p-8 text-center">
          <h2 className="text-2xl font-bold">
            No Report Available
          </h2>

          <Button
            className="mt-6"
            onClick={() => navigate("/dashboard")}
          >
            Back to Dashboard
          </Button>
        </Card>
      </div>
      </DashboardLayout>
    );
  }

  if (loading) {
    return (
      <DashboardLayout>
        <main>
          <div className="mx-auto max-w-6xl px-6 py-8">
            <ReportSkeleton />
          </div>
        </main>
      </DashboardLayout>
    );
  }

  const r = report || {};

  return (
    <DashboardLayout>
    <main>
      <div className="mx-auto max-w-6xl px-6 py-8">
        <button
          onClick={() => navigate(-1)}
          className="mb-6 flex items-center gap-2 text-blue-600 hover:underline"
        >
          <ArrowLeft size={18} />
          Back
        </button>

        <PageHeader
          title="Decision Report"
          subtitle="AI explains the reasoning behind this recommendation."
        />

        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          <Card className="p-6 lg:col-span-2">
            <h2 className="text-2xl font-bold">
              {scheme.title}
            </h2>

            <p className="mt-4 leading-7 text-slate-600">
              {scheme.description}
            </p>

            <div className="mt-8 space-y-6">
              {r.eligibility_analysis && (
                <div className="flex gap-4">
                  <BadgeCheck className="text-green-600" />
                  <div>
                    <h3 className="font-semibold">Eligibility Analysis</h3>
                    <p className="mt-1 text-slate-500">{r.eligibility_analysis}</p>
                  </div>
                </div>
              )}

              {r.expected_benefits && (
                <div className="flex gap-4">
                  <TrendingUp className="text-blue-600" />
                  <div>
                    <h3 className="font-semibold">Expected Benefits</h3>
                    <p className="mt-1 text-slate-500">
                      {typeof r.expected_benefits === "string"
                        ? r.expected_benefits
                        : JSON.stringify(r.expected_benefits)}
                    </p>
                  </div>
                </div>
              )}

              {scheme.benefits && !r.expected_benefits && (
                <div className="flex gap-4">
                  <TrendingUp className="text-blue-600" />
                  <div>
                    <h3 className="font-semibold">Benefits</h3>
                    <p className="mt-1 text-slate-500">
                      {scheme.benefits.length > 300
                        ? scheme.benefits.slice(0, 300) + "..."
                        : scheme.benefits}
                    </p>
                  </div>
                </div>
              )}

              {r.risks && (
                <div className="flex gap-4">
                  <TriangleAlert className="text-amber-500" />
                  <div>
                    <h3 className="font-semibold">Risks</h3>
                    <p className="mt-1 text-slate-500">{r.risks}</p>
                  </div>
                </div>
              )}

              {r.final_recommendation && (
                <div className="rounded-xl bg-blue-50 p-5">
                  <h3 className="font-semibold text-blue-700">
                    Final Recommendation
                  </h3>
                  <p className="mt-2 leading-7 text-slate-600">
                    {r.final_recommendation}
                  </p>
                </div>
              )}
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-bold">Summary</h3>

            <div className="mt-6 space-y-5">
              {scheme.amount && (
                <div className="flex items-center gap-3">
                  <CircleDollarSign className="text-green-600" />
                  <div>
                    <p className="text-sm text-slate-500">Funding</p>
                    <p className="font-semibold">{scheme.amount}</p>
                  </div>
                </div>
              )}

              {scheme.deadline && (
                <div className="flex items-center gap-3">
                  <CalendarDays className="text-blue-600" />
                  <div>
                    <p className="text-sm text-slate-500">Deadline</p>
                    <p className="font-semibold">{scheme.deadline}</p>
                  </div>
                </div>
              )}

              {(r.match_score ?? scheme.match_score) != null && (
                <div className="rounded-xl bg-green-100 p-5 text-center">
                  <p className="text-sm text-slate-600">AI Match Score</p>
                  <p className="mt-2 text-4xl font-bold text-green-700">
                    {r.match_score ?? scheme.match_score}%
                  </p>
                </div>
              )}

              <Button
                className="w-full"
                onClick={() =>
                  navigate("/what-if", {
                    state: { scheme },
                  })
                }
              >
                Run What-If Simulation
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </main>
    </DashboardLayout>
  );
}
