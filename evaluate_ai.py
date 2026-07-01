from main import build_demo_owner
from pawpal_ai import generate_care_plan


CASES = [
    {
        "name": "dog exercise request retrieves exercise guide",
        "pet": "Mochi",
        "request": "Mochi needs a daily dog walk and exercise routine.",
        "expected_topic": "exercise",
    },
    {
        "name": "cat grooming request creates grooming task",
        "pet": "Luna",
        "request": "Luna needs cat brushing and coat grooming reminders.",
        "expected_topic": "grooming",
        "expected_task": "AI grooming session",
    },
    {
        "name": "medication request includes safety guardrail",
        "pet": "Mochi",
        "request": "Help me remember dog heartworm medication.",
        "expected_topic": "medication",
        "guardrail_phrase": "Do not invent medication names",
    },
]


def evaluate() -> int:
    print("PawPal AI Reliability Evaluation")
    print("================================")
    passed = 0

    for case in CASES:
        owner = build_demo_owner()
        plan = generate_care_plan(
            owner,
            case["pet"],
            case["request"],
            log_path="logs/evaluation_runs.jsonl",
        )
        topics = [guide.topic for guide, _ in plan.retrieved_guides]
        tasks = [task.title for task in plan.suggested_tasks]
        checks = [case["expected_topic"] in topics]
        if "expected_task" in case:
            checks.append(case["expected_task"] in tasks)
        if "guardrail_phrase" in case:
            checks.append(any(case["guardrail_phrase"] in guardrail for guardrail in plan.guardrails))

        status = "PASS" if all(checks) else "FAIL"
        passed += int(all(checks))
        print(f"{status}: {case['name']}")
        print(f"  Pet: {case['pet']}")
        print(f"  Retrieved: {', '.join(topics) or 'none'}")
        print(f"  Suggested tasks: {', '.join(tasks) or 'none'}")
        print(f"  Confidence: {plan.confidence}")
        print(f"  Brief: {plan.specialized_brief}")

    print(f"\nSummary: {passed} out of {len(CASES)} checks passed.")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(evaluate())
