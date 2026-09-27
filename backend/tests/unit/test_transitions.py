"""Status transition table — docs/architecture/backend.md §4."""

import pytest

from app.domain.enums import Status
from app.domain.transitions import is_transition_allowed

ALL_STATUSES = list(Status)


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [
        (Status.OPEN, Status.IN_PROGRESS, True),
        (Status.OPEN, Status.REJECTED, True),
        (Status.OPEN, Status.RESOLVED, False),
        (Status.OPEN, Status.OPEN, False),
        (Status.IN_PROGRESS, Status.RESOLVED, True),
        (Status.IN_PROGRESS, Status.REJECTED, True),
        (Status.IN_PROGRESS, Status.OPEN, False),
        (Status.RESOLVED, Status.OPEN, False),
        (Status.RESOLVED, Status.IN_PROGRESS, False),
        (Status.RESOLVED, Status.REJECTED, False),
        (Status.REJECTED, Status.OPEN, False),
        (Status.REJECTED, Status.RESOLVED, False),
    ],
)
def test_transition_matrix(current: Status, target: Status, expected: bool) -> None:
    assert is_transition_allowed(current, target) is expected


@pytest.mark.parametrize("terminal", [Status.RESOLVED, Status.REJECTED])
def test_terminal_states_have_no_allowed_transitions(terminal: Status) -> None:
    assert all(not is_transition_allowed(terminal, target) for target in ALL_STATUSES)
