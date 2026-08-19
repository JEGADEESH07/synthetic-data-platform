from dataclasses import dataclass

from app.config.settings import QualityPolicy


@dataclass(frozen=True)
class QualityGateResult:
    """
    Result of applying quality requirements
    to an evaluated synthetic dataset.
    """

    passed: bool
    trust_score: float
    schema_valid: bool
    privacy_safe: bool
    reasons: list[str]

    def to_dict(self) -> dict:
        """
        Convert the quality-gate result to a dictionary.
        """

        return {
            "passed": self.passed,
            "trust_score": self.trust_score,
            "schema_valid": self.schema_valid,
            "privacy_safe": self.privacy_safe,
            "reasons": self.reasons,
        }


def evaluate_quality_gate(
    trust_score: float,
    schema_valid: bool,
    privacy_safe: bool,
    policy: QualityPolicy,
) -> QualityGateResult:
    """
    Determine whether a synthetic dataset
    satisfies the configured quality policy.
    """

    reasons = []

    trust_passed = (
        trust_score
        >= policy.minimum_trust_score
    )

    if not trust_passed:
        reasons.append(
            "Trust score is below the minimum "
            "required threshold."
        )

    if (
        policy.require_schema_valid
        and not schema_valid
    ):
        reasons.append(
            "Schema validation failed."
        )

    if (
        policy.require_privacy_safe
        and not privacy_safe
    ):
        reasons.append(
            "Privacy evaluation failed."
        )

    passed = len(reasons) == 0

    return QualityGateResult(
        passed=passed,
        trust_score=float(trust_score),
        schema_valid=bool(schema_valid),
        privacy_safe=bool(privacy_safe),
        reasons=reasons,
    )