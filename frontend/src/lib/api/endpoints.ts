/**
 * Typed API endpoint functions.
 * All API calls go through apiClient — never use raw fetch().
 */

import { apiClient } from "./client";

// === Auth ===

export const authApi = {
  register: (data: {
    email: string;
    username: string;
    password: string;
    display_name: string;
    phone?: string;
  }) => apiClient.post("/auth/register", data),

  login: (data: { email_or_username: string; password: string }) =>
    apiClient.post("/auth/login", data),
};

// === Matches ===

export const matchApi = {
  list: (params?: { status?: string; tournament_id?: number }) =>
    apiClient.get("/matches", params),

  detail: (matchId: number) => apiClient.get(`/matches/${matchId}`),
};

// === Contests ===

export const contestApi = {
  list: (matchId: number) =>
    apiClient.get("/contests", { match_id: matchId }),

  detail: (contestId: number) => apiClient.get(`/contests/${contestId}`),

  join: (contestId: number, teamId: number) =>
    apiClient.post(`/contests/${contestId}/join`, undefined, { team_id: teamId }),
};

// === Teams ===

export const teamApi = {
  list: (matchId: number) =>
    apiClient.get("/teams", { match_id: matchId }),

  create: (data: {
    match_id: number;
    name: string;
    captain_id: number;
    vice_captain_id: number;
    player_ids: number[];
  }) => apiClient.post("/teams", data),

  detail: (teamId: number) => apiClient.get(`/teams/${teamId}`),
};

// === Players ===

export const playerApi = {
  list: (matchId: number) =>
    apiClient.get("/players", { match_id: matchId }),
};

// === Wallet ===

export const walletApi = {
  balance: () => apiClient.get("/wallet"),

  transactions: (params?: { type?: string; limit?: number; offset?: number }) =>
    apiClient.get("/wallet/transactions", params),

  topup: (data: { amount: number; note?: string }) =>
    apiClient.post("/wallet/topup", data),
};

// === Leaderboard ===

export const leaderboardApi = {
  global: (period: string = "all_time") =>
    apiClient.get("/leaderboard", { period }),
};

// === Scoring ===

export const scoringApi = {
  submit: (matchId: number, scores: unknown[]) =>
    apiClient.post(`/scoring/${matchId}`, { scores }),

  finalize: (matchId: number) =>
    apiClient.post(`/scoring/${matchId}/finalize`),
};

// === Admin ===

export const adminApi = {
  dashboard: () => apiClient.get("/admin/dashboard"),
  createTournament: (data: unknown) => apiClient.post("/admin/tournaments", data),
  createMatch: (data: unknown) => apiClient.post("/admin/matches", data),
  createContest: (data: unknown) => apiClient.post("/admin/contests", data),
  createPlayer: (data: unknown) => apiClient.post("/admin/players", data),
  listUsers: () => apiClient.get("/admin/users"),
  listSettlements: () => apiClient.get("/admin/settlements"),
  updateSettlement: (id: number, data: unknown) =>
    apiClient.put(`/admin/settlements/${id}`, data),
};

// === Settlements ===

export const settlementApi = {
  iOwe: (params?: { status?: string; limit?: number; offset?: number }) =>
    apiClient.get("/settlements/i-owe", params),
  owedToMe: (params?: { status?: string; limit?: number; offset?: number }) =>
    apiClient.get("/settlements/owed-to-me", params),
  summary: () => apiClient.get("/settlements/summary"),
  markPaid: (id: number, data?: { note?: string }) =>
    apiClient.post(`/settlements/${id}/mark-paid`, data || {}),
  confirmReceived: (id: number, data?: { note?: string }) =>
    apiClient.post(`/settlements/${id}/confirm-received`, data || {}),
  forContest: (contestId: number) =>
    apiClient.get(`/settlements/contest/${contestId}`),
};
