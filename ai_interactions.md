# AI Interactions Log

## Agentic Workflow

I used Codex to help convert the corrected Module 2 PawPal+ project into an applied AI system. The workflow was:

1. Clone the corrected Module 2 project from GitHub.
2. Inspect the existing `Owner`, `Pet`, `Task`, and `Scheduler` classes.
3. Add a custom pet-care retrieval corpus.
4. Build an AI care planner that retrieves guidance, suggests tasks, simulates schedule impact, checks conflicts, applies guardrails, and logs reasoning.
5. Integrate the planner into the CLI and Streamlit app.
6. Add tests and a reliability evaluation script.
7. Fix a planning mutation risk so generated plans do not alter the real schedule before confirmation.
8. Replace emoji-heavy CLI labels with ASCII-safe output for reproducible grading.

## Helpful AI Suggestion

The most helpful suggestion was to keep PawPal's original scheduler as the stable core and add AI planning around it. That made the final project clearly connected to Module 2 while adding retrieval, guardrails, and reliability testing.

## Flawed AI Suggestion

The first simulation design reused the original pet object. That could have accidentally added AI suggestions during planning. The corrected version copies the pet's current task list and only mutates the real schedule when `apply_suggested_tasks()` is called.

## Intermediate Reasoning Trace Example

```text
Request: Mochi needs a daily dog walk and heartworm medication reminder.
Step 1: Retrieve dog medication guidance.
Step 2: Retrieve dog exercise guidance.
Step 3: Convert retrieved guides into suggested Task objects.
Step 4: Simulate schedule impact and detect exact-time conflicts.
Step 5: Return guardrails and confidence score.
Step 6: Apply suggested tasks only after explicit confirmation.
```
