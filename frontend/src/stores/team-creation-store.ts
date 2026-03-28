import { create } from "zustand";

export interface SelectedPlayer {
  matchPlayerId: number;
  playerId: number;
  name: string;
  team: string;
  role: string;
  credits: number;
}

interface TeamCreationState {
  selectedPlayers: SelectedPlayer[];
  captainId: number | null;
  viceCaptainId: number | null;
  step: 1 | 2;
  addPlayer: (p: SelectedPlayer) => void;
  removePlayer: (matchPlayerId: number) => void;
  setCaptain: (id: number) => void;
  setViceCaptain: (id: number) => void;
  setStep: (s: 1 | 2) => void;
  reset: () => void;
}

export const useTeamCreationStore = create<TeamCreationState>((set) => ({
  selectedPlayers: [],
  captainId: null,
  viceCaptainId: null,
  step: 1,

  addPlayer: (p) =>
    set((state) => {
      if (state.selectedPlayers.length >= 11) return state;
      const totalCredits = state.selectedPlayers.reduce((s, pl) => s + pl.credits, 0) + p.credits;
      if (totalCredits > 100) return state;
      return { selectedPlayers: [...state.selectedPlayers, p] };
    }),

  removePlayer: (matchPlayerId) =>
    set((state) => ({
      selectedPlayers: state.selectedPlayers.filter((p) => p.matchPlayerId !== matchPlayerId),
      captainId: state.captainId === matchPlayerId ? null : state.captainId,
      viceCaptainId: state.viceCaptainId === matchPlayerId ? null : state.viceCaptainId,
    })),

  setCaptain: (id) =>
    set((state) => ({
      captainId: id,
      viceCaptainId: state.viceCaptainId === id ? null : state.viceCaptainId,
    })),

  setViceCaptain: (id) =>
    set((state) => ({
      viceCaptainId: id,
      captainId: state.captainId === id ? null : state.captainId,
    })),

  setStep: (s) => set({ step: s }),
  reset: () => set({ selectedPlayers: [], captainId: null, viceCaptainId: null, step: 1 }),
}));
