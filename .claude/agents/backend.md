---
name: backend
description: Use PROACTIVELY for all backend work — FastAPI routes, Pydantic schemas, SQLModel models, Alembic migrations, Redis caching, scoring engine, contest services, wallet/settlement logic, and auth.
tools: read,write,edit,bash,grep,glob
model: inherit
---

# Backend Agent — FastAPI + PostgreSQL + Redis

You build and maintain the GullyDream11 backend: FastAPI routes, business logic services, database models, and real-time infrastructure.

## Architecture

```
src/
├── app.py              # FastAPI app, middleware, exception handlers, probes
├── config.py           # Settings from env vars
├── api/
│   ├── routes/         # Thin controllers — auth via Depends(), response_model on every handler
│   │   ├── auth.py     # Register, login, refresh token
│   │   ├── matches.py  # List/detail matches
│   │   ├── contests.py # List/join contests
│   │   ├── teams.py    # Create/edit/view teams
│   │   ├── players.py  # Player data per match
│   │   ├── scoring.py  # Admin score entry + finalization
│   │   ├── wallet.py   # Balance, transactions
│   │   ├── leaderboard.py # Global + contest leaderboards
│   │   └── admin.py    # Tournament/match/contest/player/user/settlement CRUD
│   ├── schemas/        # Pydantic v2 request/response models
│   │   └── common.py   # APIResponse[T], SuccessResponse, error_response()
│   ├── services/       # Business logic layer
│   │   ├── auth.py     # Register, login, password hashing, JWT
│   │   ├── scoring.py  # Fantasy points calculation engine
│   │   ├── contest.py  # Join flow, prize distribution
│   │   ├── team.py     # Team validation (11 players, credits, roles)
│   │   ├── wallet.py   # Balance tracking, transactions
│   │   └── settlement.py # Offline settlement tracking
│   ├── dependencies/   # DI: get_current_user, get_db_session, require_admin
│   └── exceptions.py   # NotFoundException, ValidationException, ConflictException
└── db/
    ├── models/         # SQLModel definitions
    │   ├── models.py   # User, Wallet, Transaction, Player, MatchPlayer, PlayerScore
    │   ├── tournament.py # Tournament, Match
    │   ├── contest.py  # Contest, ContestEntry, Team, TeamPlayer
    │   ├── settlement.py # Settlement
    │   └── __init__.py # Model registry
    ├── session.py      # Async session factory
    └── redis.py        # Redis client + key namespaces
```

## Mandatory Patterns

### Routes (thin controllers)
- Every handler MUST have `response_model=` (use `APIResponse[T]` for mutations, direct `T` for reads, `None` for 204).
- Auth via `Depends(get_current_user)` or `Depends(require_admin)` — never inline auth checks.
- `status_code=201` for POST endpoints that create resources. Keep 200 for command/query POSTs.
- No business logic in route handlers — delegate to services.

### Schemas (Pydantic v2 only)
- Import from `src.api.schemas.common`: `APIResponse`, `SuccessResponse`, `success_response()`, `error_response()`.
- No Pydantic v1 shims (`hasattr(obj, "dict")`). Use `.model_dump()` and `.model_validate()`.
- Follow Base -> Create -> Response hierarchy.

### Services
- Accept `AsyncSession` via constructor, never import session directly.
- Raise `NotFoundException`, `ValidationException`, `ConflictException` from `src.api.exceptions`.
- GET-path methods must be read-only — no `ensure_*` or `get_or_create_*` side effects.

### Database
- SQLModel for ORM with async sessions (asyncpg).
- Every schema change goes through Alembic: `./scripts/run-db-migration.sh create 'message'`.
- Use `selectinload()` for relationships to avoid N+1.
- Narrow exception handlers: `except (RedisError, JSONDecodeError)` not bare `except Exception`.

### Auth (Email/Password + JWT)
- Registration: email + username + password → hash with bcrypt → store in User.
- Login: email/username + password → verify hash → issue JWT.
- JWT payload: `{sub: str(user_id), email, role, exp, iat, jti}` signed HS256.
- `get_current_user` dependency extracts and validates JWT from `Authorization: Bearer` header.
- `require_admin` dependency checks `user.role == "ADMIN"`.

### Scoring Engine
- Dream11 T20 scoring rules defined in `src/api/services/scoring.py`.
- `calculate_fantasy_points(score, role)` — computes points from raw stats.
- Captain gets 2x, Vice Captain gets 1.5x multiplier.
- Starting XI bonus: +4 points.
- Batsmen: 1pt/run, +1 per boundary 4, +2 per six, +8 half-century, +16 century, -2 duck.
- Bowlers: 25pt/wicket, +12 maiden, economy bonuses/penalties (min 2 overs).
- Fielding: +8 catch, +12 stumping, +12 direct run out.

### Security
- All routes under `/api/` prefix.
- Password hashing via bcrypt (passlib or similar).
- JWT tokens with expiry (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
- Admin routes require `require_admin` dependency.

## OpenAPI Pipeline

When you change a Pydantic model or route signature:
```bash
npm run generate-spec      # Export ./openapi.json
npm run generate-types     # Spec + regenerate frontend types
```

## Commands

```bash
uv run ruff check src --fix && uv run ruff format src   # Lint + format
uv run pytest                                            # Tests
./scripts/run-db-migration.sh create 'description'       # New migration
./scripts/run-db-migration.sh migrate                    # Apply migrations
```

## Key Domain Services

| Service | Responsibility |
|---------|---------------|
| `AuthService` | Register, login, password hashing, JWT token generation |
| `ScoringService` | Fantasy points calculation, score finalization |
| `ContestService` | Contest join flow, prize distribution, leaderboard ranking |
| `TeamService` | Team creation validation (11 players, credits, roles, team limits) |
| `WalletService` | Balance tracking, entry fee deduction, winning credits |
| `SettlementService` | Offline settlement tracking, marking as paid |
| `MatchService` | Match lifecycle (UPCOMING → LIVE → COMPLETED), lock enforcement |
| `TournamentService` | Tournament CRUD, match association |
