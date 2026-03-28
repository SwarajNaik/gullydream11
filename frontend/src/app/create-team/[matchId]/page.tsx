"use client";

import { useMemo, useCallback, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import { usePlayers } from "@/hooks/api/use-players";
import { useCreateTeam } from "@/hooks/api/use-teams";
import { useTeamCreationStore } from "@/stores/team-creation-store";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge, RoleBadge } from "@/components/ui/badge";

const ROLES = ["ALL", "WK", "BAT", "AR", "BOWL"];

// IPL team colors for visual distinction
const TEAM_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  RCB: { bg: "bg-red-900/30", text: "text-red-400", border: "border-red-800" },
  SRH: { bg: "bg-orange-900/30", text: "text-orange-400", border: "border-orange-800" },
  CSK: { bg: "bg-yellow-900/30", text: "text-yellow-400", border: "border-yellow-800" },
  MI: { bg: "bg-blue-900/30", text: "text-blue-400", border: "border-blue-800" },
  KKR: { bg: "bg-purple-900/30", text: "text-purple-400", border: "border-purple-800" },
  DC: { bg: "bg-blue-900/30", text: "text-blue-300", border: "border-blue-700" },
  RR: { bg: "bg-pink-900/30", text: "text-pink-400", border: "border-pink-800" },
  PBKS: { bg: "bg-red-900/30", text: "text-red-300", border: "border-red-700" },
  GT: { bg: "bg-cyan-900/30", text: "text-cyan-400", border: "border-cyan-800" },
  LSG: { bg: "bg-sky-900/30", text: "text-sky-400", border: "border-sky-800" },
};

const DEFAULT_TEAM_COLOR = { bg: "bg-[#2A2A4A]", text: "text-[#9E9E9E]", border: "border-[#2A2A4A]" };

function PlayerAvatar({ name, imageUrl, team }: { name: string; imageUrl?: string | null; team: string }) {
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const teamColor = TEAM_COLORS[team] || DEFAULT_TEAM_COLOR;

  if (imageUrl) {
    return (
      <div className={`relative h-10 w-10 shrink-0 overflow-hidden rounded-full border-2 ${teamColor.border}`}>
        <Image src={imageUrl} alt={name} fill className="object-cover" unoptimized />
      </div>
    );
  }

  return (
    <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 ${teamColor.border} ${teamColor.bg}`}>
      <span className={`text-xs font-bold ${teamColor.text}`}>{initials}</span>
    </div>
  );
}

function TeamBadge({ team }: { team: string }) {
  const color = TEAM_COLORS[team] || DEFAULT_TEAM_COLOR;
  return (
    <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold ${color.bg} ${color.text}`}>
      {team}
    </span>
  );
}

