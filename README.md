# Synthetic Data Platform

A privacy-aware synthetic data generation platform that transforms structured datasets into synthetic datasets while preserving statistical characteristics and protecting sensitive identifiers.

## Version

**V0.2.0 — Release Candidate**

V0.2 delivers the first complete end-to-end version of the Synthetic Data Platform, including dataset ingestion, profiling, privacy protection, synthetic data generation, validation, CLI execution, automated testing, logging, and Dockerized execution.

---

# 1. Overview

The Synthetic Data Platform accepts structured datasets such as CSV and Excel files and generates statistically representative synthetic data.

The platform is designed around three primary goals:

1. **Data usability** — preserve important statistical characteristics of the source dataset.
2. **Privacy protection** — prevent direct reuse of sensitive identifiers.
3. **Operational reliability** — provide validation, testing, logging, and containerized execution.

The V0.2 pipeline is designed as a batch/CLI application.

---

# 2. V0.2 Capabilities

V0.2 provides the following capabilities:

- CSV dataset ingestion
- XLS/XLSX dataset ingestion
- Dataset profiling
- Identifier detection
- Identifier separation
- Privacy-aware training data preparation
- SDV metadata generation
- CTGAN-based synthetic data generation
- Fresh synthetic identifier generation
- Schema validation
- Statistical quality evaluation
- Identifier leakage evaluation
- Exact-row leakage evaluation
- CSV output persistence
- JSON evaluation reports
- Configurable generation parameters
- Command-line interface
- Structured logging
- Automated tests
- Realistic development datasets
- Dockerized execution
- CPU-only container execution

---

# 3. Architecture

The V0.2 architecture is modular.

