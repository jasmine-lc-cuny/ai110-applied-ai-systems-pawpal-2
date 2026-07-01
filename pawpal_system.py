from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """Represent one scheduled pet care activity."""

    title: str
    time: str
    duration_minutes: int
    priority: str = "medium"
    frequency: str = "once"
    due_date: date = field(default_factory=date.today)
    completed: bool = False

    def mark_complete(self):
        """Mark this task as complete."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """Create the next task for daily or weekly recurring tasks."""
        if self.frequency == "daily":
            next_date = self.due_date + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = self.due_date + timedelta(weeks=1)
        else:
            return None

        return Task(
            title=self.title,
            time=self.time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            due_date=next_date,
        )

    def summary(self, pet_name: str | None = None, use_emoji: bool = False) -> str:
        """Return a readable one-line description for CLI output."""
        pet_prefix = f"{pet_name}: " if pet_name else ""
        if use_emoji:
            status = "✅ done" if self.completed else "⏳ open"
        else:
            status = "done" if self.completed else "open"
        return (
            f"{self.time} - {pet_prefix}{self.title} "
            f"({self.duration_minutes} min, {self.priority}, "
            f"{self.frequency}, {self.due_date.isoformat()}, {status})"
        )

    def to_dict(self) -> dict[str, object]:
        """Convert this task into a JSON-friendly dictionary."""
        return {
            "title": self.title,
            "time": self.time,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "frequency": self.frequency,
            "due_date": self.due_date.isoformat(),
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Task":
        """Create a task from a JSON-friendly dictionary."""
        return cls(
            title=str(data["title"]),
            time=str(data["time"]),
            duration_minutes=int(data["duration_minutes"]),
            priority=str(data.get("priority", "medium")),
            frequency=str(data.get("frequency", "once")),
            due_date=date.fromisoformat(str(data.get("due_date", date.today().isoformat()))),
            completed=bool(data.get("completed", False)),
        )


@dataclass
class Pet:
    """Store pet details and assigned care tasks."""

    name: str
    species: str
    age: int | None = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a task to this pet."""
        self.tasks.append(task)

    def incomplete_tasks(self) -> list[Task]:
        """Return this pet's incomplete tasks."""
        return [task for task in self.tasks if not task.completed]

    def to_dict(self) -> dict[str, object]:
        """Convert this pet into a JSON-friendly dictionary."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Pet":
        """Create a pet from a JSON-friendly dictionary."""
        pet = cls(
            name=str(data["name"]),
            species=str(data["species"]),
            age=None if data.get("age") is None else int(data["age"]),
        )
        for task_data in data.get("tasks", []):
            pet.add_task(Task.from_dict(task_data))
        return pet


@dataclass
class Owner:
    """Manage a pet owner's pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Add a pet to this owner."""
        self.pets.append(pet)

    def find_pet(self, pet_name: str) -> Pet | None:
        """Return the pet with a matching name, if it exists."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet
        return None

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def to_dict(self) -> dict[str, object]:
        """Convert this owner into a JSON-friendly dictionary."""
        return {
            "name": self.name,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Owner":
        """Create an owner from a JSON-friendly dictionary."""
        owner = cls(name=str(data["name"]))
        for pet_data in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pet_data))
        return owner

    def save_to_json(self, path: str | Path):
        """Persist this owner and all associated pets/tasks to JSON."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2)

    @classmethod
    def load_from_json(cls, path: str | Path) -> "Owner":
        """Load an owner and its pets/tasks from JSON."""
        file_path = Path(path)
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls.from_dict(data)


class Scheduler:
    """Organize and manage care tasks across an owner account."""

    def __init__(self, owner: Owner):
        """Create a scheduler for one owner."""
        self.owner = owner

    def sort_by_time(self, tasks: list[tuple[Pet, Task]] | None = None):
        """Return tasks sorted chronologically by HH:MM time."""
        task_pairs = tasks if tasks is not None else self.owner.all_tasks()
        return sorted(task_pairs, key=lambda pair: pair[1].time)

    def sort_by_priority_then_time(self, tasks: list[tuple[Pet, Task]] | None = None):
        """Return tasks sorted by priority first, then time."""
        task_pairs = tasks if tasks is not None else self.owner.all_tasks()
        return sorted(
            task_pairs,
            key=lambda pair: (PRIORITY_ORDER.get(pair[1].priority, 99), pair[1].time),
        )

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None):
        """Filter tasks by pet name and completion status."""
        task_pairs = self.owner.all_tasks()

        if pet_name:
            task_pairs = [
                (pet, task)
                for pet, task in task_pairs
                if pet.name.lower() == pet_name.lower()
            ]

        if completed is not None:
            task_pairs = [
                (pet, task)
                for pet, task in task_pairs
                if task.completed is completed
            ]

        return task_pairs

    def detect_conflicts(self, tasks: list[tuple[Pet, Task]] | None = None):
        """Return warnings for tasks scheduled at the exact same date and time."""
        task_pairs = tasks if tasks is not None else self.owner.all_tasks()
        seen: dict[tuple[date, str], list[str]] = {}

        for pet, task in task_pairs:
            key = (task.due_date, task.time)
            seen.setdefault(key, []).append(f"{pet.name}: {task.title}")

        warnings = []
        for (due_date, time), labels in seen.items():
            if len(labels) > 1:
                joined = ", ".join(labels)
                warnings.append(
                    f"Conflict on {due_date.isoformat()} at {time}: {joined}"
                )

        return warnings

    def mark_task_complete(self, pet_name: str, task_title: str) -> Task | None:
        """Complete a matching task and add its next recurring occurrence."""
        pet = self.owner.find_pet(pet_name)
        if pet is None:
            return None

        for task in pet.tasks:
            if task.title.lower() == task_title.lower() and not task.completed:
                task.mark_complete()
                next_task = task.next_occurrence()
                if next_task is not None:
                    pet.add_task(next_task)
                return task

        return None

    def todays_schedule(self):
        """Return today's open tasks sorted by time."""
        today = date.today()
        open_today = [
            (pet, task)
            for pet, task in self.owner.all_tasks()
            if task.due_date == today and not task.completed
        ]
        return self.sort_by_time(open_today)

    def get_next_urgent_task(self, tasks: list[tuple[Pet, Task]] | None = None):
        """Return the highest-priority open task, breaking ties by earlier time."""
        task_pairs = tasks if tasks is not None else self.todays_schedule()
        if not task_pairs:
            return None
        return self.sort_by_priority_then_time(task_pairs)[0]

    def get_top_priority_tasks(self, limit: int = 3, tasks: list[tuple[Pet, Task]] | None = None):
        """Return the highest-priority tasks up to the requested limit."""
        task_pairs = tasks if tasks is not None else self.todays_schedule()
        if not task_pairs:
            return []
        return self.sort_by_priority_then_time(task_pairs)[:limit]