export default function CreateTeamPage() {
  const params = useParams();
  const router = useRouter();
  const matchId = Number(params.matchId);
  const [roleFilter, setRoleFilter] = useState("ALL");

  const { data } = usePlayers(matchId);
  const createTeam = useCreateTeam();
  const store = useTeamCreationStore();

  const allPlayers = (data as any)?.data?.players || [];
  const selectedIds = useMemo(() => new Set(store.selectedPlayers.map((p) => p.matchPlayerId)), [store.selectedPlayers]);
  const totalCredits = useMemo(() => store.selectedPlayers.reduce((s, p) => s + p.credits, 0), [store.selectedPlayers]);

  // Count per role for the tabs
  const roleCounts = useMemo(() => {
    const counts: Record<string, number> = { ALL: store.selectedPlayers.length };
    for (const p of store.selectedPlayers) {
      counts[p.role] = (counts[p.role] || 0) + 1;
    }
    return counts;
  }, [store.selectedPlayers]);

  const filteredPlayers = useMemo(() => {
    if (roleFilter === "ALL") return allPlayers;
    return allPlayers.filter((p: any) => p.player_role === roleFilter);
  }, [allPlayers, roleFilter]);

  const handleToggle = useCallback(
    (p: any) => {
      if (selectedIds.has(p.id)) {
        store.removePlayer(p.id);
      } else {
        store.addPlayer({
          matchPlayerId: p.id,
          playerId: p.player_id,
          name: p.player_name || "Unknown",
          team: p.team,
          role: p.player_role || "BAT",
          credits: p.credits,
        });
      }
    },
    [selectedIds, store]
  );

  const handleSave = useCallback(() => {
    if (!store.captainId || !store.viceCaptainId) return;
    createTeam.mutate(
      {
        match_id: matchId,
        name: `Team ${Date.now() % 100}`,
        captain_id: store.captainId,
        vice_captain_id: store.viceCaptainId,
        player_ids: store.selectedPlayers.map((p) => p.matchPlayerId),
      },
      {
        onSuccess: () => {
          store.reset();
          window.location.href = `/matches/${matchId}`;
        },
      }
    );
  }, [store, matchId, createTeam, router]);

  // ========== STEP 2: Captain/VC Selection ==========
  if (store.step === 2) {
    return (
      <div className="min-h-screen bg-[#1A1A2E]">
        <div className="bg-[#0F3460] p-4">
          <button onClick={() => store.setStep(1)} className="text-[#9E9E9E] mb-2">
            ← Back
          </button>
          <h2 className="text-lg font-bold">Choose Captain & Vice-Captain</h2>
          <p className="text-xs text-[#9E9E9E] mt-1">Captain gets 2x points, Vice-Captain gets 1.5x points</p>
        </div>

        <div className="p-4 space-y-2 pb-24">
          {store.selectedPlayers.map((p) => {
            // Find the full player data with image
            const fullPlayer = allPlayers.find((ap: any) => ap.id === p.matchPlayerId);
            return (
              <Card key={p.matchPlayerId}>
                <CardContent className="flex items-center justify-between pt-3 pb-3">
                  <div className="flex items-center gap-3">
                    <PlayerAvatar name={p.name} imageUrl={fullPlayer?.player_image_url} team={p.team} />
                    <div>
                      <p className="font-medium text-sm">{p.name}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <TeamBadge team={p.team} />
                        <RoleBadge role={p.role} />
                        <span className="text-xs text-[#666666]">{p.credits} cr</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => store.setCaptain(p.matchPlayerId)}
                      className={`h-9 w-9 rounded-full text-xs font-bold border-2 transition-all ${
                        store.captainId === p.matchPlayerId
                          ? "bg-[#E94560] border-[#E94560] text-white scale-110"
                          : "border-[#2A2A4A] text-[#9E9E9E] hover:border-[#E94560]"
                      }`}
                    >
                      C
                    </button>
                    <button
                      onClick={() => store.setViceCaptain(p.matchPlayerId)}
                      className={`h-9 w-9 rounded-full text-xs font-bold border-2 transition-all ${
                        store.viceCaptainId === p.matchPlayerId
                          ? "bg-[#00C853] border-[#00C853] text-white scale-110"
                          : "border-[#2A2A4A] text-[#9E9E9E] hover:border-[#00C853]"
                      }`}
                    >
                      VC
                    </button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="fixed bottom-0 left-0 right-0 z-50 bg-[#16213E] border-t border-[#2A2A4A] safe-bottom">
          <div className="px-4 py-2">
            <p className="text-xs text-center text-[#9E9E9E] mb-2">
              {!store.captainId && !store.viceCaptainId
                ? "Tap C for Captain (2x pts) and VC for Vice-Captain (1.5x pts)"
                : !store.captainId
                  ? "Select a Captain (C)"
                  : !store.viceCaptainId
                    ? "Select a Vice-Captain (VC)"
                    : "Ready to save!"}
            </p>
            <Button
              className="w-full"
              size="lg"
              disabled={!store.captainId || !store.viceCaptainId || createTeam.isPending}
              onClick={handleSave}
            >
              {createTeam.isPending ? "Saving Team..." : "SAVE TEAM"}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ========== STEP 1: Player Selection ==========
  return (
    <div className="min-h-screen bg-[#1A1A2E]">
      {/* Header */}
      <div className="bg-[#0F3460] p-4">
        <button onClick={() => { store.reset(); window.location.href = `/matches/${matchId}`; }} className="text-[#9E9E9E] mb-2">
          ← Back
        </button>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Create Team</h2>
          <div className="text-right">
            <p className="text-xs text-[#9E9E9E]">Credits Left</p>
            <p className="text-lg font-bold text-[#00C853]">{(100 - totalCredits).toFixed(1)}</p>
          </div>
        </div>
        {/* Player count bar */}
        <div className="mt-2 flex items-center gap-2">
          <div className="flex-1 h-1.5 rounded-full bg-[#1A1A2E]">
            <div
              className="h-full rounded-full bg-[#E94560] transition-all"
              style={{ width: `${(store.selectedPlayers.length / 11) * 100}%` }}
            />
          </div>
          <span className="text-xs font-medium">{store.selectedPlayers.length}/11</span>
        </div>
      </div>

      {/* Role Tabs with counts */}
      <div className="flex gap-1 p-3 overflow-x-auto">
        {ROLES.map((r) => (
          <button
            key={r}
            onClick={() => setRoleFilter(r)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium whitespace-nowrap transition ${
              roleFilter === r ? "bg-[#E94560] text-white" : "bg-[#0F3460] text-[#9E9E9E]"
            }`}
          >
            {r} {roleCounts[r] ? `(${roleCounts[r]})` : ""}
          </button>
        ))}
      </div>

      {/* Player List */}
      <div className="px-3 space-y-2 pb-36">
        {filteredPlayers.map((p: any) => {
          const selected = selectedIds.has(p.id);
          const disabled = !selected && (store.selectedPlayers.length >= 11 || totalCredits + p.credits > 100);

          return (
            <Card
              key={p.id}
              className={`transition-all ${
                selected ? "border-[#E94560] bg-[#E94560]/5" : disabled ? "opacity-40" : "hover:border-[#3A3A5A]"
              }`}
            >
              <CardContent className="flex items-center gap-3 pt-2.5 pb-2.5">
                {/* Player Photo */}
                <PlayerAvatar name={p.player_name || "?"} imageUrl={p.player_image_url} team={p.team} />

                {/* Player Info */}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm truncate">{p.player_name}</p>
                  <div className="flex items-center gap-1.5 mt-1">
                    <TeamBadge team={p.team} />
                    <RoleBadge role={p.player_role || "BAT"} />
                    {p.player_country && (
                      <span className="text-[10px] text-[#666666]">{p.player_country}</span>
                    )}
                  </div>
                </div>

                {/* Credits */}
                <div className="text-right shrink-0 mr-2">
                  <p className="text-sm font-bold">{p.credits}</p>
                  <p className="text-[10px] text-[#666666]">credits</p>
                </div>

                {/* Add/Remove Button */}
                <button
                  disabled={disabled}
                  onClick={() => handleToggle(p)}
                  className={`h-8 w-8 shrink-0 rounded-full text-sm font-bold transition-all ${
                    selected
                      ? "bg-[#E94560] text-white scale-110"
                      : disabled
                        ? "bg-[#1A1A2E] text-[#666666]"
                        : "bg-[#16213E] text-[#00C853] border border-[#00C853]/30 hover:border-[#00C853]"
                  }`}
                >
                  {selected ? "−" : "+"}
                </button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Bottom Bar — always visible */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-[#16213E] border-t border-[#2A2A4A] safe-bottom">
        <div className="flex items-center justify-between px-4 py-2">
          <div>
            <p className="text-[10px] text-[#9E9E9E]">Players</p>
            <p className="text-sm font-bold">{store.selectedPlayers.length}/11</p>
          </div>
          <div>
            <p className="text-[10px] text-[#9E9E9E]">Credits</p>
            <p className="text-sm font-bold">{totalCredits.toFixed(1)}/100</p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-[#9E9E9E]">
              {store.selectedPlayers.length < 11
                ? `Select ${11 - store.selectedPlayers.length} more`
                : "All selected!"}
            </p>
          </div>
        </div>
        <div className="px-4 pb-4">
          <Button
            className="w-full"
            size="lg"
            disabled={store.selectedPlayers.length !== 11}
            onClick={() => store.setStep(2)}
          >
            {store.selectedPlayers.length === 11
              ? "NEXT → Choose Captain & Vice-Captain"
              : `SELECT ${11 - store.selectedPlayers.length} MORE PLAYERS`}
          </Button>
        </div>
      </div>
    </div>
  );
}
