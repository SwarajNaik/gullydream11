/**
 * Query key factories for React Query.
 * NEVER use raw string keys — always use these factories.
 */

export const authKeys = {
  all: ["auth"] as const,
  user: () => [...authKeys.all, "user"] as const,
};

export const matchKeys = {
  all: ["matches"] as const,
  list: (filters?: { status?: string; tournamentId?: number }) =>
    [...matchKeys.all, "list", filters] as const,
  detail: (matchId: number) => [...matchKeys.all, "detail", matchId] as const,
};

export const contestKeys = {
  all: ["contests"] as const,
  list: (matchId: number) => [...contestKeys.all, "list", matchId] as const,
  detail: (contestId: number) => [...contestKeys.all, "detail", contestId] as const,
  leaderboard: (contestId: number) =>
    [...contestKeys.all, "leaderboard", contestId] as const,
};

export const teamKeys = {
  all: ["teams"] as const,
  list: (matchId: number) => [...teamKeys.all, "list", matchId] as const,
  detail: (teamId: number) => [...teamKeys.all, "detail", teamId] as const,
};

export const playerKeys = {
  all: ["players"] as const,
  list: (matchId: number) => [...playerKeys.all, "list", matchId] as const,
  detail: (playerId: number) => [...playerKeys.all, "detail", playerId] as const,
};

export const walletKeys = {
  all: ["wallet"] as const,
  balance: () => [...walletKeys.all, "balance"] as const,
  transactions: (filters?: { type?: string }) =>
    [...walletKeys.all, "transactions", filters] as const,
};

export const leaderboardKeys = {
  all: ["leaderboard"] as const,
  global: (period: string) => [...leaderboardKeys.all, "global", period] as const,
  contest: (contestId: number) =>
    [...leaderboardKeys.all, "contest", contestId] as const,
};

export const scoringKeys = {
  all: ["scoring"] as const,
  match: (matchId: number) => [...scoringKeys.all, "match", matchId] as const,
};

export const adminKeys = {
  all: ["admin"] as const,
  dashboard: () => [...adminKeys.all, "dashboard"] as const,
  users: () => [...adminKeys.all, "users"] as const,
  settlements: () => [...adminKeys.all, "settlements"] as const,
};

export const settlementKeys = {
  all: ["settlements"] as const,
  iOwe: (filters?: { status?: string }) =>
    [...settlementKeys.all, "i-owe", filters] as const,
  owedToMe: (filters?: { status?: string }) =>
    [...settlementKeys.all, "owed-to-me", filters] as const,
  summary: () => [...settlementKeys.all, "summary"] as const,
  contest: (contestId: number) =>
    [...settlementKeys.all, "contest", contestId] as const,
};
