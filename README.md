# Synthetic Data Platform

A production-oriented synthetic data generation platform built around privacy-aware data processing, synthetic-data quality evaluation, quality-gated regeneration, persistent job tracking, attempt-level observability, and artifact management.

The platform started as a local synthetic-data generation pipeline and has evolved into a service-oriented application capable of treating synthetic-data generation as a managed job rather than a single execution.

---

# Current Version

## V0.3.0 — Job Orchestration & Quality-Gated Generation

V0.3 introduces the first major application architecture layer around the original V0.2 synthetic-data pipeline.

The platform now supports:

- Job creation and persistent job tracking
- Generation attempt tracking
- Quality-gated synthetic-data generation
- Automatic regeneration when quality requirements are not met
- Configurable quality policies
- Trust-score evaluation
- Schema validation
- Privacy evaluation
- Statistical fidelity evaluation
- Attempt selection
- Job-level and attempt-level status
- Persistent SQLite job storage
- Per-job and per-attempt artifact storage
- REST API endpoints
- Artifact download endpoints
- FastAPI application layer
- Application service layer
- API integration tests
- Docker-ready application structure
- Backward-compatible use of the existing synthetic-data pipeline

---

# 1. What Is This Project?

Synthetic Data Platform is an application for generating synthetic datasets from real input data while evaluating the resulting synthetic data against configurable quality and privacy requirements.

The platform is designed around a simple principle:

> Synthetic-data generation should not be considered successful merely because synthetic rows were generated.

A generation attempt must also be evaluated.

If the generated dataset does not satisfy the configured quality policy, the platform can automatically generate another attempt.

The resulting workflow is:

