"use client";

import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMatch } from "@/hooks/api/use-matches";
import { useContests, useJoinContest } from "@/hooks/api/use-contests";
import { useTeams } from "@/hooks/api/use-teams";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MatchCardSkeleton } from "@/components/ui/skeleton";

export default function MatchDetailPage() {
  const params = useParams();
  const router = useRouter();
  const matchId = Number(params.matchId);
  const [tab, setTab] = useState<"contests" | "myteams">("contests");

  // Join contest state
  const [joiningContestId, setJoiningContestId] = useState<number | null>(null);
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
  const [joinError, setJoinError] = useState("");
  const [joinSuccess, setJoinSuccess] = useState("");

  const { data: matchData, isLoading: matchLoading } = useMatch(matchId);
  const { data: contestsData } = useContests(matchId);
  const { data: teamsData } = useTeams(matchId);
  const joinContest = useJoinContest();

  const match = (matchData as any)?.data;
  const contests = (contestsData as any)?.data?.contests || [];
  const teams = (teamsData as any)?.data?.teams || [];

  const handleJoinClick = useCallback((contestId: number) => {
    setJoinError("");
    setJoinSuccess("");
    if (teams.length === 0) {
      setJoinError("Create a team first!");
      return;
    }
    if (teams.length === 1) {
      // Auto-select the only team and join directly
      setJoiningContestId(contestId);
      setSelectedTeamId(teams[0].id);
    } else {
      // Show team selection
      setJoiningContestId(contestId);
      setSelectedTeamId(null);
    }
  }, [teams]);

  const handleConfirmJoin = useCallback(() => {
    if (!joiningContestId || !selectedTeamId) return;
    setJoinError("");

    joinContest.mutate(
      { contestId: joiningContestId, teamId: selectedTeamId },
      {
        onSuccess: () => {
          setJoinSuccess(`Joined contest successfully!`);
          setJoiningContestId(null);
          setSelectedTeamId(null);
          setTimeout(() => setJoinSuccess(""), 3000);
        },
        onError: (err: any) => {
          setJoinError(err.message || "Failed to join contest");
        },
      }
    );
  }, [joiningContestId, selectedTeamId, joinContest]);

  if (matchLoading) return <div className="p-4 space-y-3">{[1, 2].map(i => <MatchCardSkeleton key={i} />)}</div>;
  if (!match) return <p className="p-4 text-center text-[#666666]">Match not found</p>;

  return (
    <div className="min-h-screen pb-28">
      {/* Match Header */}
      <div className="bg-[#0F3460] p-4">
        <div className="flex items-center justify-between mb-2">
          <button onClick={() => router.push("/home")} className="text-[#9E9E9E]">← Back</button>
          {match.status === "LIVE" && <Badge variant="live">LIVE</Badge>}
          {match.status === "UPCOMING" && <Badge variant="default">UPCOMING</Badge>}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-center flex-1">
            <p className="text-2xl font-bold">{match.team_a_short}</p>
          </div>
          <span className="text-[#E94560] font-bold">VS</span>
          <div className="text-center flex-1">
            <p className="text-2xl font-bold">{match.team_b_short}</p>
          </div>
        </div>
        <p className="text-xs text-[#9E9E9E] text-center mt-1">
          {new Date(match.start_time).toLocaleString()} · {match.venue}
        </p>
      </div>

      {/* Success/Error Messages */}
      {joinSuccess && (
        <div className="mx-4 mt-3 rounded-lg bg-[#00C853]/20 border border-[#00C853]/50 p-3 text-center text-sm text-[#00C853]">
          {joinSuccess}
        </div>
      )}
      {joinError && (
        <div className="mx-4 mt-3 rounded-lg bg-[#E94560]/20 border border-[#E94560]/50 p-3 text-center text-sm text-[#E94560]">
          {joinError}
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-[#2A2A4A]">
        <button onClick={() => setTab("contests")} className={`flex-1 py-3 text-sm font-medium ${tab === "contests" ? "text-[#E94560] border-b-2 border-[#E94560]" : "text-[#9E9E9E]"}`}>
          Contests ({contests.length})
        </button>
        <button onClick={() => setTab("myteams")} className={`flex-1 py-3 text-sm font-medium ${tab === "myteams" ? "text-[#E94560] border-b-2 border-[#E94560]" : "text-[#9E9E9E]"}`}>
          My Teams ({teams.length})
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        {/* ===== CONTESTS TAB ===== */}
        {tab === "contests" && contests.map((c: any) => (
          <Card key={c.id}>
            <CardContent className="pt-3 pb-3">
              <div className="flex items-center justify-between mb-2">
                <p className="font-semibold">{c.name}</p>
                <div className="flex gap-1">
                  {c.is_guaranteed && <Badge variant="green">Guaranteed</Badge>}
                  <Badge variant="default">{c.type}</Badge>
                </div>
              </div>

              {/* Pool System Info */}
              <div className="flex items-center justify-between text-sm mb-1">
                <div>
                  <p className="text-[#9E9E9E] text-xs">Pool</p>
                  <p className="font-bold text-[#00C853]">₹{c.entry_fee * c.filled_spots}</p>
                </div>
                <div className="text-center">
                  <p className="text-[#9E9E9E] text-xs">Entry Fee</p>
                  <p className="font-bold">₹{c.entry_fee}</p>
                </div>
                <div className="text-right">
                  <p className="text-[#9E9E9E] text-xs">Top 3 Win</p>
                  <p className="font-bold text-[#FFD600]">50/30/20%</p>
                </div>
              </div>
              {/* Estimated prizes */}
              {c.filled_spots > 0 && (
                <div className="flex justify-between text-[10px] text-[#666666] mb-2 px-1">
                  <span>1st: ₹{Math.round(c.entry_fee * c.filled_spots * 0.5)}</span>
                  <span>2nd: ₹{Math.round(c.entry_fee * c.filled_spots * 0.3)}</span>
                  <span>3rd: ₹{Math.round(c.entry_fee * c.filled_spots * 0.2)}</span>
                </div>
              )}

              {/* Spots progress */}
              <div className="mb-3">
                <div className="flex justify-between text-xs text-[#9E9E9E] mb-1">
                  <span>{c.filled_spots} joined</span>
                  <span>{c.max_spots - c.filled_spots} left</span>
                </div>
                <div className="h-1.5 rounded-full bg-[#1A1A2E]">
                  <div className="h-full rounded-full bg-[#E94560] transition-all" style={{ width: `${(c.filled_spots / c.max_spots) * 100}%` }} />
                </div>
              </div>

              {/* JOIN button or team selector */}
              {joiningContestId === c.id ? (
                <div className="space-y-2">
                  <p className="text-xs text-[#9E9E9E] font-medium">Select team to enter:</p>
                  {teams.map((t: any) => (
                    <button
                      key={t.id}
                      onClick={() => setSelectedTeamId(t.id)}
                      className={`w-full text-left rounded-lg p-2.5 text-sm transition border ${
                        selectedTeamId === t.id
                          ? "bg-[#E94560]/10 border-[#E94560] text-white"
                          : "bg-[#1A1A2E] border-[#2A2A4A] text-[#9E9E9E]"
                      }`}
                    >
                      <span className="font-medium">{t.name}</span>
                      <span className="text-xs ml-2">({t.total_credits} cr)</span>
                    </button>
                  ))}
                  <div className="flex gap-2 mt-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      className="flex-1"
                      onClick={() => { setJoiningContestId(null); setSelectedTeamId(null); }}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      className="flex-1"
                      disabled={!selectedTeamId || joinContest.isPending}
                      onClick={handleConfirmJoin}
                    >
                      {joinContest.isPending ? "Joining..." : `JOIN ₹${c.entry_fee}`}
                    </Button>
                  </div>
                </div>
              ) : (
                <Button
                  className="w-full"
                  size="sm"
                  disabled={c.filled_spots >= c.max_spots}
                  onClick={() => handleJoinClick(c.id)}
                >
                  {c.filled_spots >= c.max_spots ? "FULL" : `JOIN ₹${c.entry_fee}`}
                </Button>
              )}
            </CardContent>
          </Card>
        ))}

        {/* ===== MY TEAMS TAB ===== */}
        {tab === "myteams" && (
          <>
            {teams.length === 0 && (
              <div className="text-center py-8">
                <p className="text-[#666666] mb-4">No teams created yet</p>
                <Button onClick={() => router.push(`/create-team/${matchId}`)}>
                  CREATE YOUR FIRST TEAM
                </Button>
              </div>
            )}
            {teams.map((t: any) => (
              <Card key={t.id}>
                <CardContent className="pt-3 pb-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold">{t.name}</p>
                      <p className="text-xs text-[#9E9E9E] mt-0.5">
                        Credits: {t.total_credits}/100 · Points: {t.total_points}
                      </p>
                    </div>
                    <Badge variant="green">Created</Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </>
        )}
      </div>

      {/* Sticky Bottom: Create Team */}
      <div className="fixed bottom-20 left-0 right-0 px-4 pb-2 z-40">
        <Button className="w-full" size="lg" onClick={() => router.push(`/create-team/${matchId}`)}>
          {teams.length === 0 ? "CREATE TEAM" : "+ CREATE ANOTHER TEAM"}
        </Button>
      </div>
    </div>
  );
}
