import RecommendationCard from "../components/dashboard/RecommendationCard";

import { useRecommendedSchemes } from "../hooks/useSchemes";

import Loader from "../components/ui/Loader";
import PageHeader from "../components/ui/PageHeader";

export default function Dashboard() {
  const {
    data: schemes = [],
    isLoading,
    isError,
  } = useRecommendedSchemes();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader text="Loading recommendations..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-slate-500">
          Failed to load recommendations.
        </p>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <PageHeader
          title="Recommended Schemes"
          subtitle="Personalized government schemes based on your profile."
        />

        {schemes.length === 0 ? (
          <div className="mt-10 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <h2 className="text-xl font-semibold text-slate-800">
              No recommendations yet
            </h2>

            <p className="mt-2 text-slate-500">
              Complete your profile to receive personalized recommendations.
            </p>
          </div>
        ) : (
          <div className="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {schemes.map((scheme) => (
              <RecommendationCard
                key={scheme.id}
                scheme={scheme}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}