# Hostel Repair Management System – Frontend

React + Vite dashboard for hall administrators and management staff. This UI consumes the FastAPI backend, mirrors the blue/white design system, and provides responsive layouts with sidebar navigation and Chart.js visualisations.

## Tech Stack

- Node 24 LTS (requires ≥18)
- React 18.2 + React Router 6.22
- Vite 7
- Tailwind CSS 3.4
- Chart.js 4.4 with `react-chartjs-2`
- Axios 1.6 (shared API client)

## Getting Started

```bash
cd frontend
npm install
cp .env.example .env.local    # adjust API base URL if needed
npm run dev                   # http://localhost:5173
```

Build and preview:

```bash
npm run build
npm run preview
```

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `VITE_API_BASE_URL` | Points to FastAPI backend (`/api` prefix included) | `http://localhost:8000/api` |

Vite automatically exposes variables prefixed with `VITE_`. Do **not** commit `.env.local`.

## Project Structure

```
src/
├── components/         # Reusable UI (buttons, cards, sidebar, KPI cards)
├── context/            # AuthProvider (JWT, user profile)
├── hooks/              # Custom hooks (useAuth)
├── layouts/            # Dashboard layout (sidebar + top bar)
├── pages/              # Route screens (login, dashboard, issues, detail)
├── services/           # Axios instance + API wrappers
└── index.css           # Tailwind + global styles
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm run lint` | ESLint (JS + JSX) |

## Design Notes

- Color tokens defined in `tailwind.config.js` mirror the spec from `HOSTEL_REPAIR_SYSTEM_CONTEXT.md`.
- Sidebar uses hamburger toggle on mobile and fixed layout on desktop.
- Chart.js demo data lives in `DashboardPage.jsx` until API endpoints are wired up.
- Components avoid emojis (Windows console limitation) and emphasize accessibility (contrast ratios, focus states).
