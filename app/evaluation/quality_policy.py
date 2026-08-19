from dataclasses import dataclass


@dataclass(frozen=True)
class QualityDecision:
    """
    Decision describing what the job should do
    after quality-gate evaluation.
    """

    action: str
    reason: str


def decide_quality_action(
    gate_passed: bool,
    mode: str,
) -> QualityDecision:
    """
    Determine the job action after quality evaluation.
    """

    if gate_passed:
        return QualityDecision(
            action="complete",
            reason="Quality gate passed.",
        )

    if mode == "report":
        return QualityDecision(
            action="complete",
            reason=(
                "Quality gate failed, but report mode "
                "allows completion."
            ),
        )

    if mode == "block":
        return QualityDecision(
            action="fail",
            reason=(
                "Quality gate failed and block mode "
                "rejects the result."
            ),
        )

    if mode == "regenerate":
        return QualityDecision(
            action="regenerate",
            reason=(
                "Quality gate failed and regeneration "
                "was requested."
            ),
        )

    raise ValueError(
        f"Unsupported quality policy mode: {mode}"
    )