from app.pipeline import run_pipeline


class SyntheticDataService:
    """
    Application-level service for synthetic data generation.
    """

    def generate(
        self,
        input_path: str,
        output_rows: int,
        epochs: int,
        output_data_path: str | None = None,
        output_report_path: str | None = None,
    ) -> dict:
        """
        Generate synthetic data using the existing V0.2 pipeline.
        """

        return run_pipeline(
            input_path=input_path,
            output_rows=output_rows,
            epochs=epochs,
            output_data_path=output_data_path,
            output_report_path=output_report_path,
        )