```text
                    Input Dataset
                         |
                         v
                +------------------+
                |    Ingestion     |
                +------------------+
                         |
                         v
                +------------------+
                |    Profiling     |
                +------------------+
                         |
                         v
                +---------------------------+
                | Identifier Detection      |
                | & Privacy Separation      |
                +---------------------------+
                         |
                         v
                +------------------+
                |     Metadata    |
                +------------------+
                         |
                         v
                +------------------+
                | CTGAN Training   |
                +------------------+
                         |
                         v
                +---------------------------+
                | Synthetic Data Generation|
                +---------------------------+
                         |
                         v
                +---------------------------+
                | Fresh Identifier          |
                | Generation                 |
                +---------------------------+
                         |
                         v
                +---------------------------+
                | Validation                |
                | - Schema                  |
                | - Statistical Quality     |
                | - Privacy                 |
                +---------------------------+
                         |
                         v
                +---------------------------+
                | CSV + JSON Output         |
                +---------------------------+

4. Project Structure

synthetic-data-platform/
│
├── app/
│   ├── ingestion/
│   │   └── loader.py
│   │
│   ├── profiling/
│   │   ├── profiler.py
│   │   └── metadata.py
│   │
│   ├── privacy/
│   │   ├── identifier_detector.py
│   │   ├── data_protector.py
│   │   └── identifier_generator.py
│   │
│   ├── generation/
│   │   └── ctgan_generator.py
│   │
│   ├── validation/
│   │   ├── schema_validator.py
│   │   ├── statistical_validator.py
│   │   └── privacy_validator.py
│   │
│   ├── config/
│   │   └── settings.py
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
│
├── scripts/
│
├── tests/
│   ├── test_cli.py
│   ├── test_ingestion.py
│   ├── test_pipeline.py
│   ├── test_privacy.py
│   └── test_validation.py
│
├── .dockerignore
├── Dockerfile
├── requirements.txt
└── README.md

5. Supported Input Formats

The ingestion layer supports:

.csv
.xlsx
.xls

Example input:

data/input/dev_dataset.csv

The loader validates:

File existence
File extension
File readability
Empty datasets
Invalid input paths
6. Dataset Profiling

Before synthetic generation, the platform profiles the input dataset.

The profiler collects information such as:

Row count
Column count
Data type
Missing values
Unique values

Example:

row_count
column_count
columns
    dtype
    missing_count
    unique_count

This information is used to understand the structure of the source dataset before generation.

7. Privacy Protection

Potential identifiers are detected before model training.

For example:

Customer_ID
Customer_Name

can be identified as sensitive identifier columns.

These columns are separated from the training dataset.

The model therefore learns from the non-identifier attributes such as:

Age
City
Transaction_Amount

After generation, fresh identifier values are created.

Example:

SYN100000
SYN100001
SYN100002

Synthetic names are also generated rather than copying the original customer names.

The identifier generator additionally supports forbidden-value protection to prevent generated identifiers from colliding with known original identifier values.

8. Synthetic Data Generation

V0.2 uses SDV's CTGAN-based synthetic data generation workflow.

The generation process is:

Training Dataset
       |
       v
Metadata
       |
       v
CTGAN
       |
       v
Synthetic Records
       |
       v
Fresh Identifiers

The number of generated rows and CTGAN training epochs are configurable through the CLI.

9. Metadata

The platform automatically derives metadata from the protected training dataset.

For example:

Age
    sdtype: numerical

City
    sdtype: categorical

Transaction_Amount
    sdtype: numerical

Identifier columns are excluded from the synthetic model training dataset.

10. Validation

V0.2 validates the generated dataset in three major areas.

10.1 Schema Validation

Schema validation checks:

Column count
Column names
Column order
Missing columns
Unexpected columns

Example result:

Schema valid:
True
10.2 Statistical Quality Evaluation

Numerical columns are evaluated using:

Mean
Standard deviation
Minimum
Maximum
Mean similarity

Categorical columns are evaluated using:

Value distributions
Distribution similarity

These metrics provide an indication of how closely the synthetic dataset represents the statistical characteristics of the source dataset.

10.3 Privacy Evaluation

Privacy evaluation checks:

Identifier leakage

Checks whether original identifier values appear in the generated dataset.

Exact row leakage

Checks whether complete original rows are reproduced in the synthetic dataset.

The final pipeline reports:

Privacy safe:
True

when the configured privacy checks pass.

11. Command-Line Interface

V0.2 provides a CLI for synthetic data generation.

Basic usage
python -m app.cli generate \
    --input data/input/dev_dataset.csv \
    --rows 1000 \
    --epochs 20
Parameters
Parameter	Required	Default	Description
--input	Yes	—	Input CSV/XLS/XLSX dataset
--rows	Yes	—	Number of synthetic rows
--epochs	No	300	CTGAN training epochs
--output	No	data/output/synthetic_data.csv	Synthetic dataset output
--report	No	data/output/evaluation_report.json	Evaluation report output
Custom output paths
python -m app.cli generate \
    --input data/input/dev_dataset.csv \
    --rows 1000 \
    --epochs 20 \
    --output data/output/v02_synthetic.csv \
    --report data/output/v02_evaluation.json
12. Running Locally
12.1 Create virtual environment
python -m venv .venv
12.2 Activate environment

Linux/macOS:

source .venv/bin/activate

Windows:

.venv\Scripts\activate
12.3 Install dependencies
pip install -r requirements.txt
12.4 Run the application
python -m app.cli generate \
    --input data/input/dev_dataset.csv \
    --rows 1000 \
    --epochs 20
13. Testing

V0.2 includes an automated test suite.

Run:

pytest -v

The V0.2 test suite contains seven tests covering:

CLI
Dataset ingestion
Pipeline execution
Identifier detection
Identifier separation
Schema validation

The complete test suite has been verified successfully inside Docker:

7 passed
14. Logging

The pipeline provides structured application logging.

Example:

INFO | pipeline | Dataset loaded
INFO | pipeline | Identifiers detected
INFO | pipeline | Starting CTGAN training
INFO | pipeline | Synthetic generation completed
INFO | pipeline | Schema validation completed
INFO | pipeline | Privacy evaluation completed
INFO | pipeline | Pipeline completed successfully

Logging provides visibility into the major stages of the pipeline without requiring manual debugging.

15. Error Handling

The ingestion and pipeline layers include validation for common invalid conditions.

Examples include:

Missing dataset
Unsupported file extension
Empty dataset
Invalid dataset path
Dataset loading failure
Invalid generation parameters

Example:

ValueError:
Unsupported file type: .txt

The application intentionally fails with explicit errors rather than silently continuing with invalid input.

16. Docker

V0.2 is containerized using Docker.

Build the image
docker build -t synthetic-data-platform:v0.2 .
Run synthetic generation
docker run --rm \
    -v "$(pwd)/data/input:/app/data/input" \
    -v "$(pwd)/data/output:/app/data/output" \
    synthetic-data-platform:v0.2 \
    generate \
    --input data/input/dev_dataset.csv \
    --rows 1000 \
    --epochs 20

The host input and output directories are mounted into the container.

Therefore:

Host
data/input/
      |
      v
Container
/app/data/input/

Container
/app/data/output/
      |
      v
Host
data/output/
17. Dockerized Testing

The complete test suite can also be executed inside the Docker image.

docker run --rm \
    --entrypoint pytest \
    --volume "$(pwd)/data/input:/app/data/input" \
    synthetic-data-platform:v0.2 \
    -v

Expected result:

7 passed

This verifies that the application and its dependencies work inside the containerized runtime, independently of the local virtual environment.

18. Runtime Environment

V0.2 uses a CPU-only PyTorch environment.

The container runtime was verified with:

Torch: 2.13.0+cpu
CUDA: False
SDV: 1.38.0

The V0.2 Docker image therefore does not require a CUDA-enabled host.

19. Development Dataset

A realistic development dataset is provided at:

data/input/dev_dataset.csv

The final V0.2 integration test uses:

Input rows:        5000
Input columns:     5
Synthetic rows:    1000
CTGAN epochs:      20

The final local and Docker integration tests successfully produced:

Rows: 1000
Duplicate rows: 0
Schema valid: True
Privacy safe: True
20. Output

The pipeline generates two primary artifacts.

Synthetic dataset
data/output/v02_synthetic.csv
Evaluation report
data/output/v02_evaluation.json

The evaluation report contains:

schema
statistical_quality
privacy
21. Container Health Check Decision

V0.2 is intentionally designed as a batch/CLI application, rather than a continuously running API service.

The container lifecycle is:

docker run
    |
    v
CLI command
    |
    v
Dataset ingestion
    |
    v
Synthetic generation
    |
    v
Validation
    |
    v
Output persistence
    |
    v
Process exit

Because the application terminates after completing its batch workload, an HTTP-based container health endpoint is not currently required.

V0.2 container correctness is instead validated through:

Successful process execution
Exit status
Automated tests
Docker integration tests

This is an intentional architectural decision.

It is not a limitation caused by an inability to implement a health check.

When the platform evolves into a continuously running service, V0.3 will introduce a proper service health architecture with lightweight:

/health
/readiness

endpoints.

The container/orchestration health checks will then target those endpoints rather than repeatedly importing the complete ML stack.

22. Known Dependency Warnings

V0.2 currently uses SDV 1.38.0.

The SDV runtime may emit warnings related to:

SingleTableMetadata deprecation

and metadata persistence recommendations.

These warnings do not prevent successful synthetic data generation or validation in V0.2.

Future versions will revisit the SDV metadata implementation to maintain compatibility with newer SDV APIs.

23. V0.2 Definition of Done
Requirement	Status
Development environment	Complete
Modular application architecture	Complete
File ingestion	Complete
Dataset profiling	Complete
Identifier detection/protection	Complete
Metadata policy	Complete
Synthetic generation	Complete
Fresh identifier generation	Complete
End-to-end pipeline	Complete
Schema validation	Complete
Statistical quality evaluation	Complete
Privacy evaluation	Complete
Output persistence	Complete
Configuration	Complete
CLI	Complete
Automated tests	Complete
Realistic development datasets	Complete
Robust error handling	Complete
Logging	Complete
Dockerized application	Complete
Final V0.2 integration test	Complete
V0.2 release/tag	Pending
24. V0.2 Final Validation

The final V0.2 workflow has been validated in both local and Docker environments.

                 V0.2 FINAL VALIDATION

                    5000-row dataset
                           |
                           v
                    Identifier detection
                           |
                           v
                    Privacy separation
                           |
                           v
                      CTGAN training
                           |
                           v
                   1000 synthetic rows
                           |
             +-------------+-------------+
             |                           |
             v                           v
       Schema validation          Privacy evaluation
             |                           |
             +-------------+-------------+
                           |
                           v
                    Output persistence
                           |
                           v
                       SUCCESS

Final validation results:

Synthetic rows:       1000
Duplicate rows:       0
Schema valid:         True
Privacy safe:         True
Docker integration:   Passed
Automated tests:      7 passed
25. V0.3 Roadmap

The next major version will move the platform toward a continuously running service architecture.

Potential V0.3 capabilities include:

FastAPI service
REST API
Dataset upload endpoint
Synthetic generation endpoint
Health endpoint
Readiness endpoint
Job-based generation
Improved metadata management
Advanced privacy metrics
Authentication and authorization
Production observability
Deployment-oriented configuration
Service-level Docker health checks
26. Current Status

V0.2 Release Candidate

All functional and integration requirements have been completed.

The remaining release action is the creation of the Git v0.2.0 release/tag.


---

# Where each section goes

You asked **"where should I include it in README and so on?"**

Use this exact order:

```text
README.md
│
├── 1. Project title + one-line description
├── 2. Version
├── 3. Overview
├── 4. V0.2 Capabilities
├── 5. Architecture
├── 6. Project Structure
├── 7. Supported Input Formats
├── 8. Dataset Profiling
├── 9. Privacy Protection
├── 10. Synthetic Data Generation
├── 11. Metadata
├── 12. Validation
├── 13. CLI
├── 14. Running Locally
├── 15. Testing
├── 16. Logging
├── 17. Error Handling
├── 18. Docker
├── 19. Dockerized Testing
├── 20. Runtime Environment
├── 21. Development Dataset
├── 22. Output
├── 23. Container Health Check Decision
├── 24. Known Dependency Warnings
├── 25. V0.2 Definition of Done
├── 26. V0.2 Final Validation
├── 27. V0.3 Roadmap
└── 28. Current Status

This structure is deliberate:

Beginning → what the project is.
Middle → how it works and how to use it.
Operational sections → testing, Docker, logging, errors.
Architecture decisions → health-check decision and known warnings.
End → evidence that V0.2 is complete and what comes next.