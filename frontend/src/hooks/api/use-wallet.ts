import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { walletKeys } from "@/lib/api/cache-keys";
import { walletApi } from "@/lib/api/endpoints";

export function useWallet() {
  return useQuery({
    queryKey: walletKeys.balance(),
    queryFn: () => walletApi.balance(),
  });
}

export function useTransactions(type?: string) {
  return useQuery({
    queryKey: walletKeys.transactions({ type }),
    queryFn: () => walletApi.transactions(type ? { type } : undefined),
  });
}

export function useTopup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { amount: number; note?: string }) =>
      walletApi.topup(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: walletKeys.all });
    },
  });
}
