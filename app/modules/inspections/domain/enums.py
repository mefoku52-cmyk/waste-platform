"""inspections domain enums."""

from enum import Enum


class InspectionState(str, Enum):
    """Stav obhliadky — zrkadlenie stavoveho stroja CMEP Streaming rooms.

    created      — zaznam vytvoreny, publisher token vystaveny, room este neexistuje
    room_created — streaming potvrdil createRoom (event inspection_requested, role=owner)
    requested    — viewer poziadal o obhliadku (requestInspection)
    accepted     — publisher schvalil (acceptInspection)
    live         — viewer sa pripojil (joinRoom) — stream bezi
    ended        — terminalny stav (roomClosed / owner_left / platformovy end)
    """

    CREATED = "created"
    ROOM_CREATED = "room_created"
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    LIVE = "live"
    ENDED = "ended"

    @classmethod
    def active_states(cls) -> frozenset["InspectionState"]:
        """Stavy, v ktorych je obhliadka ziva (nie je terminalna)."""
        return frozenset({cls.CREATED, cls.ROOM_CREATED, cls.REQUESTED, cls.ACCEPTED, cls.LIVE})

    @property
    def is_active(self) -> bool:
        return self in InspectionState.active_states()


class InspectionRole(str, Enum):
    """Rola ucastnika obhliadky v streamovacom tokene."""

    PUBLISHER = "publisher"
    VIEWER = "viewer"


class InspectionEventType(str, Enum):
    """Whitelist eventov prijimanych zo streamingu (zhodne s events.js)."""

    REQUESTED = "inspection_requested"
    ACCEPTED = "inspection_accepted"
    REJECTED = "inspection_rejected"
    STARTED = "inspection_started"
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    CONNECTION_FAILED = "connection_failed"
    ENDED = "inspection_ended"
