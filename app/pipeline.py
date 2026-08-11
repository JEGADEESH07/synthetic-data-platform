from app.config.settings import (
    DEFAULT_CONFIG,
    validate_generation_parameters,
)

from app.ingestion.loader import load_dataset

from app.profiling.profiler import profile_dataset
from app.profiling.metadata import detect_metadata

from app.privacy.identifier_detector import (
    detect_identifiers,
)
from app.privacy.data_protector import (
    separate_identifiers,
)
from app.privacy.identifier_generator import (
    generate_identifier_values,
)

from app.generation.ctgan_generator import (
    train_ctgan,
    generate_synthetic_data,
)

from app.validation.schema_validator import (
    validate_schema,
)
from app.validation.statistical_validator import (
    evaluate_statistical_quality,
)
from app.validation.privacy_validator import (
    evaluate_privacy,
)

from app.output.writer import (
    save_synthetic_data,
    save_evaluation_report,
)

from app.logging.logger import get_logger

logger = get_logger("pipeline")

def run_pipeline(
    input_path: str,
    output_rows: int = DEFAULT_CONFIG.default_output_rows,
    epochs: int = DEFAULT_CONFIG.default_epochs,
    output_data_path: str | None = (
        DEFAULT_CONFIG.default_output_data_path
    ),
    output_report_path: str | None = (
        DEFAULT_CONFIG.default_output_report_path
    ),
) -> dict:
    """
    Run the complete V0.2 synthetic-data pipeline.
    """

    # --------------------------------------------------
    # 1. VALIDATE PARAMETERS
    # --------------------------------------------------

    validate_generation_parameters(
        output_rows=output_rows,
        epochs=epochs,
    )

    # --------------------------------------------------
    # 2. INGESTION
    # --------------------------------------------------

    df_real = load_dataset(input_path)
    logger.info(
        "Dataset loaded: %s | rows=%d | columns=%d",
        input_path,
        len(df_real),
        len(df_real.columns),
    )
    # --------------------------------------------------
    # 3. PROFILING
    # --------------------------------------------------

    profile = profile_dataset(df_real)

    # --------------------------------------------------
    # 4. IDENTIFIER DETECTION
    # --------------------------------------------------

    identifier_columns = detect_identifiers(
        df_real
    )
    logger.info(
    "Identifiers detected: %s",
    identifier_columns,
    )

    # --------------------------------------------------
    # 5. IDENTIFIER SEPARATION
    # --------------------------------------------------

    training_data, identifier_data = separate_identifiers(
        df_real,
        identifier_columns,
    )

    # --------------------------------------------------
    # 6. METADATA
    # --------------------------------------------------

    metadata = detect_metadata(
        training_data
    )

    # --------------------------------------------------
    # 7. CTGAN TRAINING
    # --------------------------------------------------
    logger.info(
        "Starting CTGAN training | rows=%d | epochs=%d",
        len(training_data),
        epochs,
    )
    synthesizer = train_ctgan(
        training_data,
        metadata,
        epochs=epochs,
    )

    # --------------------------------------------------
    # 8. SYNTHETIC GENERATION
    # --------------------------------------------------

    synthetic_data = generate_synthetic_data(
        synthesizer,
        output_rows,
    )
    logger.info(
    "Synthetic generation completed | rows=%d",
    len(synthetic_data),
    )

    # --------------------------------------------------
    # 9. FRESH IDENTIFIERS
    # --------------------------------------------------

    forbidden_values = {
        column: set(
            identifier_data[column]
            .dropna()
            .astype(str)
        )
        for column in identifier_columns
    }

    final_data = generate_identifier_values(
        synthetic_data,
        identifier_columns,
        forbidden_values=forbidden_values,
    )

    # --------------------------------------------------
    # 10. COLUMN ORDER
    # --------------------------------------------------

    final_data = final_data[
        df_real.columns
    ]

    # --------------------------------------------------
    # 11. SCHEMA VALIDATION
    # --------------------------------------------------

    schema_report = validate_schema(
        df_real,
        final_data,
    )
    logger.info(
    "Schema validation completed | valid=%s",
    schema_report["valid"],
    )

    # --------------------------------------------------
    # 12. STATISTICAL QUALITY
    # --------------------------------------------------

    quality_report = evaluate_statistical_quality(
        df_real,
        final_data,
        identifier_columns,
    )

    # --------------------------------------------------
    # 13. PRIVACY
    # --------------------------------------------------

    privacy_report = evaluate_privacy(
        df_real,
        final_data,
        identifier_columns,
    )
    logger.info(
    "Privacy evaluation completed | safe=%s",
    privacy_report["safe"],
    )

    # --------------------------------------------------
    # 14. EVALUATION
    # --------------------------------------------------

    evaluation = {
        "schema": schema_report,
        "statistical_quality": quality_report,
        "privacy": privacy_report,
    }

    # --------------------------------------------------
    # 15. OUTPUT
    # --------------------------------------------------

    saved_files = {}

    if output_data_path is not None:
        saved_files["synthetic_data"] = (
            save_synthetic_data(
                final_data,
                output_data_path,
            )
        )

    if output_report_path is not None:
        saved_files["evaluation_report"] = (
            save_evaluation_report(
                evaluation,
                output_report_path,
            )
        )

    logger.info(
        "Pipeline completed successfully | saved_files=%s",
        saved_files,
    )
    # --------------------------------------------------
    # 16. RETURN
    # --------------------------------------------------

    return {
        "profile": profile,
        "identifier_columns": identifier_columns,
        "metadata": metadata.to_dict(),
        "synthetic_data": final_data,
        "evaluation": evaluation,
        "saved_files": saved_files,
    }