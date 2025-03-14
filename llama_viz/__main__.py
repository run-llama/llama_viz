from typing import Any

from openai import OpenAI
from pydantic import HttpUrl

from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from llama_index.core.workflow.ui.dash_backend import DashBackend


class QuestionAsked(StartEvent):
    query: str


class ImageDrawn(StopEvent):
    image: HttpUrl

    def _get_result(self) -> Any:
        return str(self.image)


class UIWorkflow(Workflow):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            start_event_class=QuestionAsked,
            stop_event_class=ImageDrawn,
            **kwargs,
        )

    @step
    async def chat(self, ctx: Context, ev: QuestionAsked) -> ImageDrawn | None:
        # llm_response = OpenAI(model="gpt-4o").complete(ev.query)
        client = OpenAI()
        response = client.images.generate(
            model="dall-e-3",
            prompt=ev.query,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        # Get the URL of the generated image
        image_url = response.data[0].url or ""

        # return StopEvent(result=llm_response.text)
        return ImageDrawn(image=image_url)


async def main():
    w = UIWorkflow()
    result = await w.run(query="draw a picture of a black labrador retriever")
    print(result)


if __name__ == "__main__":
    # Set up signal handling
    be = DashBackend(UIWorkflow())
    be.run(debug=True)
    # import asyncio

    # asyncio.run(main())
