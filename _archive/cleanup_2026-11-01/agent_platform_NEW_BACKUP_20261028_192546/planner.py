"""Planovac uloh - kontrola cyklickych zavislosti a blokovanych uloh."""

from __future__ import annotations

from .models import Task, TaskStatus


class CyclicDependencyError(Exception):
    """Zavislosti tvoria cyklus."""


class MissingDependencyError(Exception):
    """Zavislost odkazuje na neexistujucu ulohu."""


class Planner:
    """Planuje a validuje ulohy. Kahnov algoritmus pre detekciu cyklov."""

    def __init__(self, tasks: list[Task]):
        self.tasks = list(tasks)
        self._index = {t.id: t for t in self.tasks}
        self._duplicate_ids = len(self._index) != len(self.tasks)

    def validate(self) -> tuple[bool, str]:
        """Validuje plan. Vrati (True, '') ak OK, inak (False, dovod)."""
        # Duplicitné ID robia graf nejednoznačným.
        if self._duplicate_ids:
            return False, "Duplicitné ID úloh"

        # Kontrola existencie závislostí
        for t in self.tasks:
            for dep in t.dependencies:
                if dep not in self._index:
                    return False, f"Neexistujuca zavislost: {dep} (uloha {t.id})"
        # Detekcia cyklov (Kahn)
        in_degree = {t.id: 0 for t in self.tasks}
        for t in self.tasks:
            for dep in t.dependencies:
                if dep in in_degree:
                    in_degree[t.id] += 1
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        processed = 0
        while queue:
            node = queue.pop(0)
            processed += 1
            for t in self.tasks:
                if node in t.dependencies:
                    in_degree[t.id] -= 1
                    if in_degree[t.id] == 0:
                        queue.append(t.id)
        if processed != len(self.tasks):
            return False, "Cyklicke zavislosti detekovane"
        return True, ""

    def detect_cycles(self) -> list[str]:
        """Vráti iba ID úloh, ktoré patria do cyklov."""
        adjacency: dict[str, list[str]] = {task.id: list(task.dependencies) for task in self.tasks}
        valid_ids = set(adjacency)
        adjacency = {
            task_id: [dep for dep in deps if dep in valid_ids]
            for task_id, deps in adjacency.items()
        }

        index = 0
        indices: dict[str, int] = {}
        lowlink: dict[str, int] = {}
        stack: list[str] = []
        on_stack: set[str] = set()
        cyclic: set[str] = set()

        def strongconnect(node: str) -> None:
            nonlocal index
            indices[node] = lowlink[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)

            for neighbor in adjacency[node]:
                if neighbor not in indices:
                    strongconnect(neighbor)
                    lowlink[node] = min(lowlink[node], lowlink[neighbor])
                elif neighbor in on_stack:
                    lowlink[node] = min(lowlink[node], indices[neighbor])

            if lowlink[node] == indices[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack.remove(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1 or node in adjacency[node]:
                    cyclic.update(component)

        for task in self.tasks:
            if task.id not in indices:
                strongconnect(task.id)

        return [task.id for task in self.tasks if task.id in cyclic]

    def get_blocked(self) -> list[Task]:
        """Ulohy, ktore cakaju na neukoncene zavislosti."""
        completed_ids = {t.id for t in self.tasks if t.status == TaskStatus.COMPLETED}
        blocked = []
        for t in self.tasks:
            if t.status == TaskStatus.COMPLETED:
                continue
            unmet = [d for d in t.dependencies if d not in completed_ids]
            if unmet:
                blocked.append(t)
        return blocked

    def get_ready(self) -> list[Task]:
        """Ulohy pripravene na vykonanie (vsetky zavislosti splnene)."""
        completed_ids = {t.id for t in self.tasks if t.status == TaskStatus.COMPLETED}
        ready = []
        for t in self.tasks:
            if t.status not in (TaskStatus.PLANNED, TaskStatus.BLOCKED):
                continue
            if all(d in completed_ids for d in t.dependencies):
                ready.append(t)
        return ready

    def topological_order(self) -> list[Task]:
        """Topologicky utriedeny zoznam uloh. Vyhadzuje vynimku pri neplatnom grafe."""
        ok, msg = self.validate()
        if not ok:
            if "Neexistujuca" in msg:
                raise MissingDependencyError(msg)
            raise CyclicDependencyError(msg)
        in_degree = {t.id: 0 for t in self.tasks}
        for t in self.tasks:
            for dep in t.dependencies:
                if dep in in_degree:
                    in_degree[t.id] += 1
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result: list[Task] = []
        while queue:
            node = queue.pop(0)
            task = self._index.get(node)
            if task:
                result.append(task)
            for t in self.tasks:
                if node in t.dependencies:
                    in_degree[t.id] -= 1
                    if in_degree[t.id] == 0:
                        queue.append(t.id)
        return result