```text
Real Dataset
     |
     v
Dataset Ingestion
     |
     v
Dataset Profiling
     |
     v
Identifier Detection
     |
     v
Identifier Separation
     |
     v
Metadata Detection
     |
     v
Synthetic Data Generation
     |
     v
Evaluation
     |
     +-----------------------------+
     |                             |
     | Quality Gate Passed         | Quality Gate Failed
     |                             |
     v                             v
 Select Attempt              Regenerate
     |                             |
     |                             v
     |                       New Attempt
     |                             |
     |<----------------------------+
     |
     v
Persist Result
     |
     v
Expose Job + Artifacts
# 2. V0.3 Architecture

V0.3 introduces a layered application architecture around the original generation pipeline.

                         REST API
                            |
                            v
                    +---------------+
                    |   API Layer   |
                    |   FastAPI      |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    | Service Layer |
                    | SyntheticData |
                    | Service       |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    |   Pipeline    |
                    |   Execution   |
                    +-------+-------+
                            |
            +---------------+---------------+
            |               |               |
            v               v               v
       Ingestion       Generation       Evaluation
            |               |               |
            |               |       +-------+-------+
            |               |       |       |       |
            |               |       v       v       v
            |               |    Schema  Privacy  Statistical
            |               |    Quality Quality Fidelity
            |               |       |
            |               |       v
            |               |   Trust Score
            |               |       |
            |               +-------+
            |                       |
            +-----------------------+
                            |
                            v
                    +---------------+
                    | Quality Gate  |
                    +-------+-------+
                            |
                  +---------+---------+
                  |                   |
                PASS                FAIL
                  |                   |
                  v                   v
          Attempt Selection      Regeneration
                  |                   |
                  +---------+---------+
                            |
                            v
                    +---------------+
                    |   Job Store   |
                    |    SQLite     |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    | Artifact Store|
                    |  Filesystem   |
                    +---------------+
# 3. V0.3 Design Goals

V0.3 focuses on moving the project from a pipeline-oriented application toward an application-oriented architecture.

The main goals are:

## 3.1 Treat generation as a job

A generation request creates a job with a unique job_id.

The job has a lifecycle independent of the HTTP request that created it.

## 3.2 Treat every generation as an attempt

A job can contain multiple generation attempts.

For example:

Job
 |
 +-- Attempt 1 → quality_failed
 |
 +-- Attempt 2 → completed
## 3.3 Make quality a decision point

Generation is evaluated before the job is considered successful.

## 3.4 Support controlled regeneration

When quality requirements are not satisfied, the platform can regenerate the dataset according to the configured policy.

## 3.5 Preserve attempt history

Failed attempts are not discarded.

They remain available for inspection and debugging.

## 3.6 Persist operational state

Jobs and attempts are persisted using SQLite.

## 3.7 Separate artifacts from application state

Generated datasets and evaluation reports are stored as filesystem artifacts.

# 4. V0.3 Features
## 4.1 Job Management

Every generation request creates a job.

A job contains information such as:

job_id
status
created_at
started_at
completed_at
error
result
artifacts

Example job lifecycle:

queued
  |
  v
running
  |
  +----------------+
  |                |
  v                v
completed        failed

A job may also contain multiple attempts.

# 5. Generation Attempts

A JobAttempt represents one individual synthetic-data generation execution.

Each attempt contains:

attempt_id
job_id
attempt_number
status
created_at
completed_at
error
trust_score
quality_gate
artifacts

Example:

Job: bbcca467...

Attempt 1
---------
Status: quality_failed
Trust Score: 0.6717
Quality Gate: failed

Attempt 2
---------
Status: completed
Trust Score: 0.7260
Quality Gate: passed

The platform therefore preserves the complete regeneration history instead of exposing only the final dataset.

# 6. Quality Policy

V0.3 introduces an explicit quality policy.

The default policy is:

minimum_trust_score = 0.70
require_schema_valid = True
require_privacy_safe = True
mode = regenerate
max_regeneration_attempts = 3

Conceptually:

QualityPolicy(
    minimum_trust_score=0.70,
    require_schema_valid=True,
    require_privacy_safe=True,
    mode="regenerate",
    max_regeneration_attempts=3,
)

The quality policy controls whether an attempt is accepted.

# 7. Quality Gate

The quality gate determines whether a generation attempt is acceptable.

The gate considers:

Trust score

The generated dataset must achieve at least the configured minimum trust score.

Default:

0.70
Schema validity

The generated dataset must satisfy schema requirements when schema validation is required.

Privacy safety

The generated dataset must satisfy the configured privacy requirement.

The final decision can therefore be represented as:

Trust Score >= Minimum
        AND
Schema Valid
        AND
Privacy Safe
        |
        v
   Quality Passed

If any required condition fails:

Quality Failed
# 8. Quality Policy Modes

V0.3 supports three policy modes:

report
block
regenerate
Report

The quality result is reported without triggering regeneration.

Block

The quality result prevents successful completion when requirements are not met.

Regenerate

The platform automatically creates another generation attempt until:

the quality gate passes, or
the maximum number of attempts is reached.

The default mode is:

regenerate
# 9. Regeneration Workflow

The regeneration workflow is one of the central features of V0.3.

Example:

Attempt 1
Trust Score = 0.6717
Quality Gate = FAIL
        |
        v
Regenerate
        |
        v
Attempt 2
Trust Score = 0.7260
Quality Gate = PASS
        |
        v
Job Completed

The job result records regeneration information.

Example:

{
  "regeneration": {
    "enabled": true,
    "attempts_used": 1,
    "max_attempts": 3,
    "regenerated": true,
    "stopping_reason": "quality_gate_passed"
  }
}

If all attempts fail:

{
  "regeneration": {
    "enabled": true,
    "attempts_used": 3,
    "max_attempts": 3,
    "regenerated": true,
    "stopping_reason": "max_attempts_reached"
  }
}
# 10. Attempt Selection

When multiple attempts exist, the platform selects the appropriate attempt as the job's best/selected attempt.

A successful example:

Attempt 1 → quality_failed
Attempt 2 → completed

The selected attempt becomes:

Attempt 2

The API exposes information about the selected attempt.

Example:

{
  "selected_attempt": {
    "attempt_id": "5ce026c8-e836-4a53-beeb-e10af3e455ca",
    "attempt_number": 2,
    "trust_score": 0.7259992341844775,
    "status": "completed"
  }
}
# 11. Evaluation Architecture

The evaluation subsystem is divided into multiple concerns.

Evaluation Engine
      |
      +-- Schema Evaluation
      |
      +-- Statistical Fidelity
      |
      +-- Privacy Evaluation
      |
      +-- Trust Evaluation
      |
      +-- Confidence Evaluation
      |
      +-- Quality Gate
      |
      +-- Attempt Selection

This separation allows individual evaluation components to evolve independently.

# 12. Schema Evaluation

The platform evaluates whether the generated dataset maintains the expected schema.

The evaluation includes information such as:

real_column_count
synthetic_column_count
missing_columns
unexpected_columns
column_order_match
valid

Example:

{
  "schema": {
    "valid": true,
    "real_column_count": 5,
    "synthetic_column_count": 5,
    "missing_columns": [],
    "unexpected_columns": [],
    "column_order_match": true
  }
}
# 13. Statistical Fidelity

The statistical evaluation layer measures how closely the synthetic dataset resembles the source dataset from a statistical perspective.

The V0.3 evaluation subsystem contains a dedicated statistical-fidelity implementation.

The evaluation contributes to the broader synthetic-data quality assessment.

# 14. Privacy Evaluation

Privacy evaluation remains part of the platform's quality decision.

The pipeline continues to detect and separate identifier columns before synthetic-data training.

The architecture therefore maintains the V0.2 privacy-aware processing flow while integrating its results into the V0.3 quality pipeline.

# 15. Trust Score

V0.3 introduces a unified trust-oriented evaluation concept.

The trust score provides a normalized signal that can be used by the quality gate.

The default minimum threshold is:

0.70

Example:

Trust Score = 0.6717
Required     = 0.7000
Result       = FAIL

and:

Trust Score = 0.7260
Required     = 0.7000
Result       = PASS
# 16. Confidence Evaluation

The evaluation subsystem also contains confidence-related evaluation functionality.

Confidence information can be retained alongside:

schema
statistical_quality
privacy
trust

This allows future versions to build more sophisticated quality and confidence decision mechanisms without restructuring the entire evaluation system.

# 17. Persistent Job Store

V0.3 introduces a persistent SQLite-backed job store.

Default location:

data/output/jobs.db

The job store persists:

Jobs
Attempts
Status
Timestamps
Errors
Trust scores
Quality-gate results
Attempt artifacts
Job artifacts
Result metadata

This means job state survives beyond the lifetime of an individual Python function call.

# 18. Job Storage Model

Conceptually:

jobs
 |
 +-- job_id
 +-- status
 +-- created_at
 +-- started_at
 +-- completed_at
 +-- error
 +-- result
 +-- artifacts

job_attempts
 |
 +-- attempt_id
 +-- job_id
 +-- attempt_number
 +-- status
 +-- created_at
 +-- completed_at
 +-- error
 +-- trust_score
 +-- quality_gate
 +-- artifacts

The relationship is:

One Job
   |
   +---- Attempt 1
   |
   +---- Attempt 2
   |
   +---- Attempt 3
# 19. Artifact Storage

V0.3 introduces a dedicated ArtifactStore.

Artifacts are organized by job and attempt.

The structure is:

data/
└── output/
    └── jobs/
        └── <job_id>/
            ├── synthetic_data.csv
            ├── evaluation_report.json
            ├── attempt_1/
            │   ├── synthetic_data.csv
            │   └── evaluation_report.json
            ├── attempt_2/
            │   ├── synthetic_data.csv
            │   └── evaluation_report.json
            └── ...

Attempt-specific artifacts prevent one generation attempt from overwriting another.

# 20. Artifact Types

The platform currently manages two primary artifacts.

Synthetic Dataset
synthetic_data.csv
Evaluation Report
evaluation_report.json

The API can expose artifacts belonging to the selected attempt.

Example:

{
  "job_id": "bbcca467-0f18-400a-a6a9-5cc39c8639d1",
  "selected_attempt": {
    "attempt_id": "5ce026c8-e836-4a53-beeb-e10af3e455ca",
    "attempt_number": 2,
    "trust_score": 0.7259992341844775,
    "status": "completed"
  },
  "artifacts": {
    "synthetic_data": "data/output/jobs/bbcca467-0f18-400a-a6a9-5cc39c8639d1/attempt_2/synthetic_data.csv",
    "evaluation_report": "data/output/jobs/bbcca467-0f18-400a-a6a9-5cc39c8639d1/attempt_2/evaluation_report.json"
  }
}
# 21. REST API

V0.3 introduces a FastAPI-based REST API.

Application entry point:

app/api/main.py
# 22. Health Endpoint
GET /health

Used to determine whether the application is running.

# 23. Readiness Endpoint
GET /readiness

Used to determine whether the application is ready to serve requests.

# 24. Generate Endpoint
POST /api/v1/generate

The endpoint accepts a dataset and generation parameters.

Example:

curl -X POST http://localhost:8000/api/v1/generate \
  -F "file=@data/input/sample.csv" \
  -F "rows=100" \
  -F "epochs=300"

Example response:

{
  "job_id": "851b61f0-41bf-4621-b0df-4878833fb62f",
  "status": "queued",
  "message": "Generation job created."
}

The returned job_id is then used to inspect the generation job.

# 25. Job Status Endpoint
GET /api/v1/jobs/{job_id}

Example:

curl http://localhost:8000/api/v1/jobs/<job_id>

The response contains:

Job status
Timestamps
Error information
Result metadata
Selected attempt
All attempts
Artifacts

Conceptually:

{
  "job_id": "...",
  "status": "completed",
  "created_at": "...",
  "started_at": "...",
  "completed_at": "...",
  "error": null,
  "result": {},
  "selected_attempt": {},
  "attempts": [],
  "artifacts": {}
}
# 26. Attempt Endpoint

Individual attempts can be inspected through the attempt-level API.

The response identifies:

Parent job
Attempt information
Whether the attempt was selected

This provides visibility into individual generation executions rather than only the final job state.

# 27. Job Artifacts Endpoint
GET /api/v1/jobs/{job_id}/artifacts

Example:

curl http://localhost:8000/api/v1/jobs/<job_id>/artifacts

Example response:

{
  "job_id": "...",
  "selected_attempt": {
    "attempt_id": "...",
    "attempt_number": 2,
    "trust_score": 0.7259992341844775,
    "status": "completed"
  },
  "artifacts": {
    "synthetic_data": "data/output/jobs/.../attempt_2/synthetic_data.csv",
    "evaluation_report": "data/output/jobs/.../attempt_2/evaluation_report.json"
  }
}
# 28. Artifact Download Endpoint

Synthetic data:

GET /api/v1/jobs/{job_id}/artifacts/synthetic_data

Evaluation report:

GET /api/v1/jobs/{job_id}/artifacts/evaluation_report

Example:

curl -o synthetic_data.csv \
http://localhost:8000/api/v1/jobs/<job_id>/artifacts/synthetic_data

Example:

curl -o evaluation_report.json \
http://localhost:8000/api/v1/jobs/<job_id>/artifacts/evaluation_report
# 29. Application Service Layer

V0.3 introduces an application service layer:

app/services/synthetic_data_service.py

The service provides an application-level abstraction around the existing pipeline.

API
 |
 v
SyntheticDataService
 |
 v
run_pipeline()

This separation prevents the API layer from becoming tightly coupled to the internal pipeline implementation.

# 30. Existing V0.2 Pipeline

The original generation pipeline remains the foundation of V0.3.

The pipeline continues to perform:

# 1. Parameter validation
# 2. Dataset ingestion
# 3. Dataset profiling
# 4. Identifier detection
# 5. Identifier separation
# 6. Metadata detection
# 7. CTGAN training
# 8. Synthetic-data generation
# 9. Identifier generation
# 10. Evaluation
# 11. Artifact writing

V0.3 wraps this pipeline with job orchestration and quality-gated execution.

# 31. Data Ingestion

Supported file types:

.csv
.xlsx
.xls

The ingestion layer validates:

Input type
File existence
File path validity
Supported extension
Empty files
Empty datasets
Missing columns

The loader is implemented in:

app/ingestion/loader.py
# 32. Identifier Protection

The platform detects identifier columns before synthetic-data training.

The workflow is:

Real Dataset
     |
     v
Identifier Detection
     |
     +----------------------+
     |                      |
     v                      v
Identifiers            Training Data
     |                      |
     v                      v
Protected             CTGAN Training

Identifiers are therefore separated from the training data and handled independently.

# 33. Synthetic Data Generation

The platform currently uses the CTGAN-based generation implementation inherited from V0.2.

The generation layer is located under:

app/generation/

The application validates generation parameters before training.

# 34. Generation Parameter Validation

The platform validates:

Output rows

Default:

100

Allowed range:

1 → 1,000,000
Epochs

Default:

300

Allowed range:

1 → 10,000

These values are configurable through PipelineConfig.

# 35. Configuration

Configuration is defined in:

app/config/settings.py

Default pipeline configuration:

default_epochs = 300
default_output_rows = 100

default_output_data_path =
data/output/synthetic_data.csv

default_output_report_path =
data/output/evaluation_report.json

max_output_rows = 1,000,000
min_output_rows = 1

min_epochs = 1
max_epochs = 10,000

job_database_path =
data/output/jobs.db

Default quality configuration:

minimum_trust_score = 0.70
require_schema_valid = True
require_privacy_safe = True
mode = regenerate
max_regeneration_attempts = 3
# 36. Configuration Validation

Quality-policy configuration is validated before use.

The platform validates:

## 0.0 <= minimum_trust_score <= 1.0

Supported modes:

report
block
regenerate

Regeneration attempts must not be negative.

Regeneration mode requires at least one regeneration attempt.

# 37. Error Handling

V0.3 distinguishes between:

Invalid input
Invalid generation parameters
Missing jobs
Missing attempts
Missing artifacts
Failed generation
Quality-gate failure
Maximum regeneration attempts reached

API errors are represented through appropriate HTTP responses.

For example:

404
Job not found.

or:

404
No artifacts available for this job.
# 38. Job Lifecycle

A typical successful job:

POST /api/v1/generate
        |
        v
      queued
        |
        v
     running
        |
        v
Create Attempt 1
        |
        v
Generate Data
        |
        v
Evaluate
        |
        v
Quality Gate
        |
        v
     PASSED
        |
        v
   completed

A regeneration scenario:

queued
  |
  v
running
  |
  v
Attempt 1
  |
  v
quality_failed
  |
  v
Attempt 2
  |
  v
completed

A complete failure scenario:

Attempt 1 → quality_failed
Attempt 2 → quality_failed
Attempt 3 → quality_failed
                  |
                  v
                failed
# 39. Example Quality-Gated Job

Suppose the configured policy is:

Minimum trust score = 0.70
Maximum attempts = 3

The platform receives:

Customer dataset
Attempt 1
Trust score = 0.6717
Schema = valid
Privacy = safe

Quality Gate = FAIL

The platform records:

attempt_number = 1
status = quality_failed
trust_score = 0.6717

Then regeneration occurs.

Attempt 2
Trust score = 0.7260
Schema = valid
Privacy = safe

Quality Gate = PASS

The platform records:

attempt_number = 2
status = completed
trust_score = 0.7260

The job selects attempt 2.

# 40. Project Structure

Current V0.3 structure:

synthetic-data-platform/
│
├── app/
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── attempt_selector.py
│   │   ├── confidence.py
│   │   ├── evaluator.py
│   │   ├── models.py
│   │   ├── quality_gate.py
│   │   ├── quality_policy.py
│   │   ├── statistical_fidelity.py
│   │   └── trust.py
│   │
│   ├── generation/
│   │   └── ...
│   │
│   ├── ingestion/
│   │   └── loader.py
│   │
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── attempts.py
│   │   ├── models.py
│   │   └── store.py
│   │
│   ├── logging/
│   │   └── ...
│   │
│   ├── privacy/
│   │   └── ...
│   │
│   ├── profiling/
│   │   └── ...
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── synthetic_data_service.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── artifacts.py
│   │
│   ├── validation/
│   │   └── ...
│   │
│   ├── cli.py
│   ├── main.py
│   └── pipeline.py
│
├── config/
│
├── data/
│   ├── input/
│   └── output/
│       └── jobs/
│
├── scripts/
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_cli.py
│   ├── test_ingestion.py
│   ├── test_pipeline.py
│   ├── test_privacy.py
│   └── test_validation.py
│
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md
# 41. Testing

V0.3 adds API-level testing in addition to the existing unit and pipeline tests.

The test suite covers:

Health endpoint
Readiness endpoint
Invalid generation parameters
Successful generation
Quality-gated regeneration
Maximum regeneration attempts
Job status
Attempt persistence
Artifact access
Existing pipeline functionality
Dataset ingestion
Privacy behavior
Validation behavior
CLI behavior

Run the complete suite:

pytest -q

Current V0.3 validation:

15 passed

The test suite completes successfully.

# 42. Compilation Check

Python compilation can be checked using:

python -m compileall app

The V0.3 application compiles successfully across its application modules.

# 43. Running the Application

Activate the virtual environment:

source .venv/bin/activate

Start the FastAPI application:

uvicorn app.api.main:app --reload

The application is then available through:

http://localhost:8000
# 44. API Documentation

FastAPI provides interactive API documentation.

Swagger UI:

http://localhost:8000/docs

ReDoc:

http://localhost:8000/redoc

These interfaces can be used to inspect and manually test the V0.3 API.

# 45. Docker

The project includes a Dockerfile for containerized execution.

Build the image:

docker build -t synthetic-data-platform .

Run the container:

docker run -p 8000:8000 synthetic-data-platform

The application can then be accessed through:

http://localhost:8000
# 46. CLI

The existing CLI remains available for direct pipeline execution.

Example:

python -m app.cli \
    --input data/input/sample.csv \
    --rows 100 \
    --epochs 300

The CLI reports generation and evaluation information directly to the terminal.

# 47. Logging

The application uses a centralized logging implementation.

Important pipeline events are logged, including:

Dataset loaded
Identifiers detected
CTGAN training started
Generation attempt started
Evaluation completed
Quality gate result
Regeneration
Job completion
Job failure

This provides operational visibility without relying on scattered debugging statements.

# 48. V0.2 → V0.3 Evolution

V0.2 established the core synthetic-data generation pipeline.

V0.2

Input
 ↓
Profiling
 ↓
Privacy
 ↓
Metadata
 ↓
CTGAN
 ↓
Synthetic Data
 ↓
Evaluation
 ↓
Output

V0.3 adds an application orchestration layer.

V0.3

API Request
 ↓
Job
 ↓
Attempt
 ↓
Generation
 ↓
Evaluation
 ↓
Quality Gate
 ↓
 ┌───────────────┐
 │               │
PASS           FAIL
 │               │
 ↓               ↓
Select        Regenerate
Attempt           │
 │                ↓
 │             Attempt N
 │                │
 └────────────────┘
          ↓
     Persist Job
          ↓
      Artifacts

This is the primary architectural transition in V0.3.

# 49. Why Attempts Are First-Class Objects

A failed generation should not disappear.

For example:

Attempt 1
Trust = 0.6717
Status = quality_failed

is valuable information.

It allows the platform to answer:

How many attempts were required?
Which attempt passed?
What was the trust score of each attempt?
Why did an attempt fail?
Which artifacts belong to which attempt?
Did regeneration actually improve quality?

This is why V0.3 models attempts separately from jobs.

# 50. Why Artifacts Are Attempt-Specific

Without attempt-specific artifact directories:

job/
    synthetic_data.csv

a regenerated dataset could overwrite the previous attempt.

V0.3 instead uses:

job/
    attempt_1/
        synthetic_data.csv
        evaluation_report.json

    attempt_2/
        synthetic_data.csv
        evaluation_report.json

This preserves the execution history.

# 51. Why SQLite Was Introduced

V0.2 primarily operated as a pipeline.

V0.3 introduces persistent jobs.

A persistent job model requires storage for:

job state
attempt state
timestamps
quality results
errors
artifact references

SQLite provides a lightweight persistent store without introducing an external database dependency at this stage.

The architecture can later evolve toward a production database without changing the conceptual job model.

# 52. V0.3 Engineering Principles

V0.3 follows several architectural principles.

Separation of concerns

API, services, pipeline, evaluation, jobs, and storage are separated.

Persistence

Operational job state is persisted.

Observability

Attempts and quality results remain inspectable.

Controlled regeneration

Regeneration is policy-driven rather than unlimited.

Artifact isolation

Each attempt receives its own artifact location.

Configuration-driven quality

Quality requirements are represented as policy rather than hard-coded application behavior.

Backward compatibility

The V0.2 generation pipeline remains the foundation.

# 53. Known Limitations

V0.3 is an important architectural milestone, but it is not yet a complete production deployment platform.

Current limitations include:

Job execution currently uses the application process/background-task mechanism.
SQLite is suitable for the current stage but is not the final distributed production datastore.
Artifact storage is filesystem-based.
There is no distributed worker queue yet.
There is no authentication/authorization layer yet.
There is no object-storage backend yet.
There is no multi-user tenancy model yet.
There is no production-grade orchestration system yet.
Quality evaluation can be computationally expensive for larger datasets.
SDV currently emits warnings regarding future metadata API changes.

These limitations are intentional boundaries for the V0.3 architecture.

# 54. Future Architecture Direction

The V0.3 architecture establishes the foundation for future versions.

A future production architecture can evolve toward:

                    API Gateway
                         |
                         v
                  Job Management API
                         |
                         v
                  Message / Job Queue
                         |
            +------------+------------+
            |                         |
            v                         v
      Generation Workers        Evaluation Workers
            |                         |
            +------------+------------+
                         |
                         v
                  Quality Gate
                         |
                +--------+--------+
                |                 |
              PASS              FAIL
                |                 |
                v                 v
          Attempt Select      Regeneration
                |                 |
                +--------+--------+
                         |
                         v
                 Persistent Store
                         |
              +----------+----------+
              |                     |
              v                     v
          PostgreSQL           Object Storage

Potential future technologies include:

PostgreSQL
Redis
Distributed worker queues
Object storage
Kubernetes
Authentication and authorization
Multi-tenant job management
Metrics and observability
Production monitoring
Horizontal worker scaling

These are future architectural directions and are not part of the current V0.3 implementation.

# 55. Release Evidence

V0.3 is considered complete when the following are verified:

✓ Job creation works
✓ Job persistence works
✓ Attempt persistence works
✓ Quality evaluation works
✓ Quality gate works
✓ Regeneration works
✓ Maximum attempt limit works
✓ Selected attempt is exposed
✓ Attempt history is exposed
✓ Artifacts are persisted
✓ Artifacts are downloadable
✓ API endpoints work
✓ Existing pipeline tests pass
✓ API tests pass
✓ Python compilation succeeds
✓ Docker configuration exists

Current automated test result:

15 passed
# 56. Version History
V0.1

Initial synthetic-data generation foundation.

Focused on:

Basic data ingestion
Synthetic-data generation
Initial validation
CLI-based execution
V0.2

Core synthetic-data pipeline release.

Focused on:

Dataset ingestion
Profiling
Identifier detection
Privacy-aware processing
Metadata detection
CTGAN generation
Synthetic-data output
Evaluation
Validation
Logging
CLI
Docker foundation
Configuration
Documentation
V0.3.0

Job orchestration and quality pipeline release.

Focused on:

FastAPI application
Job management
Persistent job storage
Generation attempts
Attempt history
Quality policy
Quality gate
Trust scoring
Statistical fidelity
Confidence evaluation
Automatic regeneration
Maximum regeneration limits
Attempt selection
Artifact storage
Artifact download API
API integration tests
Service layer architecture
# 57. Release Philosophy

The platform is being developed incrementally.

Each version should introduce a meaningful architectural capability rather than simply adding features.

V0.1
Foundation
   ↓
V0.2
Reliable Synthetic Data Pipeline
   ↓
V0.3
Job Orchestration + Quality Gate
   ↓
V0.4
Production-oriented execution architecture
   ↓
Future
Scalable Synthetic Data Platform

The goal is to evolve from a local synthetic-data pipeline into a reliable, observable, policy-driven synthetic-data platform.

# 58. Current Release
Version: V0.3.0

Primary capability:
Job Orchestration + Quality-Gated Synthetic Data Generation

Generation:
CTGAN / SDV

API:
FastAPI

Persistence:
SQLite

Artifacts:
Filesystem

Testing:
pytest

Containerization:
Docker

Quality policy:
Regeneration enabled

Default trust threshold:
0.70

Maximum attempts:
3
# 59. Final Architecture Summary

V0.3 transforms the project from:

"Run a synthetic-data pipeline."

into:

"Create a generation job,
execute controlled generation attempts,
evaluate every result,
apply a quality policy,
regenerate when necessary,
select the appropriate attempt,
persist the complete execution history,
and expose the resulting artifacts through an API."

That transition represents the core architectural milestone of V0.3.

End of V0.3 Documentation

V0.3 establishes the job-oriented foundation required for the platform's next stage of development.

The next versions can build on this foundation rather than redesigning the core generation pipeline.
