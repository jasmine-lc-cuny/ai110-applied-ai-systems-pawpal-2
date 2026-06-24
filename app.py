import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")


def get_owner():
    """Return the session's owner object, creating it once if needed."""
    if "owner" not in st.session_state:
        st.session_state.owner = Owner("Jordan")
    return st.session_state.owner


def task_rows(task_pairs):
    """Convert scheduler task pairs into table-friendly dictionaries."""
    return [
        {
            "Time": task.time,
            "Pet": pet.name,
            "Task": task.title,
            "Duration": task.duration_minutes,
            "Priority": task.priority,
            "Frequency": task.frequency,
            "Due Date": task.due_date.isoformat(),
            "Status": "Done" if task.completed else "Open",
        }
        for pet, task in task_pairs
    ]


owner = get_owner()
scheduler = Scheduler(owner)

st.title("PawPal+")
st.caption("A smart pet care scheduler for daily routines and reminders.")

owner.name = st.sidebar.text_input("Owner name", value=owner.name)
view_mode = st.sidebar.radio("Schedule view", ["Time", "Priority"], horizontal=True)
pet_filter = st.sidebar.selectbox(
    "Filter by pet",
    ["All pets"] + [pet.name for pet in owner.pets],
)
status_filter = st.sidebar.selectbox("Filter by status", ["Open", "Done", "All"])

left, right = st.columns([1, 2])

with left:
    st.subheader("Pets")
    with st.form("add_pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "other"])
        age = st.number_input("Age", min_value=0, max_value=40, value=1)
        submitted_pet = st.form_submit_button("Add pet")

    if submitted_pet and pet_name.strip():
        owner.add_pet(Pet(pet_name.strip(), species, int(age)))
        st.success(f"Added {pet_name.strip()}.")
        st.rerun()

    if owner.pets:
        st.table(
            [
                {"Name": pet.name, "Species": pet.species, "Age": pet.age}
                for pet in owner.pets
            ]
        )
    else:
        st.info("Add a pet to start scheduling care tasks.")

with right:
    st.subheader("Schedule a Task")
    if not owner.pets:
        st.warning("Add at least one pet before scheduling tasks.")
    else:
        with st.form("add_task_form", clear_on_submit=True):
            selected_pet = st.selectbox("Pet", [pet.name for pet in owner.pets])
            title = st.text_input("Task title", value="Morning walk")
            time = st.time_input("Time")
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
            submitted_task = st.form_submit_button("Add task")

        if submitted_task and title.strip():
            pet = owner.find_pet(selected_pet)
            if pet is not None:
                pet.add_task(
                    Task(
                        title=title.strip(),
                        time=time.strftime("%H:%M"),
                        duration_minutes=int(duration),
                        priority=priority,
                        frequency=frequency,
                    )
                )
                st.success(f"Added {title.strip()} for {selected_pet}.")
                st.rerun()

st.divider()

completed_filter = None
if status_filter == "Open":
    completed_filter = False
elif status_filter == "Done":
    completed_filter = True

pet_name = None if pet_filter == "All pets" else pet_filter
filtered = scheduler.filter_tasks(pet_name=pet_name, completed=completed_filter)
display_tasks = (
    scheduler.sort_by_priority_then_time(filtered)
    if view_mode == "Priority"
    else scheduler.sort_by_time(filtered)
)

st.subheader("Care Schedule")
if display_tasks:
    st.table(task_rows(display_tasks))
else:
    st.info("No tasks match the current filters.")

conflicts = scheduler.detect_conflicts(scheduler.filter_tasks(completed=False))
if conflicts:
    for warning in conflicts:
        st.warning(warning)
else:
    st.success("No open task conflicts.")

if owner.pets:
    st.subheader("Complete a Task")
    open_tasks = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    task_options = [f"{pet.name} | {task.title}" for pet, task in open_tasks]
    if task_options:
        selected = st.selectbox("Open task", task_options)
        if st.button("Mark complete"):
            pet_name, task_title = selected.split(" | ", 1)
            scheduler.mark_task_complete(pet_name, task_title)
            st.success(f"Completed {task_title}.")
            st.rerun()
    else:
        st.info("All tasks are complete.")
