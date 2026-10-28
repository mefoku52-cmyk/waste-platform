"""Model uloh pre riadiace jadro CMEP."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


class TaskStatus(enum.Enum):
    PLANNED = "planned"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """Jednotka prace v riadiacom systeme."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PLANNED
    priority: TaskPriority = TaskPriority.MEDIUM
    risk: RiskLevel = RiskLevel.LOW
    dependencies: list[str] = field(default_factory=list)
    completion_criteria: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    result: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "risk": self.risk.value,
            "dependencies": self.dependencies,
            "completion_criteria": self.completion_criteria,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "planned")),
            priority=TaskPriority(data.get("priority", "medium")),
            risk=RiskLevel(data.get("risk", "low")),
            dependencies=data.get("dependencies", []),
            completion_criteria=data.get("completion_criteria", []),
            created_at=data.get("created_at", datetime.now(UTC).isoformat()),
            updated_at=data.get("updated_at", datetime.now(UTC).isoformat()),
            result=data.get("result"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TaskAssignment:
    """Zadanie prijate systemom."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    constraints: list[str] = field(default_factory=list)
    unverified_assumptions: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "constraints": self.constraints,
            "unverified_assumptions": self.unverified_assumptions,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskAssignment:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            constraints=data.get("constraints", []),
            unverified_assumptions=data.get("unverified_assumptions", []),
            tasks=[Task.from_dict(t) for t in data.get("tasks", [])],
            created_at=data.get("created_at", datetime.now(UTC).isoformat()),
        )
