from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from llama_index.llms.openai import OpenAI
from openai import OpenAI


class QuestionAsked(StartEvent):
    query: str


class CompletionWorkflow(Workflow):
    @step
    async def chat(self, ctx: Context, ev: QuestionAsked) -> StopEvent | None:
        llm_response = OpenAI(model="gpt-4o").complete(ev.query)

        return StopEvent(result=llm_response.text)


async def main():
    w = CompletionWorkflow()
    result = await w.run(query="Who founded OpenAI?")
    print(result)


if __name__ == "__main__":
    # import asyncio

    # asyncio.run(main())

    from llama_viz import DashBackend

    be = DashBackend(CompletionWorkflow())
    be.run(debug=True)
