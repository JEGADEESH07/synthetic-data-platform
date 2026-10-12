"""Tests for the command-line interface."""

from typer.testing import CliRunner

from synthetic_data.cli import app


runner = CliRunner()


def test_generate_command(tmp_path):
    input_file = tmp_path / "input.csv"

    input_file.write_text(
        """Customer_ID,Customer_Name,Phone_Number,Email,Age,City,Amount
C001,Alice,9000000001,alice@example.com,25,Chennai,1000
C002,Bob,9000000002,bob@example.com,30,Madurai,2000
C003,Charlie,9000000003,charlie@example.com,35,Chennai,3000
C004,David,9000000004,david@example.com,40,Coimbatore,4000
C005,Eve,9000000005,eve@example.com,45,Madurai,5000
""",
        encoding="utf-8",
    )

    config_file = tmp_path / "config.yaml"
    output_dir = tmp_path / "output"

    config_file.write_text(
        f"""
generation:
  default_row_count: 10
  ctgan_epochs: 1

output:
  directory: {output_dir.as_posix()}

quality:
  minimum_score: 0.80

privacy:
  fail_on_exact_match: true

input:
  allowed_root: {tmp_path.as_posix()}
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "generate",
            str(input_file),
            "--config",
            str(config_file),
        ],
    )

    assert result.exit_code == 0, (
    f"CLI failed with exit code {result.exit_code}\n"
    f"CLI output:\n{result.stdout}\n"
    f"CLI exception: {result.exception!r}"
)
    assert "Synthetic data generation completed." in result.stdout
    assert "Privacy" in result.stdout
    assert output_dir.exists()
    assert len(list(output_dir.iterdir())) == 1


def test_generate_command_with_rows_override(tmp_path):
    input_file = tmp_path / "input.csv"

    input_file.write_text(
        """Customer_ID,Age,City,Amount
C001,25,Chennai,1000
C002,30,Madurai,2000
C003,35,Chennai,3000
C004,40,Coimbatore,4000
C005,45,Madurai,5000
""",
        encoding="utf-8",
    )

    config_file = tmp_path / "config.yaml"
    output_dir = tmp_path / "output"

    config_file.write_text(
        f"""
generation:
  default_row_count: 10
  ctgan_epochs: 1

output:
  directory: {output_dir.as_posix()}

quality:
  minimum_score: 0.80

privacy:
  fail_on_exact_match: true

input:
  allowed_root: {tmp_path.as_posix()}
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "generate",
            str(input_file),
            "--rows",
            "7",
            "--config",
            str(config_file),
        ],
    )

    assert result.exit_code == 0
    assert "Synthetic rows" in result.stdout