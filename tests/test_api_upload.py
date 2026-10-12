from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from synthetic_data.api import app as app_module


def test_upload_creates_queued_job():
    client = TestClient(app_module.app)

    csv_content = (
        "employee_id,name,department\n"
        "1,Alice,Engineering\n"
        "2,Bob,Finance\n"
    )

    response = client.post(
        "/api/v1/jobs/upload",
        files={
            "file": (
                "customer_data.csv",
                BytesIO(csv_content.encode("utf-8")),
                "text/csv",
            )
        },
        data={
            "row_count": "10",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert "job_id" in body
    assert body["status"] == "CREATED"

    job_id = body["job_id"]

    job = app_module.job_service.get_job(job_id)

    assert job is not None
    assert job.job_id == job_id
    assert job.row_count == 10

    input_path = Path(job.input_file)

    assert input_path.exists()
    assert input_path.is_file()
    assert input_path.suffix == ".csv"

    assert input_path.parent.name == "uploads"

    assert input_path.name != "customer_data.csv"

    assert input_path.name.endswith(".csv")