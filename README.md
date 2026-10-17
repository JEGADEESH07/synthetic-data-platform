Synthetic Data Engineering & Privacy Platform

V0.4 — Frontend Integration

A synthetic data engineering and privacy evaluation platform designed to generate synthetic datasets while evaluating schema integrity, statistical quality, and privacy risk.

V0.4 introduces a React-based web interface around the existing V0.2 synthetic-data engine and V0.3.1 execution backend.

Platform Architecture

Frontend: React, TypeScript, Vite

Backend: FastAPI, Python 3.12

Generation: SDV / CTGAN

Job persistence: SQLite

Job execution: In-process queue and background worker

Artifacts: Local filesystem

Testing: Pytest, TypeScript build, ESLint

The frontend communicates with the backend through the /api/v1/ API. Vite proxies frontend API requests to the local FastAPI server during development.

Features

Synthetic Data Engine

CSV ingestion and dataset profiling

Identifier detection and protection

Synthetic data generation

Schema validation

Statistical quality evaluation

Privacy risk evaluation

Execution Backend

Job creation and lifecycle management

SQLite-backed job persistence

Background job execution

Job status and artifact retrieval

Structured API errors and logging

Web Interface

Dashboard summary metrics

Job listing and status visibility

CSV upload and row-count configuration

Job progress/status monitoring

Artifact listing and downloads

Feature availability depends on the running backend and the corresponding API response. A successful privacy evaluation is not a guarantee against every possible privacy attack.

Project Structure

synthetic-data-platform/
├── src/synthetic_data/       # Backend and synthetic-data engine
├── tests/                    # Automated backend tests
├── frontend/                 # React + TypeScript application
├── docs/                     # Architecture and release documentation
├── config/                   # Application configuration
├── data/                     # Input data and generated outputs
├── scripts/                  # Utility scripts
├── Dockerfile
└── README.md

Development Setup

Prerequisites

Python 3.12

Node.js and npm

Git

Docker is optional for local development.

1. Start the backend

From the project root, activate the Python virtual environment if it is not already active:

.\.venv\Scripts\Activate.ps1

Start the API:

python -m uvicorn synthetic_data.api.app:app --app-dir src --host 127.0.0.1 --port 8000

Check the service:

Health: http://127.0.0.1:8000/api/v1/health

Readiness: http://127.0.0.1:8000/api/v1/readiness

Version: http://127.0.0.1:8000/api/v1/version

Keep this terminal running.

2. Start the frontend

Open a second PowerShell terminal:

Set-Location .\frontend
npm install
npm run dev

Open http://localhost:5173/ in your browser.

The Vite development server proxies /api requests to http://127.0.0.1:8000. Start the backend first so dashboard data and job operations can reach the API.

3. Verify the frontend

From the project root:

npm --prefix frontend run build
npm --prefix frontend run lint

The build runs TypeScript project checks and produces the production frontend bundle. ESLint checks frontend source and configuration.

4. Run backend tests

From the project root with the virtual environment active:

python -m pytest -q

Record the actual output when performing a new verification run; test counts and warnings can change as the code evolves.

API Overview

The V0.3.1 backend exposes these principal endpoints:

Method

Endpoint

Purpose

GET

/api/v1/health

Health status

GET

/api/v1/readiness

Readiness status

GET

/api/v1/version

Backend version

GET

/api/v1/...

Dashboard summary and job queries, where implemented

POST

/api/v1/jobs/upload

Upload a CSV and request generation

POST

/api/v1/jobs

Create a job from a server-accessible input file

GET

/api/v1/jobs/{job_id}

Retrieve job status

GET

/api/v1/jobs/{job_id}/artifacts

List job artifacts

GET

/api/v1/jobs/{job_id}/artifacts/{artifact_name}

Download an artifact

For exact request and response schemas, consult the backend API implementation and schemas.

Documentation

V0.3 Architecture

V0.3 Execution Orchestration

V0.3 Release Audit

V0.4 Release Audit — release verification record

The V0.3 documents are retained as historical architecture and release records.

Scope and Limitations

The platform currently uses a local execution architecture. The job queue is in-memory, the worker runs within the API process, job metadata is stored in SQLite, and artifacts are stored on the local filesystem.

The platform does not currently claim to provide distributed worker orchestration, horizontal scaling, production authentication and authorization, enterprise SSO, billing, multi-tenancy, or regulatory certification.

A privacy evaluation result is an assessment produced by the implemented checks. It is not legal advice or proof that a dataset is immune to re-identification, inference, or other privacy attacks.