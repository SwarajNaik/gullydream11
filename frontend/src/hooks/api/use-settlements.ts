import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { settlementKeys, walletKeys } from "@/lib/api/cache-keys";
import { settlementApi } from "@/lib/api/endpoints";

export function useSettlementsIOwe(status?: string) {
  return useQuery({
    queryKey: settlementKeys.iOwe({ status }),
    queryFn: () => settlementApi.iOwe(status ? { status } : undefined),
  });
}

export function useSettlementsOwedToMe(status?: string) {
  return useQuery({
    queryKey: settlementKeys.owedToMe({ status }),
    queryFn: () => settlementApi.owedToMe(status ? { status } : undefined),
  });
}

export function useSettlementSummary() {
  return useQuery({
    queryKey: settlementKeys.summary(),
    queryFn: () => settlementApi.summary(),
  });
}

export function useContestSettlements(contestId: number) {
  return useQuery({
    queryKey: settlementKeys.contest(contestId),
    queryFn: () => settlementApi.forContest(contestId),
    enabled: contestId > 0,
  });
}

export function useMarkPaid() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: number; note?: string }) =>
      settlementApi.markPaid(id, note ? { note } : undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settlementKeys.all });
      queryClient.invalidateQueries({ queryKey: walletKeys.all });
    },
  });
}

export function useConfirmReceived() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: number; note?: string }) =>
      settlementApi.confirmReceived(id, note ? { note } : undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settlementKeys.all });
      queryClient.invalidateQueries({ queryKey: walletKeys.all });
    },
  });
}
