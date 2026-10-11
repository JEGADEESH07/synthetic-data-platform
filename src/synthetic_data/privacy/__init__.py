"""Privacy evaluation package."""

from synthetic_data.privacy.evaluator import (
    DuplicatePrivacyResult,
    IdentifierPrivacyResult,
    PrivacyEvaluationError,
    PrivacyReport,
    evaluate_privacy,
)

__all__ = [
    "DuplicatePrivacyResult",
    "IdentifierPrivacyResult",
    "PrivacyEvaluationError",
    "PrivacyReport",
    "evaluate_privacy",
]