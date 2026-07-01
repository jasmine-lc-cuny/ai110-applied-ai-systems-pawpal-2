# Model Card: PawPal AI

## Model Name

PawPal AI: Applied Pet Care Planning System

## Intended Use

PawPal AI is intended to help pet owners organize care routines by suggesting schedule tasks from owner-provided goals. It is a classroom project and portfolio artifact. It is not veterinary advice and should not be used for diagnosis, treatment, medication dosing, or emergency decisions.

## Original Project

The system extends my Module 2 PawPal+ project, an object-oriented scheduler for pets, owners, tasks, recurring routines, conflict detection, JSON persistence, and Streamlit interaction.

## How The System Works

The user gives a care request for a pet. The system retrieves matching guidance from `data/care_guides.csv`, converts the guidance into suggested `Task` objects, simulates the schedule impact, checks for exact-time conflicts, returns reasoning steps and guardrails, produces a specialized brief, and logs the plan.

## Data

The retrieval corpus is a small custom CSV of pet-care scheduling guidance. It includes dog exercise, dog medication reminders, cat feeding, cat grooming, senior care, and conflict-safety guidance. The style examples are a tiny synthetic few-shot dataset for specialized output tone.

## Limitations and Biases

The system only knows the care guide entries provided in the repository. It may miss species, ages, routines, or health needs not represented in the guide file. It also assumes that exact same-time overlaps are the main schedule conflict, which is simpler than real life.

Because the guides are manually written, they reflect the author's assumptions about common pet-care needs. The system should not be treated as a universal pet-care authority.

## Misuse and Prevention

Possible misuse would be using the system for medical decisions. To reduce that risk, medication guidance explicitly says not to invent medication names or dosages, and senior/sick pet concerns are framed as veterinarian-review issues. The system suggests reminders, not treatment plans.

## Reliability Testing

The project includes 13 unit tests and a scenario evaluation harness. Tests verify the original scheduler behavior, AI retrieval, non-mutating planning, applying suggestions, and medication guardrails. The evaluation harness passed 3 out of 3 cases.

## What Surprised Me

The biggest implementation lesson was that planning should not silently mutate the live schedule. The AI planner now simulates suggested tasks first, then only applies them when explicitly requested.

## AI Collaboration Reflection

I used AI to help transform the Module 2 scheduler into an applied AI system. A helpful suggestion was to keep the original object-oriented scheduler as the reliable core and add retrieval/planning around it. A flawed early design reused the original pet object during simulation, which could have changed the real schedule before confirmation; testing and review caught that, and the planner now uses a copied pet for simulation.
