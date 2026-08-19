from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationResult:
    """
    Unified evaluation result for a synthetic dataset.
    """

    schema: dict[str, Any] = field(
        default_factory=dict
    )

    statistical_quality: dict[str, Any] = field(
        default_factory=dict
    )

    privacy: dict[str, Any] = field(
        default_factory=dict
    )
    confidence: dict[str, Any] = field(
        default_factory=dict
    )
    trust: dict[str, Any] = field(
        default_factory=dict
    )
    quality_gate: dict[str, Any] = field(
    default_factory=dict
    )
    @property
    def schema_valid(self) -> bool:
        """
        Return whether schema validation passed.

        """

        return bool(
            self.schema.get("valid", False)
        )

    @property
    def privacy_safe(self) -> bool:
        """
        Return whether privacy evaluation passed.
        """

        return bool(
            self.privacy.get("safe", False)
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the evaluation result to a dictionary.
        """

        return {
            "schema": self.schema,
            "statistical_quality": (
                self.statistical_quality
            ),
            "privacy": self.privacy,
            "confidence": self.confidence,
            "trust": self.trust,
            "quality_gate": self.quality_gate,
        }