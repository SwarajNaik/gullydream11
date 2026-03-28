"use client";

import { useState } from "react";
import {
  useSettlementsIOwe,
  useSettlementsOwedToMe,
  useSettlementSummary,
  useMarkPaid,
  useConfirmReceived,
} from "@/hooks/api/use-settlements";
import { SettlementCard } from "@/components/wallet/settlement-card";

const TABS = ["I Owe", "Owed to Me"] as const;
const FILTERS = ["ALL", "PENDING", "COMPLETED"] as const;

export default function SettlementsPage() {
  const [activeTab, setActiveTab] = useState<(typeof TABS)[number]>("I Owe");
  const [filter, setFilter] = useState<string>("ALL");

  const statusFilter = filter === "ALL" ? undefined : filter;

  const { data: iOweData } = useSettlementsIOwe(statusFilter);
  const { data: owedData } = useSettlementsOwedToMe(statusFilter);
  const { data: summaryData } = useSettlementSummary();

  const markPaid = useMarkPaid();
  const confirmReceived = useConfirmReceived();

  /* eslint-disable @typescript-eslint/no-explicit-any */
  const summary = (summaryData as any)?.data;
  const iOweSettlements = (iOweData as any)?.data?.settlements || [];
  const owedSettlements = (owedData as any)?.data?.settlements || [];
  /* eslint-enable @typescript-eslint/no-explicit-any */

  const settlements = activeTab === "I Owe" ? iOweSettlements : owedSettlements;

  return (
    <div className="px-4 pt-6 pb-20">
      <h1 className="mb-4 text-xl font-bold text-white">Settlements</h1>

      {/* Summary */}
      {summary && (
        <div className="mb-4 flex gap-3">
          <div className="flex-1 rounded-xl bg-[#0F3460] p-3 text-center">
            <p className="text-xs text-[#9E9E9E]">You Owe</p>
            <p className="text-lg font-bold text-[#E94560]">
              ₹{summary.total_i_owe}
            </p>
          </div>
          <div className="flex-1 rounded-xl bg-[#0F3460] p-3 text-center">
            <p className="text-xs text-[#9E9E9E]">You&apos;re Owed</p>
            <p className="text-lg font-bold text-[#00C853]">
              ₹{summary.total_owed_to_me}
            </p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-4 flex rounded-xl bg-[#1A1A2E] p-1">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 rounded-lg py-2 text-sm font-semibold transition-colors ${
              activeTab === tab
                ? "bg-[#0F3460] text-white"
                : "text-[#9E9E9E] hover:text-white"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="mb-4 flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              filter === f
                ? "bg-[#E94560] text-white"
                : "bg-[#1A1A2E] text-[#9E9E9E] hover:text-white"
            }`}
          >
            {f === "ALL" ? "All" : f.charAt(0) + f.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Settlement List */}
      <div className="space-y-3">
        {settlements.length === 0 && (
          <p className="py-8 text-center text-[#666666]">
            No settlements found
          </p>
        )}
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {settlements.map((s: any) => (
          <SettlementCard
            key={s.id}
            settlement={s}
            direction={activeTab === "I Owe" ? "i_owe" : "owed_to_me"}
            onAction={(id) => {
              if (activeTab === "I Owe") {
                markPaid.mutate({ id });
              } else {
                confirmReceived.mutate({ id });
              }
            }}
            isLoading={markPaid.isPending || confirmReceived.isPending}
          />
        ))}
      </div>
    </div>
  );
}
