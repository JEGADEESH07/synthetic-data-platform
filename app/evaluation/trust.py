from dataclasses import dataclass


@dataclass(frozen=True)
class TrustScore:
    """
    Overall trust assessment for a synthetic dataset.
    """

    fidelity_score: float
    confidence_score: float
    trust_score: float
    level: str

    def to_dict(self) -> dict:
        """
        Convert the trust score to a dictionary.
        """

        return {
            "fidelity_score": self.fidelity_score,
            "confidence_score": self.confidence_score,
            "trust_score": self.trust_score,
            "level": self.level,
        }


def calculate_trust_score(
    fidelity_score: float,
    confidence_score: float,
) -> TrustScore:
    """
    Calculate the overall trust score.

    Fidelity contributes 70%.
    Evaluation confidence contributes 30%.
    """

    fidelity_score = max(
        0.0,
        min(1.0, fidelity_score),
    )

    confidence_score = max(
        0.0,
        min(1.0, confidence_score),
    )

    trust_score = (
        0.70 * fidelity_score
        + 0.30 * confidence_score
    )

    trust_score = max(
        0.0,
        min(1.0, trust_score),
    )

    if trust_score >= 0.90:
        level = "excellent"

    elif trust_score >= 0.80:
        level = "high"

    elif trust_score >= 0.70:
        level = "good"

    elif trust_score >= 0.60:
        level = "moderate"

    else:
        level = "low"

    return TrustScore(
        fidelity_score=float(fidelity_score),
        confidence_score=float(confidence_score),
        trust_score=float(trust_score),
        level=level,
    )