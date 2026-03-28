import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { teamKeys } from "@/lib/api/cache-keys";
import { teamApi } from "@/lib/api/endpoints";

export function useTeams(matchId: number) {
  return useQuery({
    queryKey: teamKeys.list(matchId),
    queryFn: () => teamApi.list(matchId),
    enabled: !!matchId,
  });
}

export function useCreateTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: teamApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: teamKeys.all });
    },
  });
}
