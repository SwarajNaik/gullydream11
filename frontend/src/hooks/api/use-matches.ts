import { useQuery } from "@tanstack/react-query";
import { matchKeys } from "@/lib/api/cache-keys";
import { matchApi } from "@/lib/api/endpoints";

export function useMatches(status?: string) {
  return useQuery({
    queryKey: matchKeys.list({ status }),
    queryFn: () => matchApi.list(status ? { status } : undefined),
  });
}

export function useMatch(matchId: number) {
  return useQuery({
    queryKey: matchKeys.detail(matchId),
    queryFn: () => matchApi.detail(matchId),
    enabled: !!matchId,
  });
}
