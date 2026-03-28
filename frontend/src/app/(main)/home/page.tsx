"use client";

import { useState } from "react";
import Link from "next/link";
import { useMatches } from "@/hooks/api/use-matches";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MatchCardSkeleton } from "@/components/ui/skeleton";

const TABS = ["UPCOMING", "LIVE", "COMPLETED"];

export default function HomePage() {
  const [activeTab, setActiveTab] = useState("UPCOMING");
  const { data, isLoading } = useMatches(activeTab);
  const matches = (data as any)?.data?.matches || [];
  const user = typeof window !== "undefined" ? JSON.parse(localStorage.getItem("auth_user") || "{}") : {};

  return (
    <div className="px-4 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-sm text-[#9E9E9E]">Welcome back</p>
          <h1 className="text-xl font-bold">Hi, {user?.display_name || "Player"}!</h1>
        </div>
        <Link href="/wallet" className="rounded-full bg-[#0F3460] px-3 py-1.5 text-sm font-medium">
          Wallet
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        {TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
              activeTab === tab ? "bg-[#E94560] text-white" : "bg-[#0F3460] text-[#9E9E9E]"
            }`}
          >
            {tab.charAt(0) + tab.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Match List */}
      <div className="space-y-3">
        {isLoading && [1, 2, 3].map(i => <MatchCardSkeleton key={i} />)}
        {!isLoading && matches.length === 0 && (
          <p className="text-center text-[#666666] py-8">No {activeTab.toLowerCase()} matches</p>
        )}
        {matches.map((m: any) => (
          <Link key={m.id} href={`/matches/${m.id}`}>
            <Card className="hover:border-[#E94560] transition cursor-pointer">
              <CardContent className="pt-3 pb-3">
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="default">IPL</Badge>
                  {m.status === "LIVE" && <Badge variant="live">LIVE</Badge>}
                  {m.status === "UPCOMING" && (
                    <span className="text-xs text-[#9E9E9E]">
                      {new Date(m.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <div className="text-center flex-1">
                    <p className="text-lg font-bold">{m.team_a_short}</p>
                    <p className="text-xs text-[#9E9E9E]">{m.team_a}</p>
                  </div>
                  <span className="text-[#E94560] font-bold text-sm px-3">VS</span>
                  <div className="text-center flex-1">
                    <p className="text-lg font-bold">{m.team_b_short}</p>
                    <p className="text-xs text-[#9E9E9E]">{m.team_b}</p>
                  </div>
                </div>
                {m.venue && <p className="text-xs text-[#666666] text-center mt-2">{m.venue}</p>}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
