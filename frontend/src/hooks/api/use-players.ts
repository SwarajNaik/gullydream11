import { useQuery } from "@tanstack/react-query";
import { playerKeys } from "@/lib/api/cache-keys";
import { playerApi } from "@/lib/api/endpoints";

export function usePlayers(matchId: number) {
  return useQuery({
    queryKey: playerKeys.list(matchId),
    queryFn: () => playerApi.list(matchId),
    enabled: !!matchId,
  });
}
