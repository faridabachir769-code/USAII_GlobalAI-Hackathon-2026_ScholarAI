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
import DashboardLayout from "../layouts/DashboardLayout";

export default function DecisionReport() {
  const navigate = useNavigate();
  const { state } = useLocation();

  const scheme = state?.scheme;

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
              <div className="flex gap-4">
                <BadgeCheck className="text-green-600" />

                <div>
                  <h3 className="font-semibold">
                    Eligibility Analysis
                  </h3>

                  <p className="mt-1 text-slate-500">
                    Based on your profile, you satisfy
                    the majority of the eligibility
                    requirements for this scheme.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <TrendingUp className="text-blue-600" />

                <div>
                  <h3 className="font-semibold">
                    Expected Benefits
                  </h3>

                  <p className="mt-1 text-slate-500">
                    This scheme provides strong
                    financial support and aligns well
                    with your educational and career
                    goals.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <TriangleAlert className="text-amber-500" />

                <div>
                  <h3 className="font-semibold">
                    Risks
                  </h3>

                  <p className="mt-1 text-slate-500">
                    Ensure all required documents are
                    complete and submit before the
                    deadline.
                  </p>
                </div>
              </div>

              <div className="rounded-xl bg-blue-50 p-5">
                <h3 className="font-semibold text-blue-700">
                  Final Recommendation
                </h3>

                <p className="mt-2 leading-7 text-slate-600">
                  This scheme is one of the strongest
                  options available for your profile.
                  We recommend applying while also
                  comparing alternative schemes before
                  making a final decision.
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-bold">
              Summary
            </h3>

            <div className="mt-6 space-y-5">
              <div className="flex items-center gap-3">
                <CircleDollarSign className="text-green-600" />

                <div>
                  <p className="text-sm text-slate-500">
                    Funding
                  </p>

                  <p className="font-semibold">
                    {scheme.amount || "Not specified"}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <CalendarDays className="text-blue-600" />

                <div>
                  <p className="text-sm text-slate-500">
                    Deadline
                  </p>

                  <p className="font-semibold">
                    {scheme.deadline || "Open"}
                  </p>
                </div>
              </div>

              <div className="rounded-xl bg-green-100 p-5 text-center">
                <p className="text-sm text-slate-600">
                  AI Match Score
                </p>

                <p className="mt-2 text-4xl font-bold text-green-700">
                  {scheme.match_score ?? 95}%
                </p>
              </div>

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