# DiaspoFinance

Plateforme de tontine digitale pour la diaspora. Collecte automatique, distribution transparente, zéro stress.

## Stack Technique

| Composant | Technologie |
|---|---|
| Frontend | Next.js 16.1, React 19, TypeScript, Tailwind 4, shadcn/ui |
| Backend | FastAPI 0.135, Python 3.12, SQLAlchemy async, Pydantic v2 |
| Base de données | PostgreSQL 18.3 |
| Cache | Redis 8.6 |
| Auth | Clerk |
| Paiements | Stripe Connect |

## Structure

```
DiaspoFinance/
├── frontend/          # Next.js (PWA)
├── backend/           # FastAPI
├── .github/workflows/ # CI/CD
└── README.md
```

## Démarrage rapide

### Prérequis

- Node.js >= 22, pnpm
- Python >= 3.12, uv
- PostgreSQL 18+
- Redis 8+

### Frontend

```bash
cd frontend
cp .env.example .env.local
pnpm install
pnpm dev
```

L'app sera disponible sur http://localhost:3000

### Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

L'API sera disponible sur http://localhost:8000

### Vérification

```bash
# Health check
curl http://localhost:8000/api/v1/health
```

## Scripts CI/CD

- `ci-frontend.yml` — Lint ESLint + build Next.js
- `ci-backend.yml` — Lint Ruff + tests pytest
- `deploy.yml` — Déploiement automatique (Vercel + Railway)

## Licence

Propriétaire — Tous droits réservés.
