from datetime import date, timedelta

from main import build_demo_owner
from pawpal_ai import (
    apply_suggested_tasks,
    generate_care_plan,
    retrieve_guides,
)
from pawpal_system import Owner, Pet, Scheduler, Task


def test_owner_persistence_round_trip(tmp_path):
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Morning walk", "08:00", 30, priority="high"))
    owner.add_pet(pet)
    path = tmp_path / "owner.json"

    owner.save_to_json(path)
    reloaded = Owner.load_from_json(path)

    assert reloaded.name == "Jordan"
    assert len(reloaded.pets) == 1
    assert reloaded.pets[0].name == "Mochi"
    assert reloaded.pets[0].tasks[0].title == "Morning walk"
    assert reloaded.pets[0].tasks[0].priority == "high"


def test_task_completion_marks_status():
    task = Task("Feed breakfast", "07:30", 10)

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")

    pet.add_task(Task("Morning walk", "08:00", 30))

    assert len(pet.tasks) == 1


def test_scheduler_sorts_tasks_by_time():
    owner = Owner("Jordan")
    pet = Pet("Luna", "cat")
    pet.add_task(Task("Dinner", "18:00", 10))
    pet.add_task(Task("Breakfast", "07:30", 10))
    owner.add_pet(pet)

    sorted_tasks = Scheduler(owner).sort_by_time()

    assert [task.title for _, task in sorted_tasks] == ["Breakfast", "Dinner"]


def test_filter_tasks_by_pet_and_status():
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    completed = Task("Medication", "12:00", 5, completed=True)
    open_task = Task("Brush coat", "08:00", 15)
    mochi.add_task(completed)
    luna.add_task(open_task)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    filtered = Scheduler(owner).filter_tasks(pet_name="Luna", completed=False)

    assert filtered == [(luna, open_task)]


def test_daily_recurrence_creates_tomorrows_task():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    task = Task("Morning walk", "08:00", 30, frequency="daily")
    pet.add_task(task)
    owner.add_pet(pet)

    completed = Scheduler(owner).mark_task_complete("Mochi", "Morning walk")

    assert completed is task
    assert task.completed is True
    assert len(pet.tasks) == 2
    assert pet.tasks[1].due_date == date.today() + timedelta(days=1)
    assert pet.tasks[1].completed is False


def test_conflict_detection_flags_duplicate_times():
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    mochi.add_task(Task("Morning walk", "08:00", 30))
    luna.add_task(Task("Brush coat", "08:00", 15))
    owner.add_pet(mochi)
    owner.add_pet(luna)

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]
    assert "Mochi: Morning walk" in warnings[0]
    assert "Luna: Brush coat" in warnings[0]


def test_scheduler_selects_urgent_task_by_priority_and_time():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Low priority check", "10:00", 10, priority="low"))
    pet.add_task(Task("Medication", "07:00", 5, priority="high"))
    pet.add_task(Task("Another high task", "08:00", 5, priority="high"))
    owner.add_pet(pet)

    urgent = Scheduler(owner).get_next_urgent_task()

    assert urgent is not None
    assert urgent[1].title == "Medication"


def test_scheduler_returns_top_three_priority_tasks():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Low priority check", "10:00", 10, priority="low"))
    pet.add_task(Task("Medication", "07:00", 5, priority="high"))
    pet.add_task(Task("Another high task", "08:00", 5, priority="high"))
    pet.add_task(Task("Medium task", "09:00", 10, priority="medium"))
    owner.add_pet(pet)

    top_three = Scheduler(owner).get_top_priority_tasks(limit=3)

    assert len(top_three) == 3
    assert [task.title for _, task in top_three] == [
        "Medication",
        "Another high task",
        "Medium task",
    ]


def test_ai_retriever_is_species_aware():
    dog_results = retrieve_guides("daily dog walk exercise", "dog", k=1)
    cat_results = retrieve_guides("cat brushing coat grooming", "cat", k=1)

    assert dog_results[0][0].topic == "exercise"
    assert cat_results[0][0].topic == "grooming"


def test_ai_care_plan_suggests_tasks_without_mutating_owner():
    owner = build_demo_owner()
    original_count = len(owner.find_pet("Mochi").tasks)

    plan = generate_care_plan(
        owner,
        "Mochi",
        "Mochi needs a daily dog walk and medication reminder.",
        log_path=None,
    )

    assert len(owner.find_pet("Mochi").tasks) == original_count
    assert any(task.title == "AI suggested walk" for task in plan.suggested_tasks)
    assert plan.confidence > 0
    assert plan.reasoning_steps


def test_ai_plan_can_be_applied_to_owner_schedule():
    owner = build_demo_owner()
    original_count = len(owner.find_pet("Luna").tasks)
    plan = generate_care_plan(
        owner,
        "Luna",
        "Luna needs cat brushing and coat grooming reminders.",
        log_path=None,
    )

    added = apply_suggested_tasks(owner, "Luna", plan)

    assert added == len(plan.suggested_tasks)
    assert len(owner.find_pet("Luna").tasks) == original_count + added
    assert any(task.title == "AI grooming session" for task in owner.find_pet("Luna").tasks)


def test_ai_plan_includes_medication_guardrail():
    owner = build_demo_owner()

    plan = generate_care_plan(
        owner,
        "Mochi",
        "Help me remember dog heartworm medication.",
        log_path=None,
    )

    assert plan.retrieved_guides[0][0].topic == "medication"
    assert any("Do not invent medication names" in guardrail for guardrail in plan.guardrails)
