"""
Simple example showing the enhanced UI package.
"""

import datetime
from typing import List

from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step

from llama_viz import DashBackend


class SimpleInput(StartEvent):
    """Input event with simple data types."""

    name: str
    age: int = 25
    birthdate: datetime.date
    is_student: bool = False
    hobbies: List[str] = ["reading", "coding"]


class SimpleOutput(StopEvent):
    """Output event with simple data types."""

    greeting: str
    years_old: int
    days_alive: int
    hobby_count: int
    student_status: str

    def _get_result(self) -> str:
        """Return the complete result as a string."""
        return (
            f"Hello {self.greeting}! You are {self.years_old} years old, "
            f"have been alive for {self.days_alive} days, "
            f"have {self.hobby_count} hobbies, "
            f"and your student status is: {self.student_status}."
        )


class SimpleWorkflow(Workflow):
    """A simple workflow demonstrating basic input and output types."""

    @step
    async def process_input(self, ctx: Context, ev: SimpleInput) -> SimpleOutput:
        """Process the simple input data."""
        # Calculate days alive
        today = datetime.date.today()
        days_alive = (today - ev.birthdate).days

        # Determine student status
        student_status = (
            "Currently a student" if ev.is_student else "Not currently a student"
        )

        # Create and return the result
        return SimpleOutput(
            greeting=f"{ev.name}",
            years_old=ev.age,
            days_alive=days_alive,
            hobby_count=len(ev.hobbies),
            student_status=student_status,
        )


if __name__ == "__main__":
    # Create the UI backend with a custom theme
    backend = DashBackend(SimpleWorkflow(), theme="flatly")
    backend.run(debug=True, port=8050)
