
from synthetic_data.audit.versions import (
    ENGINE_NAME,
    ENGINE_VERSION,
    capture_engine_version,
)


def test_capture_engine_version_includes_platform_and_engine():
    versions = capture_engine_version()

    assert versions["platform_version"]
    assert versions["engine_name"] == ENGINE_NAME
    assert versions["engine_version"] == ENGINE_VERSION


def test_engine_version_identifies_frozen_v02_baseline():
    versions = capture_engine_version()

    assert versions["engine_version"] == "0.2.0"
    assert "V0.2" in versions["engine_name"]


def test_capture_engine_version_returns_string_values():
    versions = capture_engine_version()

    assert all(
        isinstance(value, str)
        for value in versions.values()
    )


def test_platform_version_fallback(monkeypatch):
    import synthetic_data.audit.versions as versions_module

    def missing_package(package_name):
        raise versions_module.PackageNotFoundError(package_name)

    monkeypatch.setattr(
        versions_module,
        "version",
        missing_package,
    )

    result = versions_module.capture_engine_version()

    assert result["platform_version"] == "unknown"
    assert result["engine_version"] == "0.2.0"
