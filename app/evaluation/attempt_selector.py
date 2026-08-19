from typing import Any


def select_best_attempt(
    attempts: list[Any],
) -> Any | None:
    """
    Select the attempt with the highest trust score.

    Returns None when no attempts are available.
    """

    if not attempts:
        return None

    return max(
        attempts,
        key=lambda attempt: (
            attempt.trust_score
            if attempt.trust_score is not None
            else 0.0
        ),
    )