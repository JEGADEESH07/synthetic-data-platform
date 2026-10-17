Synthetic Data Platform — Frontend

React and TypeScript web interface for the Synthetic Data Engineering & Privacy Platform.

Technology

React

TypeScript

Vite

ESLint

Prerequisites

Node.js

npm

The platform's FastAPI backend for live dashboard data and job operations

Development

From the repository root:

Set-Location .\frontend
npm install
npm run dev

Open http://localhost:5173/.

The Vite development server proxies requests beginning with /api to http://127.0.0.1:8000. Start the backend separately from the repository root:

.\.venv\Scripts\Activate.ps1
python -m uvicorn synthetic_data.api.app:app --app-dir src --host 127.0.0.1 --port 8000

Verification

Run these commands from the frontend directory:

npm run build
npm run lint

The build performs TypeScript checks and creates the production bundle in dist/. The lint command runs ESLint.

Main Workflows

The interface integrates with the backend for dashboard metrics, job visibility, CSV uploads, job status, and generated artifact access.

Actual operation results depend on backend availability, job state, and the API responses returned by the server.

Related Documentation

See the repository root README.md and docs/V0.4_RELEASE_AUDIT.md for the overall platform architecture and release verification record.