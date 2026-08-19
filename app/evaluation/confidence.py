from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationConfidence:
    """
    Describes how much evidence supports an evaluation.
    """

    sample_size_score: float
    feature_coverage_score: float
    metric_coverage_score: float
    confidence_score: float
    level: str

    def to_dict(self) -> dict:
        """
        Convert confidence information to a dictionary.
        """

        return {
            "sample_size_score": self.sample_size_score,
            "feature_coverage_score": (
                self.feature_coverage_score
            ),
            "metric_coverage_score": (
                self.metric_coverage_score
            ),
            "confidence_score": self.confidence_score,
            "level": self.level,
        }

def calculate_evaluation_confidence(
    real_rows: int,
    synthetic_rows: int,
    evaluated_columns: int,
    total_evaluable_columns: int,
    available_metrics: int,
    applicable_metrics: int,
) -> EvaluationConfidence:
    """
    Calculate confidence in the evaluation evidence.
    """

    if real_rows <= 0:
        raise ValueError(
            "real_rows must be greater than zero."
        )

    if synthetic_rows <= 0:
        raise ValueError(
            "synthetic_rows must be greater than zero."
        )

    if total_evaluable_columns <= 0:
        raise ValueError(
            "total_evaluable_columns must be greater than zero."
        )

    # --------------------------------------------------
    # SAMPLE SIZE
    # --------------------------------------------------

    sample_size_score = min(
        1.0,
        synthetic_rows / 1000.0,
    )

    # --------------------------------------------------
    # FEATURE COVERAGE
    # --------------------------------------------------

    feature_coverage_score = (
        evaluated_columns
        / total_evaluable_columns
    )

    feature_coverage_score = max(
        0.0,
        min(1.0, feature_coverage_score),
    )

    # --------------------------------------------------
    # METRIC COVERAGE
    # --------------------------------------------------

    if applicable_metrics <= 0:
        metric_coverage_score = 0.0

    else:
        metric_coverage_score = (
            available_metrics
            / applicable_metrics
        )

        metric_coverage_score = max(
            0.0,
            min(1.0, metric_coverage_score),
        )

    # --------------------------------------------------
    # OVERALL CONFIDENCE
    # --------------------------------------------------

    confidence_score = (
        0.40 * sample_size_score
        + 0.30 * feature_coverage_score
        + 0.30 * metric_coverage_score
    )

    confidence_score = max(
        0.0,
        min(1.0, confidence_score),
    )

    if confidence_score >= 0.80:
        level = "high"

    elif confidence_score >= 0.60:
        level = "medium"

    else:
        level = "low"

    return EvaluationConfidence(
        sample_size_score=float(
            sample_size_score
        ),
        feature_coverage_score=float(
            feature_coverage_score
        ),
        metric_coverage_score=float(
            metric_coverage_score
        ),
        confidence_score=float(
            confidence_score
        ),
        level=level,
    )