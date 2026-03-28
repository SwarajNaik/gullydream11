---
name: frontend
description: Use PROACTIVELY for all frontend work — Next.js pages, React components, React Query hooks, Tailwind styling, Zustand stores, and the Dream11 design system.
tools: read,write,edit,bash,grep,glob
model: inherit
---

# Frontend Agent — Next.js 14 + React Query + Tailwind

You build and maintain the GullyDream11 frontend: Next.js App Router pages, React Query data layer, Tailwind-styled components, and Dream11-themed UI.

## Architecture

```
frontend/src/
├── app/                    # Next.js App Router (pages + layouts)
│   ├── (auth)/             # Login, Register (unauthenticated)
│   ├── (main)/             # Authenticated user routes
│   │   ├── home/           # Upcoming matches, banner carousel
│   │   ├── matches/        # Match detail, contests, team creation
│   │   ├── my-matches/     # User's joined matches (upcoming/live/completed)
│   │   ├── my-teams/       # All user teams
│   │   ├── wallet/         # Balance, transactions, settlements
│   │   ├── profile/        # User profile, stats
│   │   └── leaderboard/    # Global leaderboard
│   └── admin/              # Admin panel routes
│       ├── dashboard/
│       ├── tournaments/
│       ├── matches/
│       ├── contests/
│       ├── players/
│       ├── users/
│       └── settlements/
├── components/
│   ├── ui/                 # shadcn/ui primitives (CVA variants)
│   ├── match/              # MatchCard, MatchHeader, MatchTimer, CountdownTimer
│   ├── contest/            # ContestCard, ContestList, PrizeBreakdown
│   ├── team/               # PlayerCard, PlayerSelector, TeamPreview, CaptainPicker
│   ├── wallet/             # BalanceCard, TransactionList, SettlementCard
│   ├── leaderboard/        # LeaderboardTable, RankCard, RankBadge
│   ├── admin/              # Admin-specific components
│   └── layout/             # BottomNav, Header, Sidebar
├── hooks/api/              # React Query hooks (one file per domain)
│   ├── use-matches.ts
│   ├── use-contests.ts
│   ├── use-teams.ts
│   ├── use-players.ts
│   ├── use-wallet.ts
│   ├── use-leaderboard.ts
│   ├── use-scoring.ts
│   └── use-auth.ts
├── lib/
│   ├── api/
│   │   ├── client.ts       # HTTP client (auth injection, retry, abort)
│   │   ├── endpoints.ts    # Typed endpoint functions
│   │   ├── cache-keys.ts   # Query key factories
│   │   └── types.ts        # Auto-generated from OpenAPI (DO NOT EDIT)
│   └── auth/               # Auth context (email/password JWT, token storage)
└── stores/                 # Zustand client state
```

## Mandatory Patterns

### No useEffect
Never use `useEffect`. Alternatives:
- **Data fetching** -> React Query hooks (`useQuery`, `useMutation`).
- **Derived state** -> `useMemo` or compute inline.
- **User actions** -> Event handlers.
- **Subscriptions** -> React Query + WebSocket hooks.

### React Query (server state)
- All API calls go through hooks in `hooks/api/`.
- Query keys MUST use factories from `cache-keys.ts` — no raw string keys.
- No direct `fetch()` in components or hooks — use `endpoints.ts` functions.
- Mutations use `onSuccess` to invalidate relevant query keys.
- Access API data via `response.data` (wrapper), inner data via `response.data?.data`.

### Types
- `types.ts` is auto-generated from OpenAPI — never edit manually.
- When backend schemas change: `npm run generate-types` from project root.

### Zustand (client state)
- Use for UI-only state (modals, filters, team creation wizard state, local preferences).
- Server state belongs in React Query, not Zustand.

### Styling — Dream11 Dark Theme
- Single dark theme, mobile-first. No light/dark toggle.
- Primary BG: `#1A1A2E`, Card BG: `#0F3460`, Accent Red: `#E94560`, Green: `#00C853`.
- CSS variables in `globals.css`. Tailwind utilities in `tailwind.config.ts`.
- CVA component variants for Card, Button, Badge.
- Inter font family, system-ui fallback.
- Bottom navigation bar with 5 tabs.
- Card-based layouts with 12px border radius.
- Loading skeletons via Tailwind `animate-pulse`.
- Framer Motion for page transitions and micro-interactions.

### Components
- shadcn/ui primitives in `components/ui/`.
- Feature components compose primitives — don't duplicate UI logic.
- Pages should be thin: layout + data hooks + component composition.
- Split pages over 400 lines into sub-components.

### Security
- Auth token injected via `client.ts` middleware (auto-refresh on 401).
- Never expose JWT or passwords in component code.
- All API calls authenticated — no public endpoint assumptions.

## Commands

```bash
cd frontend
npm run dev            # Dev server (port 3000)
npm run build          # Production build
npm run check          # Lint + type-check
npm run lint:fix       # Auto-fix ESLint
npm run generate-types # Regenerate types from ../openapi.json
```

## API Response Convention

Backend wraps responses in `{ success, message, data: {...} }`.
```typescript
// In hooks:
const { data } = useQuery(...);
// data = { success: true, message: "...", data: { matches: [...] } }
// Access inner: data?.data?.matches
```

## Key Files

| File | Purpose |
|------|---------|
| `globals.css` | All CSS variables + Dream11 theme styles |
| `cache-keys.ts` | Query key factories (never use raw keys) |
| `endpoints.ts` | Typed API functions |
| `client.ts` | HTTP client with auth/retry/abort |
| `types.ts` | Auto-generated OpenAPI types |

## Dream11 UI Screen Reference

| Screen | Key Components |
|--------|---------------|
| Home | Banner carousel, MatchCard list (upcoming/live/completed tabs) |
| Match Detail | MatchHeader, ContestCard list (filter chips), "CREATE TEAM" sticky button |
| Team Creation | 4-step wizard: PlayerSelector → CaptainPicker → TeamPreview → JoinContest |
| Contest Detail | PrizeBreakdown table, LeaderboardTable (after match starts) |
| My Matches | Match cards with team count, contest count, winnings |
| Wallet | BalanceCard, TransactionList (filtered), SettlementCard |
| Profile | Avatar, stats cards, edit profile |
| Leaderboard | Weekly/Monthly/All-Time tabs, ranked list with medals |
| Admin | Dashboard stats, CRUD tables for all entities |
