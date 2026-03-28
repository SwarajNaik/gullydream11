import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { contestKeys, walletKeys } from "@/lib/api/cache-keys";
import { contestApi } from "@/lib/api/endpoints";

export function useContests(matchId: number) {
  return useQuery({
    queryKey: contestKeys.list(matchId),
    queryFn: () => contestApi.list(matchId),
    enabled: !!matchId,
  });
}

export function useContest(contestId: number) {
  return useQuery({
    queryKey: contestKeys.detail(contestId),
    queryFn: () => contestApi.detail(contestId),
    enabled: !!contestId,
  });
}

export function useJoinContest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ contestId, teamId }: { contestId: number; teamId: number }) =>
      contestApi.join(contestId, teamId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: contestKeys.all });
      qc.invalidateQueries({ queryKey: walletKeys.all });
    },
  });
}

export function useContestLeaderboard(contestId: number) {
  return useQuery({
    queryKey: contestKeys.leaderboard(contestId),
    queryFn: () => contestApi.detail(contestId), // Will need a dedicated endpoint
    enabled: !!contestId,
    refetchInterval: 30000,
  });
}
