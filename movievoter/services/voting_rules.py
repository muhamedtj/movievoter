from __future__ import annotations

MIN_VOTERS_FOR_EARLY_FINISH = 3


def should_finish_poll_early(
    voter_count: int,
    option_counts: list[int] | tuple[int, ...],
) -> bool:
    if voter_count < MIN_VOTERS_FOR_EARLY_FINISH:
        return False
    if voter_count <= 0:
        return False
    return any(count / voter_count > 0.5 for count in option_counts)
