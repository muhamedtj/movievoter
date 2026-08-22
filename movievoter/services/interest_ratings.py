from __future__ import annotations

import math

MIN_INTEREST_RATINGS = 3
MAX_INTEREST_RATINGS = 10
INTEREST_QUORUM_RATIO = 0.25


def required_interest_ratings(participant_count: int) -> int:
    """Return the dynamic pre-vote rating quorum."""
    if participant_count < 0:
        raise ValueError("participant_count cannot be negative")
    if participant_count <= 2:
        return participant_count
    return min(
        MAX_INTEREST_RATINGS,
        max(MIN_INTEREST_RATINGS, math.ceil(participant_count * INTEREST_QUORUM_RATIO)),
    )
