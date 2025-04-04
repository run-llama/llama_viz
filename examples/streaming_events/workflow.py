from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

from llama_viz import Viz


class QueryEvent(StartEvent):
    """The `query` parameter will be shown as an input text box in the UI."""

    query: str


class InfoMessage(Event):
    msg: str


class ErrorMessagge(InfoMessage):
    pass


class StreamingWorkflow(Workflow):
    @step
    async def stream(self, ctx: Context, ev: QueryEvent) -> StopEvent | None:
        for msg in ("Hello, world", "I am an info message"):
            ctx.write_event_to_stream(InfoMessage(msg=msg))

        ctx.write_event_to_stream(ErrorMessagge(msg="There was an error"))
        return StopEvent(result="Finish")


if __name__ == "__main__":
    # Wrap the workflow in a Viz object.
    be = Viz(StreamingWorkflow())
    # Run the UI, the workflow will run in the background.
    be.run(debug=True)
