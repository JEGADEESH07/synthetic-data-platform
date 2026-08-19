import pandas as pd

from app.evaluation.statistical_fidelity import (
    StatisticalFidelityEngine,
)
from app.validation.schema_validator import (
    validate_schema,
)
from app.evaluation.trust import (
    calculate_trust_score,
)
from app.validation.schema_validator import (
    validate_schema,
)
from app.evaluation.quality_gate import (
    evaluate_quality_gate,
)
from app.config.settings import (
    DEFAULT_QUALITY_POLICY,
)
from app.evaluation.confidence import (
    calculate_evaluation_confidence,
)

from app.validation.privacy_validator import (
    evaluate_privacy,
)

from app.validation.privacy_validator import (
    evaluate_privacy,
)

from app.evaluation.models import (
    EvaluationResult,
)


class EvaluationEngine:
    """
    Orchestrates all synthetic-data evaluations.
    """

    def __init__(self) -> None:
        self.statistical_fidelity = (
            StatisticalFidelityEngine()
        )

    def evaluate(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        identifier_columns: list[str] | None = None,
    ) -> EvaluationResult:
        """
        Run schema, statistical, and privacy evaluation.
        """

        if identifier_columns is None:
            identifier_columns = []

        schema_report = validate_schema(
            real_data,
            synthetic_data,
        )

        statistical_report = (
            self.statistical_fidelity.evaluate(
                real_data=real_data,
                synthetic_data=synthetic_data,
                identifier_columns=identifier_columns,
            )
        )

        privacy_report = evaluate_privacy(
            real_data,
            synthetic_data,
            identifier_columns,
        )

        evaluated_columns = [
            column
            for column in real_data.columns
            if column not in identifier_columns
            and column in synthetic_data.columns
        ]

        applicable_metrics = 0
        available_metrics = 0

        if statistical_report.get(
            "numerical_score"
        ) is not None:
            applicable_metrics += 1
            available_metrics += 1

        if statistical_report.get(
            "categorical_score"
        ) is not None:
            applicable_metrics += 1
            available_metrics += 1

        if statistical_report.get(
            "correlation_score"
        ) is not None:
            applicable_metrics += 1
            available_metrics += 1

        if statistical_report.get(
            "missingness_score"
        ) is not None:
            applicable_metrics += 1
            available_metrics += 1

        confidence = calculate_evaluation_confidence(
            real_rows=len(real_data),
            synthetic_rows=len(synthetic_data),
            evaluated_columns=len(
                evaluated_columns
            ),
            total_evaluable_columns=len(
                evaluated_columns
            ),
            available_metrics=available_metrics,
            applicable_metrics=applicable_metrics,
        )

        trust = calculate_trust_score(
            fidelity_score=statistical_report[
                "overall_score"
            ],
            confidence_score=confidence.confidence_score,
        )
        quality_gate = evaluate_quality_gate(
            trust_score=trust.trust_score,
            schema_valid=(
                schema_report["valid"]
            ),
            privacy_safe=(
                privacy_report["safe"]
            ),
            policy=DEFAULT_QUALITY_POLICY,
        )
        return EvaluationResult(
            schema=schema_report,
            statistical_quality=statistical_report,
            privacy=privacy_report,
            confidence=confidence.to_dict(),
            trust=trust.to_dict(),
            quality_gate=quality_gate.to_dict(),
        )