import { useQuery } from "@tanstack/react-query";
import { getRecommendedSchemes, getSchemes } from "../services/scheme.service";

const profileVersionKey = "profile_version";

export function getProfileVersion() {
  return parseInt(localStorage.getItem(profileVersionKey) || "0", 10);
}

export function bumpProfileVersion() {
  localStorage.setItem(profileVersionKey, String(Date.now()));
}

export function useRecommendedSchemes() {
  const version = getProfileVersion();
  return useQuery({
    queryKey: ["recommended-schemes", version],
    queryFn: getRecommendedSchemes,
    staleTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  });
}

export function useSearchSchemes(query) {
  return useQuery({
    queryKey: ["search-schemes", query],
    queryFn: () => getSchemes({ search: query, limit: 50 }),
    enabled: !!query && query.trim().length > 0,
    staleTime: 30000,
  });
}
