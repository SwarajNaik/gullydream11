"use client";

import { useState } from "react";
import Link from "next/link";
import { useMatches } from "@/hooks/api/use-matches";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const TABS = ["UPCOMING", "LIVE", "COMPLETED"];

export default function MyMatchesPage() {
  const [tab, setTab] = useState("UPCOMING");
  const { data, isLoading } = useMatches(tab);
  const matches = (data as any)?.data?.matches || [];

  return (
    <div className="px-4 pt-6">
      <h1 className="text-xl font-bold mb-4">My Matches</h1>
      <div className="flex gap-2 mb-4">
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`rounded-full px-4 py-1.5 text-sm ${tab === t ? "bg-[#E94560] text-white" : "bg-[#0F3460] text-[#9E9E9E]"}`}>
            {t.charAt(0) + t.slice(1).toLowerCase()}
          </button>
        ))}
      </div>
      <div className="space-y-3">
        {isLoading && <p className="text-center text-[#666666] py-4">Loading...</p>}
        {!isLoading && matches.length === 0 && <p className="text-center text-[#666666] py-8">No matches</p>}
        {matches.map((m: any) => (
          <Link key={m.id} href={`/matches/${m.id}`}>
            <Card className="hover:border-[#E94560] transition cursor-pointer">
              <CardContent className="pt-3 pb-3">
                <div className="flex items-center justify-between">
                  <p className="font-bold">{m.team_a_short} vs {m.team_b_short}</p>
                  {m.status === "LIVE" ? <Badge variant="live">LIVE</Badge> : <Badge>{m.status}</Badge>}
                </div>
                {m.result_summary && <p className="text-xs text-[#9E9E9E] mt-1">{m.result_summary}</p>}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
