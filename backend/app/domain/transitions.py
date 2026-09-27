"""Explicit complaint status transition table.

Backend architecture (docs/architecture/backend.md §4) requires this as data,
not scattered if/elif chains, so it's auditable and independently testable.
The frontend must never duplicate this table.
"""

from app.domain.enums import Status

ALLOWED_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.OPEN: frozenset({Status.IN_PROGRESS, Status.REJECTED}),
    Status.IN_PROGRESS: frozenset({Status.RESOLVED, Status.REJECTED}),
    Status.RESOLVED: frozenset(),
    Status.REJECTED: frozenset(),
}


def is_transition_allowed(current: Status, target: Status) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
