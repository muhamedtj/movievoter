from movievoter.services.voting_rules import should_finish_poll_early


def test_early_finish_requires_three_voters() -> None:
    assert not should_finish_poll_early(2, [2, 0])


def test_early_finish_requires_strict_majority() -> None:
    assert not should_finish_poll_early(4, [2, 2])
    assert should_finish_poll_early(5, [3, 2])


def test_early_finish_works_with_multiple_options() -> None:
    assert should_finish_poll_early(6, [4, 1, 1])
    assert not should_finish_poll_early(6, [3, 2, 1])
