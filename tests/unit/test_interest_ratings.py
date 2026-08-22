import pytest

from movievoter.services.interest_ratings import required_interest_ratings


@pytest.mark.parametrize(
    ("participants", "expected"),
    [
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 3),
        (10, 3),
        (12, 3),
        (13, 4),
        (20, 5),
        (40, 10),
        (100, 10),
    ],
)
def test_dynamic_interest_quorum(participants: int, expected: int) -> None:
    assert required_interest_ratings(participants) == expected


def test_negative_participant_count_is_rejected() -> None:
    with pytest.raises(ValueError):
        required_interest_ratings(-1)
