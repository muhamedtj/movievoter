from enum import StrEnum


class MovieStatus(StrEnum):
    WAITING = "waiting"
    VOTING = "voting"
    WATCHING = "watching"
    DONE = "done"


class Stage(StrEnum):
    VOTING = "voting"
    WINNER = "winner"
    FINAL_RATING = "final_rating"
    FINAL = "final"


class ReportStatus(StrEnum):
    OPEN = "OPEN"
    FIXED = "FIXED"
    CLOSED = "CLOSED"
