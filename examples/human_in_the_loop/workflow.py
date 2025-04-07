from llama_index.core.workflow import (
    HumanResponseEvent,
    InputRequiredEvent,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

from llama_viz import Viz


class ResultEvent(StopEvent):
    number: int


class SquaredWorkflow(Workflow):
    @step
    async def step1(self, ev: StartEvent) -> InputRequiredEvent:
        return InputRequiredEvent(prefix="Enter a number: ")

    @step
    async def step2(self, ev: HumanResponseEvent) -> ResultEvent:
        return ResultEvent(number=int(ev.response) ** 2)


if __name__ == "__main__":
    # Wrap the workflow in a Viz object.
    be = Viz(SquaredWorkflow(timeout=None))
    # Run the UI, the workflow will run in the background.
    be.run(debug=True)
