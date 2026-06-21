import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertCircle,
  TrendingUp,
  Shield,
  ExternalLink,
  Star,
  BarChart3,
} from "lucide-react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import { TableRowSkeleton } from "../components/ui/Skeleton";
import DashboardLayout from "../layouts/DashboardLayout";
import { getRecommendedSchemes, compareSchemes } from "../services/scheme.service";

const difficultyColor = {
  Easy: "text-green-600 bg-green-50",
  Medium: "text-amber-600 bg-amber-50",
  Hard: "text-red-600 bg-red-50",
};
const likelihoodColor = {
  High: "text-green-600 bg-green-50",
  Medium: "text-amber-600 bg-amber-50",
  Low: "text-red-600 bg-red-50",
};

function ScoreBar({ label, value, color }) {
  const pct = Math.min(value, 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 text-slate-500">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right font-medium text-slate-700">{Math.round(value)}</span>
    </div>
  );
}

export default function Comparison() {
  const navigate = useNavigate();
  const { state } = useLocation();
  const [comparison, setComparison] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const singleScheme = state?.scheme;
    if (singleScheme) {
      const sd = { ...singleScheme, scoring_breakdown: singleScheme.scoring_breakdown };
      setComparison([sd]);
      setLoading(false);
      return;
    }
    setLoading(true);
    getRecommendedSchemes()
      .then((data) => {
        const schemes = Array.isArray(data) ? data : data?.schemes || data?.recommendations || [];
        if (schemes.length === 0) {
          setComparison([]);
          setLoading(false);
          return;
        }
        const ids = schemes.map((s) => s.id).filter(Boolean);
        if (ids.length === 0) {
          setComparison(schemes);
          setLoading(false);
          return;
        }
        return compareSchemes(ids).then((cmp) => {
          setComparison(cmp?.comparison || schemes);
          setLoading(false);
        });
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load comparison data");
        setLoading(false);
      });
  }, [state]);

  if (loading) {
    return (
      <DashboardLayout>
        <main>
          <div className="mx-auto max-w-7xl px-6 py-8">
            <div className="h-8 w-48 animate-pulse rounded bg-slate-200" />
            <div className="mt-2 h-4 w-72 animate-pulse rounded bg-slate-100" />
            <div className="mt-8 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
              <table className="w-full">
                <thead className="border-b bg-slate-50">
                  <tr>
                    {["Scheme", "Score", "Match", "Difficulty", "Likelihood", "Benefits", "Action"].map((h) => (
                      <th key={h} className="p-4 text-left text-sm font-semibold text-slate-600">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[1, 2, 3, 4, 5].map((i) => (
                    <TableRowSkeleton key={i} cols={7} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="flex min-h-[60vh] items-center justify-center">
          <Card className="max-w-md p-8 text-center">
            <AlertCircle className="mx-auto text-red-500" size={40} />
            <h2 className="mt-4 text-xl font-bold">Error</h2>
            <p className="mt-2 text-slate-500">{error}</p>
            <Button className="mt-6" onClick={() => navigate("/dashboard")}>
              Back to Dashboard
            </Button>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  if (comparison.length === 0) {
    return (
      <DashboardLayout>
        <div className="flex min-h-[60vh] items-center justify-center">
          <Card className="max-w-md p-8 text-center">
            <h2 className="text-2xl font-bold">No Schemes to Compare</h2>
            <p className="mt-3 text-slate-500">
              Build your profile on the dashboard first.
            </p>
            <Button className="mt-6" onClick={() => navigate("/dashboard")}>
              Back to Dashboard
            </Button>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  const scoreColor = (score) => {
    if (score >= 70) return "text-green-600";
    if (score >= 45) return "text-amber-600";
    return "text-red-600";
  };

  return (
    <DashboardLayout>
      <main>
        <div className="mx-auto max-w-7xl px-6 py-8">
          <button
            onClick={() => navigate(-1)}
            className="mb-6 flex items-center gap-2 text-blue-600 hover:underline"
          >
            <ArrowLeft size={18} />
            Back
          </button>

          <PageHeader
            title="Scheme Comparison"
            subtitle="Compare recommended schemes side by side based on your profile."
          />

          <div className="mt-8 overflow-x-auto">
            <table className="w-full border-collapse rounded-xl bg-white shadow-sm">
              <thead>
                <tr className="border-b bg-slate-50 text-left text-sm font-semibold text-slate-600">
                  <th className="p-4 min-w-[200px]">Scheme</th>
                  <th className="p-4 min-w-[100px]">Score</th>
                  <th className="p-4 min-w-[120px]">Match</th>
                  <th className="p-4 min-w-[120px]">Difficulty</th>
                  <th className="p-4 min-w-[120px]">Likelihood</th>
                  <th className="p-4 min-w-[200px]">Key Benefits</th>
                  <th className="p-4 min-w-[160px]">Action</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((s, i) => (
                  <tr key={s.id || i} className="border-b last:border-0 hover:bg-slate-50/50">
                    <td className="p-4">
                      <p className="font-semibold text-slate-900">{s.name || s.title}</p>
                      {s.ministry && <p className="mt-1 text-xs text-slate-400">{s.ministry}</p>}
                      {s.scoring_breakdown && (
                        <div className="mt-3 space-y-1 border-t pt-2">
                          <ScoreBar label="Eligibility" value={s.scoring_breakdown.eligibility} color="bg-blue-500" />
                          <ScoreBar label="Benefit" value={s.scoring_breakdown.benefit} color="bg-emerald-500" />
                          <ScoreBar label="Goal match" value={s.scoring_breakdown.goal_alignment} color="bg-violet-500" />
                          <ScoreBar label="Simplicity" value={s.scoring_breakdown.complexity} color="bg-amber-500" />
                        </div>
                      )}
                    </td>
                    <td className="p-4">
                      {s.total_score != null && (
                        <div className="flex items-center gap-1">
                          <Star className={scoreColor(s.total_score)} size={16} />
                          <span className={`text-lg font-bold ${scoreColor(s.total_score)}`}>
                            {Math.round(s.total_score)}
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="p-4">
                      <div className="flex flex-wrap gap-1">
                        {(s.match_reasons || []).length > 0 ? (
                          s.match_reasons.map((r, j) => (
                            <span
                              key={j}
                              className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700"
                            >
                              <CheckCircle2 size={12} />
                              {r}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-slate-400">No criteria matched</span>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      {s.eligibility_difficulty && (
                        <span
                          className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${
                            difficultyColor[s.eligibility_difficulty] || "text-slate-600 bg-slate-50"
                          }`}
                        >
                          {s.eligibility_difficulty}
                        </span>
                      )}
                    </td>
                    <td className="p-4">
                      {s.approval_likelihood && (
                        <span
                          className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${
                            likelihoodColor[s.approval_likelihood] || "text-slate-600 bg-slate-50"
                          }`}
                        >
                          {s.approval_likelihood}
                        </span>
                      )}
                    </td>
                    <td className="p-4 text-sm text-slate-600 max-w-xs truncate">
                      {s.benefits
                        ? s.benefits.length > 120
                          ? s.benefits.slice(0, 120) + "..."
                          : s.benefits
                        : "—"}
                    </td>
                    <td className="p-4">
                      <div className="flex flex-col gap-2">
                        <Button
                          size="sm"
                          onClick={() =>
                            navigate("/decision-report", { state: { scheme: s } })
                          }
                        >
                          <Shield size={14} />
                          Report
                        </Button>
                        {s.source_url && (
                          <button
                            onClick={() => window.open(s.source_url, "_blank")}
                            className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
                          >
                            <ExternalLink size={12} />
                            Official site
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 text-center">
            <Button onClick={() => navigate("/dashboard")}>
              Back to Dashboard
            </Button>
          </div>
        </div>
      </main>
    </DashboardLayout>
  );
}
