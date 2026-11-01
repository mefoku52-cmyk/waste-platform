"""Prijatie a rozbor zadania."""

from __future__ import annotations

from .models import RiskLevel, Task, TaskAssignment, TaskPriority


class TaskIntake:
    """Prijme zadanie a rozlozi ho na ulohy."""

    SPLIT_WORDS = [" a ", " potom ", " najprv ", " následne ", " a zároveň "]

    def accept(
        self,
        title: str,
        description: str,
        constraints: list[str] | None = None,
        unverified: list[str] | None = None,
    ) -> TaskAssignment:
        assignment = TaskAssignment(
            title=title,
            description=description,
            constraints=constraints or [],
            unverified_assumptions=unverified or [],
        )

        # Jednoduchy rozklad: ak text obsahuje oddeľovače, rozdelime na ulohy
        parts = self._split_description(description)
        for i, part in enumerate(parts):
            if not part.strip():
                continue
            task = self.create_task(
                title=f"{title} - cast {i + 1}" if len(parts) > 1 else title,
                description=part.strip(),
                priority=TaskPriority.MEDIUM,
                risk=RiskLevel.LOW,
            )
            self.add_task(assignment, task)

        return assignment

    def _split_description(self, description: str) -> list[str]:
        """Rozdeli text podla oddeľovačov na menšie casti."""
        text = description
        for word in self.SPLIT_WORDS:
            text = text.replace(word, "|")
        parts = [p.strip() for p in text.split("|") if p.strip()]
        return parts if parts else [description]

    def add_task(self, assignment: TaskAssignment, task: Task) -> None:
        assignment.tasks.append(task)

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        risk: RiskLevel = RiskLevel.LOW,
        dependencies: list[str] | None = None,
        criteria: list[str] | None = None,
    ) -> Task:
        return Task(
            title=title,
            description=description,
            priority=priority,
            risk=risk,
            dependencies=dependencies or [],
            completion_criteria=criteria or [],
        )
