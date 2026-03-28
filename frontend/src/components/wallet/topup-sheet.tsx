"use client";

import { useState } from "react";
import { useTopup } from "@/hooks/api/use-wallet";
import { Button } from "@/components/ui/button";

const QUICK_AMOUNTS = [100, 500, 1000, 2000];

export function TopupSheet({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [amount, setAmount] = useState<number>(0);
  const [note, setNote] = useState("");
  const topup = useTopup();

  const handleSubmit = () => {
    if (amount <= 0 || amount > 50000) return;
    topup.mutate(
      { amount, note: note || undefined },
      {
        onSuccess: () => {
          setAmount(0);
          setNote("");
          onClose();
        },
      }
    );
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60">
      <div className="w-full max-w-md rounded-t-2xl bg-[#16213E] p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">Add Money</h2>
          <button onClick={onClose} className="text-2xl text-[#9E9E9E]">
            &times;
          </button>
        </div>

        <div className="mb-4">
          <label className="mb-1 block text-xs text-[#9E9E9E]">
            Amount
          </label>
          <input
            type="number"
            min={1}
            max={50000}
            value={amount || ""}
            onChange={(e) => setAmount(Number(e.target.value))}
            placeholder="Enter amount"
            className="w-full rounded-lg border border-[#2A2A4A] bg-[#1A1A2E] px-4 py-3 text-lg font-bold text-white placeholder:text-[#666666] focus:border-[#00C853] focus:outline-none"
          />
        </div>

        <div className="mb-4 flex gap-2">
          {QUICK_AMOUNTS.map((amt) => (
            <button
              key={amt}
              onClick={() => setAmount(amt)}
              className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                amount === amt
                  ? "border-[#00C853] bg-[#00C853]/20 text-[#00C853]"
                  : "border-[#2A2A4A] bg-[#1A1A2E] text-[#9E9E9E] hover:border-[#00C853]/50"
              }`}
            >
              ₹{amt}
            </button>
          ))}
        </div>

        <div className="mb-6">
          <label className="mb-1 block text-xs text-[#9E9E9E]">
            Note (optional)
          </label>
          <input
            type="text"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="e.g. Cash deposit"
            className="w-full rounded-lg border border-[#2A2A4A] bg-[#1A1A2E] px-4 py-2 text-sm text-white placeholder:text-[#666666] focus:border-[#00C853] focus:outline-none"
          />
        </div>

        <Button
          onClick={handleSubmit}
          disabled={amount <= 0 || amount > 50000 || topup.isPending}
          className="w-full rounded-xl bg-[#00C853] py-3 text-base font-bold text-white hover:bg-[#00C853]/90 disabled:opacity-50"
        >
          {topup.isPending ? "Adding..." : `Add ₹${amount || 0}`}
        </Button>
      </div>
    </div>
  );
}
