from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo_owner():
    """Create sample data for the PawPal+ CLI demo."""
    owner = Owner("Jordan")

    mochi = Pet("Mochi", "dog", age=4)
    luna = Pet("Luna", "cat", age=2)

    mochi.add_task(
        Task("Morning walk", "08:00", 30, priority="high", frequency="daily")
    )
    mochi.add_task(Task("Heartworm medication", "12:00", 5, priority="high"))
    luna.add_task(Task("Breakfast", "07:30", 10, priority="high", frequency="daily"))
    luna.add_task(Task("Brush coat", "08:00", 15, priority="medium"))

    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner


def print_schedule(title, task_pairs):
    """Print a readable schedule section."""
    print(title)
    if not task_pairs:
        print("  No tasks found.")
        return

    for pet, task in task_pairs:
        print(f"  {task.summary(pet.name)}")


def main():
    """Run a CLI-first demo of the PawPal+ backend."""
    owner = build_demo_owner()
    scheduler = Scheduler(owner)

    print(f"PawPal+ schedule for {owner.name}")
    print("=" * 32)

    print_schedule("Today's Schedule", scheduler.todays_schedule())
    print()

    print_schedule(
        "High Priority First",
        scheduler.sort_by_priority_then_time(scheduler.todays_schedule()),
    )
    print()

    conflicts = scheduler.detect_conflicts(scheduler.todays_schedule())
    print("Conflict Warnings")
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts found.")
    print()

    scheduler.mark_task_complete("Mochi", "Morning walk")
    next_walks = [
        (pet, task)
        for pet, task in owner.all_tasks()
        if pet.name == "Mochi" and task.title == "Morning walk" and task.due_date > date.today()
    ]
    print_schedule("Recurring Task Created", next_walks)


if __name__ == "__main__":
    main()
