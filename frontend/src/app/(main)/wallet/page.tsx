"use client";

import { useState } from "react";
import Link from "next/link";
import { useWallet, useTransactions } from "@/hooks/api/use-wallet";
import { useSettlementSummary } from "@/hooks/api/use-settlements";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TopupSheet } from "@/components/wallet/topup-sheet";

export default function WalletPage() {
  const [showTopup, setShowTopup] = useState(false);
  const { data: walletData } = useWallet();
  const { data: txnData } = useTransactions();
  const { data: summaryData } = useSettlementSummary();
  /* eslint-disable @typescript-eslint/no-explicit-any */
  const wallet = (walletData as any)?.data;
  const transactions = (txnData as any)?.data?.transactions || [];
  const summary = (summaryData as any)?.data;
  /* eslint-enable @typescript-eslint/no-explicit-any */

  return (
    <div className="px-4 pt-6 pb-20">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Wallet</h1>
        <Button
          onClick={() => setShowTopup(true)}
          className="rounded-lg bg-[#00C853] px-4 py-2 text-sm font-semibold hover:bg-[#00C853]/90"
        >
          + Add Money
        </Button>
      </div>

      {/* Balance Card */}
      <Card className="mb-4 border-[#2A2A4A] bg-[#0F3460]">
        <CardContent className="pt-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-[#9E9E9E]">Balance</p>
              <p className="text-xl font-bold text-[#00C853]">
                ₹{wallet?.balance?.toFixed(0) || 0}
              </p>
            </div>
            <div>
              <p className="text-xs text-[#9E9E9E]">Winnings</p>
              <p className="text-xl font-bold text-white">
                ₹{wallet?.total_winnings?.toFixed(0) || 0}
              </p>
            </div>
            <div>
              <p className="text-xs text-[#9E9E9E]">Fees Paid</p>
              <p className="text-sm font-medium text-[#9E9E9E]">
                ₹{wallet?.total_entry_fees?.toFixed(0) || 0}
              </p>
            </div>
            <div>
              <p className="text-xs text-[#9E9E9E]">Pending Dues</p>
              <p className="text-sm font-medium text-[#E94560]">
                ₹{wallet?.pending_dues?.toFixed(0) || 0}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Settlement Summary — links to settlements page */}
      {summary && (summary.total_i_owe > 0 || summary.total_owed_to_me > 0) && (
        <Link href="/wallet/settlements">
          <Card className="mb-4 border-[#2A2A4A] bg-[#16213E]">
            <CardContent className="flex items-center justify-between pt-3 pb-3">
              <div className="flex gap-6">
                <div>
                  <p className="text-xs text-[#9E9E9E]">You Owe</p>
                  <p className="text-base font-bold text-[#E94560]">
                    ₹{summary.total_i_owe}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[#9E9E9E]">You&apos;re Owed</p>
                  <p className="text-base font-bold text-[#00C853]">
                    ₹{summary.total_owed_to_me}
                  </p>
                </div>
              </div>
              <span className="text-xs text-[#9E9E9E]">View All &rarr;</span>
            </CardContent>
          </Card>
        </Link>
      )}

      {/* Transactions */}
      <h2 className="mb-3 text-lg font-semibold text-white">Transactions</h2>
      <div className="space-y-2">
        {transactions.length === 0 && (
          <p className="py-4 text-center text-[#666666]">No transactions yet</p>
        )}
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {transactions.map((t: any) => (
          <Card key={t.id} className="border-[#2A2A4A]">
            <CardContent className="flex items-center justify-between pt-3 pb-3">
              <div>
                <p className="text-sm font-medium text-white">{t.description}</p>
                <p className="text-xs text-[#666666]">{t.type}</p>
              </div>
              <p className={`font-bold ${t.amount > 0 ? "text-[#00C853]" : "text-[#E94560]"}`}>
                {t.amount > 0 ? "+" : ""}₹{Math.abs(t.amount)}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <TopupSheet open={showTopup} onClose={() => setShowTopup(false)} />
    </div>
  );
}
