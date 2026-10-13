
import json

from synthetic_data.audit.environment import capture_environment


def test_capture_environment_includes_runtime_information():
    environment = capture_environment()

    assert environment["python_version"]
    assert environment["python_implementation"]
    assert environment["platform_system"]
    assert environment["platform_release"]


def test_capture_environment_includes_tracked_packages():
    environment = capture_environment()

    packages = environment["packages"]

    assert "sdv" in packages
    assert "pandas" in packages
    assert "numpy" in packages
    assert "fastapi" in packages
    assert "pydantic" in packages

    assert all(
        version is None or isinstance(version, str)
        for version in packages.values()
    )


def test_environment_metadata_is_json_serializable():
    environment = capture_environment()

    serialized = json.dumps(environment)
    restored = json.loads(serialized)

    assert restored == environment


def test_environment_metadata_excludes_sensitive_fields():
    environment = capture_environment()

    forbidden_fields = {
        "hostname",
        "username",
        "password",
        "secret",
        "environment_variables",
        "input_file",
    }

    assert forbidden_fields.isdisjoint(environment)
