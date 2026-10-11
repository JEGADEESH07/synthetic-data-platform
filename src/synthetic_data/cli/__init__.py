"""Command-line interface for the Synthetic Data Platform."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from synthetic_data.config import load_config
from synthetic_data.errors import SyntheticDataPlatformError
from synthetic_data.logging_config import configure_logging
from synthetic_data.persistence import persist_artifacts
from synthetic_data.pipeline import run_pipeline
from synthetic_data.privacy import evaluate_privacy
from synthetic_data.validation import validate_schema


app = typer.Typer(
    name="sdp",
    help="Synthetic Data Engineering & Privacy Platform",
)

console = Console()


@app.command()
def generate(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to the source CSV dataset.",
    ),
    rows: int | None = typer.Option(
        None,
        "--rows",
        "-r",
        help="Number of synthetic rows to generate.",
    ),
    config_file: Path = typer.Option(
        Path("config/default.yaml"),
        "--config",
        "-c",
        help="Path to the YAML configuration file.",
    ),
):
    """Generate synthetic data from a CSV dataset."""

    try:
        configure_logging()

        config = load_config(config_file)

        result = run_pipeline(
            file_path=input_file,
            row_count=rows,
            config=config,
        )

        schema_result = validate_schema(
            source_dataframe=result.source_dataframe,
            synthetic_dataframe=result.synthetic_dataframe,
        )

        privacy_report = evaluate_privacy(
            source_dataframe=result.source_dataframe,
            synthetic_dataframe=result.synthetic_dataframe,
            detection=result.detection,
        )

        artifacts = persist_artifacts(
            synthetic_dataframe=result.synthetic_dataframe,
            schema_result=schema_result,
            privacy_report=privacy_report,
            output_root=config.output.directory,
        )

    except SyntheticDataPlatformError as exc:
        console.print(
            f"[bold red]Generation failed:[/bold red] {exc}"
        )
        raise typer.Exit(code=1) from exc

    except Exception as exc:
        console.print(
            "[bold red]Unexpected error:[/bold red] "
            f"{type(exc).__name__}: {exc}"
        )
        raise typer.Exit(code=1) from exc

    console.print()
    console.print(
        "[bold green]Synthetic data generation completed.[/bold green]"
    )
    console.print()

    table = Table(title="Generation Summary")

    table.add_column("Property")
    table.add_column("Value")

    table.add_row(
        "Source rows",
        str(len(result.source_dataframe)),
    )

    table.add_row(
        "Synthetic rows",
        str(len(result.synthetic_dataframe)),
    )

    table.add_row(
        "Columns",
        str(len(result.synthetic_dataframe.columns)),
    )

    table.add_row(
        "Schema",
        "PASS" if schema_result.valid else "FAIL",
    )

    table.add_row(
        "Privacy",
        privacy_report.status,
    )

    table.add_row(
        "Job ID",
        artifacts.job_id,
    )

    console.print(table)
    console.print()

    console.print(
        f"[bold]Synthetic CSV:[/bold] "
        f"{artifacts.synthetic_data_path}"
    )

    console.print(
        f"[bold]Report:[/bold] "
        f"{artifacts.report_path}"
    )


@app.command()
def version():
    """Show the platform version."""

    from synthetic_data import __version__

    console.print(
        f"Synthetic Data Engineering & Privacy Platform v{__version__}"
    )


if __name__ == "__main__":
    app()