import { useLocation, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  ExternalLink,
} from "lucide-react";

import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import DashboardLayout from "../layouts/DashboardLayout";

export default function Comparison() {
  const navigate = useNavigate();
  const { state } = useLocation();

  const scheme = state?.scheme;

  if (!scheme) {
    return (
      <DashboardLayout>
      <div className="flex min-h-[60vh] items-center justify-center">
        <Card className="max-w-md p-8 text-center">
          <h2 className="text-2xl font-bold">
            No Scheme Selected
          </h2>

          <p className="mt-3 text-slate-500">
            Please return to the dashboard and choose a
            recommendation.
          </p>

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
          title="Scheme Comparison"
          subtitle="AI explanation of why this scheme matches your profile."
        />

        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          <Card className="p-6 lg:col-span-2">
            <h2 className="text-2xl font-bold text-slate-900">
              {scheme.title}
            </h2>

            <p className="mt-4 leading-7 text-slate-600">
              {scheme.description}
            </p>

            <div className="mt-8 grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-sm font-semibold text-slate-500">
                  Provider
                </p>

                <p className="mt-1">
                  {scheme.provider}
                </p>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-500">
                  Country
                </p>

                <p className="mt-1">
                  {scheme.country}
                </p>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-500">
                  Study Level
                </p>

                <p className="mt-1">
                  {scheme.study_level}
                </p>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-500">
                  Amount
                </p>

                <p className="mt-1">
                  {scheme.amount || "Not specified"}
                </p>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-500">
                  Deadline
                </p>

                <p className="mt-1">
                  {scheme.deadline || "Open"}
                </p>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-500">
                  Match Score
                </p>

                <p className="mt-1 font-semibold text-green-600">
                  {scheme.match_score ?? 95}%
                </p>
              </div>
            </div>

            <Button
              className="mt-8"
              onClick={() =>
                window.open(
                  scheme.source_url,
                  "_blank"
                )
              }
            >
              <ExternalLink size={18} />
              View Official Scheme
            </Button>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-bold">
              AI Recommendation
            </h3>

            <div className="mt-6 space-y-5">
              <div className="flex gap-3">
                <CheckCircle2 className="mt-1 text-green-600" />

                <div>
                  <h4 className="font-semibold">
                    Why it matches
                  </h4>

                  <p className="mt-1 text-sm text-slate-500">
                    Your education level, income,
                    category and profile satisfy most
                    eligibility requirements.
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <CheckCircle2 className="mt-1 text-green-600" />

                <div>
                  <h4 className="font-semibold">
                    Benefits
                  </h4>

                  <p className="mt-1 text-sm text-slate-500">
                    High approval potential, financial
                    support and strong relevance to your
                    profile.
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <XCircle className="mt-1 text-red-500" />

                <div>
                  <h4 className="font-semibold">
                    Considerations
                  </h4>

                  <p className="mt-1 text-sm text-slate-500">
                    Double-check deadlines and required
                    documents before applying.
                  </p>
                </div>
              </div>
            </div>

            <Button
              className="mt-8 w-full"
              onClick={() =>
                navigate("/decision-report", {
                  state: { scheme },
                })
              }
            >
              Generate Decision Report
            </Button>
          </Card>
        </div>
      </div>
    </main>
    </DashboardLayout>
  );
}