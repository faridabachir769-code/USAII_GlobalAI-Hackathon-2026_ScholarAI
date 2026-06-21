import { useSearchParams } from "react-router-dom";
import { Search, Filter } from "lucide-react";
import { useState } from "react";
import RecommendationCard from "../components/dashboard/RecommendationCard";
import { useRecommendedSchemes, useSearchSchemes } from "../hooks/useSchemes";
import { SchemeCardSkeleton } from "../components/ui/Skeleton";
import PageHeader from "../components/ui/PageHeader";
import DashboardLayout from "../layouts/DashboardLayout";

export default function Dashboard() {
  const [searchParams] = useSearchParams();
  const searchFromUrl = searchParams.get("search") || "";
  const [searchQuery, setSearchQuery] = useState(searchFromUrl);
  const [showSearch, setShowSearch] = useState(!!searchFromUrl);

  const { data: recommended = [], isLoading, isError } = useRecommendedSchemes();
  const { data: searchResults = [], isLoading: searchLoading } = useSearchSchemes(showSearch ? searchQuery : "");

  const schemes = showSearch && searchQuery.trim() ? searchResults : recommended;
  const loading = showSearch && searchQuery.trim() ? searchLoading : isLoading;

  return (
    <DashboardLayout>
      <main>
        <div className="mx-auto max-w-7xl px-6 py-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <PageHeader
              title={showSearch && searchQuery ? `Results for "${searchQuery}"` : "Recommended Schemes"}
              subtitle={
                showSearch && searchQuery
                  ? `${schemes.length} scheme${schemes.length !== 1 ? "s" : ""} found`
                  : "Personalized government schemes based on your profile."
              }
            />
            <button
              onClick={() => {
                setShowSearch(!showSearch);
                if (!showSearch) setSearchQuery("");
              }}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all ${
                showSearch ? "bg-blue-100 text-blue-700" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              <Filter size={16} />
              {showSearch ? "Show All" : "Search"}
            </button>
          </div>

          {showSearch && (
            <div className="mt-4 relative max-w-md">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by scheme name, keyword..."
                autoFocus
                className="h-12 w-full rounded-xl border border-slate-300 bg-white pl-12 pr-4 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all"
              />
            </div>
          )}

          {loading ? (
            <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <SchemeCardSkeleton key={i} />
              ))}
            </div>
          ) : isError ? (
            <div className="mt-10 rounded-2xl border border-red-200 bg-red-50 p-10 text-center">
              <p className="text-red-600 font-medium">Failed to load recommendations. Please try again.</p>
            </div>
          ) : schemes.length === 0 ? (
            <div className="mt-10 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <h2 className="text-xl font-semibold text-slate-800">No schemes found</h2>
              <p className="mt-2 text-slate-500">
                {showSearch && searchQuery
                  ? "Try a different search keyword."
                  : "Complete your profile to receive personalized recommendations."}
              </p>
            </div>
          ) : (
            <div className="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {schemes.map((scheme) => (
                <RecommendationCard key={scheme.id} scheme={scheme} />
              ))}
            </div>
          )}
        </div>
      </main>
    </DashboardLayout>
  );
}
