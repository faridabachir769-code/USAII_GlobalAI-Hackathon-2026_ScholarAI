import RecommendationCard from "../dashboard/RecommendationCard";

const recommendations = [
  {
    id: 1,
    title: "National Scholarship Scheme",
    provider: "Government of India",
    deadline: "30 Aug 2026",
    match: 96,
  },
  {
    id: 2,
    title: "Merit Scholarship",
    provider: "Ministry of Education",
    deadline: "12 Sept 2026",
    match: 91,
  },
  {
    id: 3,
    title: "Women in STEM",
    provider: "AICTE",
    deadline: "21 Sept 2026",
    match: 89,
  },
];

export default function Dashboard() {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-8">

        {/* Header */}

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">
            Welcome back 👋
          </h1>

          <p className="mt-2 text-slate-500">
            Here are the best government schemes for your profile.
          </p>
        </div>

        {/* Stats */}

        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">

          <div className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="text-sm text-slate-500">
              Eligible Schemes
            </h2>

            <p className="mt-3 text-4xl font-bold">
              14
            </p>
          </div>

          <div className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="text-sm text-slate-500">
              Profile Completion
            </h2>

            <p className="mt-3 text-4xl font-bold">
              95%
            </p>
          </div>

          <div className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="text-sm text-slate-500">
              AI Match Score
            </h2>

            <p className="mt-3 text-4xl font-bold">
              93%
            </p>
          </div>

        </div>

        {/* Recommendations */}

        <div className="mt-10">

          <h2 className="mb-5 text-2xl font-semibold">
            Recommended For You
          </h2>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">

            {recommendations.map((scheme) => (
              <RecommendationCard
                key={scheme.id}
                scheme={scheme}
              />
            ))}

          </div>

        </div>

      </div>
    </main>
  );
}