from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pawpal_system import Owner, Pet, Scheduler, Task


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {"a", "an", "and", "for", "i", "my", "need", "the", "to", "with"}


@dataclass
class CareGuide:
    """Retrieved care guidance used to suggest a PawPal task."""

    id: int
    species: str
    topic: str
    keywords: str
    guidance: str
    suggested_task: str
    default_time: str
    duration_minutes: int
    priority: str
    frequency: str
    guardrail: str


@dataclass
class StyleExample:
    """Few-shot style template for specialized PawPal explanations."""

    style: str
    prefix: str
    focus: str
    template: str


@dataclass
class CarePlan:
    """End-to-end AI output for a pet care planning request."""

    pet_name: str
    request: str
    retrieved_guides: list[tuple[CareGuide, float]]
    suggested_tasks: list[Task]
    reasoning_steps: list[str]
    guardrails: list[str]
    conflicts: list[str]
    specialized_brief: str
    confidence: float


def tokenize(text: str) -> set[str]:
    """Tokenize transparent retrieval text."""
    return {token for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOPWORDS}


def load_care_guides(path: str | Path = "data/care_guides.csv") -> list[CareGuide]:
    """Load local pet-care guidance for retrieval."""
    guides = []
    with Path(path).open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            guides.append(
                CareGuide(
                    id=int(row["id"]),
                    species=row["species"],
                    topic=row["topic"],
                    keywords=row["keywords"],
                    guidance=row["guidance"],
                    suggested_task=row["suggested_task"],
                    default_time=row["default_time"],
                    duration_minutes=int(row["duration_minutes"]),
                    priority=row["priority"],
                    frequency=row["frequency"],
                    guardrail=row["guardrail"],
                )
            )
    return guides


def retrieve_guides(
    request: str,
    species: str,
    guides: list[CareGuide] | None = None,
    k: int = 2,
) -> list[tuple[CareGuide, float]]:
    """Retrieve species-aware care guides with token overlap."""
    guides = guides if guides is not None else load_care_guides()
    query_tokens = tokenize(" ".join([request, species]))
    ranked = []

    for guide in guides:
        if guide.species not in {"all", species.lower()}:
            continue
        guide_tokens = tokenize(" ".join([guide.species, guide.topic, guide.keywords, guide.guidance]))
        overlap = query_tokens & guide_tokens
        if overlap:
            ranked.append((guide, round(len(overlap) / max(len(query_tokens), 1), 4)))

    return sorted(ranked, key=lambda item: item[1], reverse=True)[:k]


def generate_care_plan(
    owner: Owner,
    pet_name: str,
    request: str,
    audience: str = "care",
    log_path: str | Path | None = "logs/ai_care_plans.jsonl",
) -> CarePlan:
    """Plan task suggestions from retrieved care guidance and schedule checks."""
    pet = owner.find_pet(pet_name)
    if pet is None:
        raise ValueError(f"Pet not found: {pet_name}")

    retrieved = retrieve_guides(request, pet.species)
    suggested_tasks = [
        Task(
            title=guide.suggested_task,
            time=guide.default_time,
            duration_minutes=guide.duration_minutes,
            priority=guide.priority,
            frequency=guide.frequency,
        )
        for guide, _ in retrieved
    ]

    simulated_pet = Pet(pet.name, pet.species, pet.age, tasks=list(pet.tasks))
    simulated_owner = Owner(owner.name, pets=[simulated_pet])
    for task in suggested_tasks:
        simulated_owner.pets[0].add_task(task)
    scheduler = Scheduler(simulated_owner)
    conflicts = scheduler.detect_conflicts(scheduler.filter_tasks(completed=False))
    guardrails = [guide.guardrail for guide, _ in retrieved]
    reasoning_steps = [
        f"Matched request to {guide.topic} guidance for {pet.species} care."
        for guide, _ in retrieved
    ]
    if conflicts:
        reasoning_steps.append("Detected schedule overlap after adding suggested tasks.")
    else:
        reasoning_steps.append("No exact same-time conflict detected after suggested tasks.")

    specialized = render_specialized_brief(pet.name, suggested_tasks, retrieved, audience)
    confidence = score_confidence(retrieved, conflicts)
    plan = CarePlan(
        pet_name=pet.name,
        request=request,
        retrieved_guides=retrieved,
        suggested_tasks=suggested_tasks,
        reasoning_steps=reasoning_steps,
        guardrails=guardrails,
        conflicts=conflicts,
        specialized_brief=specialized,
        confidence=confidence,
    )
    if log_path is not None:
        log_care_plan(log_path, plan)
    return plan


def apply_suggested_tasks(owner: Owner, pet_name: str, plan: CarePlan) -> int:
    """Add suggested tasks to the owner schedule."""
    pet = owner.find_pet(pet_name)
    if pet is None:
        raise ValueError(f"Pet not found: {pet_name}")
    for task in plan.suggested_tasks:
        pet.add_task(task)
    return len(plan.suggested_tasks)


def load_styles(path: str | Path = "data/style_examples.csv") -> dict[str, StyleExample]:
    """Load specialized output style examples."""
    styles = {}
    with Path(path).open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            styles[row["style"]] = StyleExample(
                style=row["style"],
                prefix=row["prefix"],
                focus=row["focus"],
                template=row["template"],
            )
    return styles


def choose_style(audience: str, conflicts: list[str] | None = None) -> str:
    """Choose a constrained explanation style."""
    if conflicts:
        return "safety_coach"
    if "busy" in audience.lower():
        return "busy_owner"
    return "care_coach"


def render_specialized_brief(
    pet_name: str,
    tasks: list[Task],
    retrieved: list[tuple[CareGuide, float]],
    audience: str,
) -> str:
    """Render a short specialized care brief."""
    styles = load_styles()
    conflicts: list[str] = []
    style = styles[choose_style(audience, conflicts)]
    task = tasks[0].title if tasks else "a schedule review"
    reason = (
        retrieved[0][0].guidance.rstrip(".")
        if retrieved
        else "the request did not match a guide"
    )
    return style.template.format(
        prefix=style.prefix,
        pet=pet_name,
        task=task,
        focus=style.focus,
        reason=reason,
    )


def score_confidence(retrieved: list[tuple[CareGuide, float]], conflicts: list[str]) -> float:
    """Return a simple reliability score for the generated plan."""
    retrieval_score = sum(score for _, score in retrieved)
    conflict_penalty = 0.15 if conflicts else 0
    return round(max(0.35, min(0.95, 0.55 + retrieval_score - conflict_penalty)), 2)


def log_care_plan(path: str | Path, plan: CarePlan) -> None:
    """Append a parseable JSONL trace of AI planning."""
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pet_name": plan.pet_name,
        "request": plan.request,
        "retrieved_guides": [
            {"topic": guide.topic, "score": score, "guardrail": guide.guardrail}
            for guide, score in plan.retrieved_guides
        ],
        "suggested_tasks": [task.to_dict() for task in plan.suggested_tasks],
        "reasoning_steps": plan.reasoning_steps,
        "conflicts": plan.conflicts,
        "specialized_brief": plan.specialized_brief,
        "confidence": plan.confidence,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
