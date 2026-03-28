"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface SettlementData {
  id: number;
  payer_name: string;
  payer_username: string;
  receiver_name: string;
  receiver_username: string;
  match_description: string;
  contest_name: string;
  amount: number;
  status: string;
  payer_confirmed: boolean;
  receiver_confirmed: boolean;
  settlement_note: string | null;
}

export function SettlementCard({
  settlement,
  direction,
  onAction,
  isLoading,
}: {
  settlement: SettlementData;
  direction: "i_owe" | "owed_to_me";
  onAction: (id: number) => void;
  isLoading: boolean;
}) {
  const isCompleted = settlement.status === "COMPLETED";
  const counterparty =
    direction === "i_owe"
      ? { name: settlement.receiver_name, username: settlement.receiver_username }
      : { name: settlement.payer_name, username: settlement.payer_username };

  const alreadyConfirmed =
    direction === "i_owe" ? settlement.payer_confirmed : settlement.receiver_confirmed;

  return (
    <Card className="border-[#2A2A4A] bg-[#0F3460]">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#1A1A2E] text-sm font-bold text-white">
                {counterparty.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <p className="text-sm font-semibold text-white">
                  {counterparty.name}
                </p>
                <p className="text-xs text-[#666666]">
                  @{counterparty.username}
                </p>
              </div>
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              <span className="rounded bg-[#1A1A2E] px-2 py-0.5 text-xs text-[#9E9E9E]">
                {settlement.match_description}
              </span>
              <span className="rounded bg-[#1A1A2E] px-2 py-0.5 text-xs text-[#9E9E9E]">
                {settlement.contest_name}
              </span>
            </div>
          </div>

          <div className="text-right">
            <p
              className={`text-lg font-bold ${
                direction === "i_owe" ? "text-[#E94560]" : "text-[#00C853]"
              }`}
            >
              {direction === "i_owe" ? "-" : "+"}₹{settlement.amount}
            </p>
            {isCompleted ? (
              <span className="inline-block rounded-full bg-[#00C853]/20 px-2 py-0.5 text-xs font-medium text-[#00C853]">
                Settled
              </span>
            ) : (
              <span className="inline-block rounded-full bg-[#FFD600]/20 px-2 py-0.5 text-xs font-medium text-[#FFD600]">
                Pending
              </span>
            )}
          </div>
        </div>

        {!isCompleted && !alreadyConfirmed && (
          <Button
            onClick={() => onAction(settlement.id)}
            disabled={isLoading}
            className={`mt-3 w-full rounded-lg py-2 text-sm font-semibold ${
              direction === "i_owe"
                ? "bg-[#E94560] hover:bg-[#E94560]/80"
                : "bg-[#00C853] hover:bg-[#00C853]/80"
            }`}
          >
            {isLoading
              ? "Processing..."
              : direction === "i_owe"
                ? "Mark as Paid"
                : "Confirm Received"}
          </Button>
        )}

        {!isCompleted && alreadyConfirmed && (
          <p className="mt-3 text-center text-xs text-[#9E9E9E]">
            {direction === "i_owe"
              ? "Marked as paid - waiting for confirmation"
              : "Confirmed - waiting for payer to mark paid"}
          </p>
        )}

        {settlement.settlement_note && (
          <p className="mt-2 text-xs italic text-[#666666]">
            Note: {settlement.settlement_note}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
