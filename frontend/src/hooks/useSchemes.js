import { useQuery } from "@tanstack/react-query";

import { getRecommendedSchemes } from "../services/scheme.service";

export function useRecommendedSchemes() {
  return useQuery({
    queryKey: ["recommended-schemes"],

    queryFn:
      getRecommendedSchemes,
  });
}