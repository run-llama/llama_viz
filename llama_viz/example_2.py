from typing import Any

from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from openai import OpenAI
from pydantic import HttpUrl


class QuestionAsked(StartEvent):
    query: str


class ImageDrawn(StopEvent):
    image: HttpUrl

    def _get_result(self) -> Any:
        return str(self.image)


class UIWorkflow(Workflow):
    @step
    async def chat(self, ctx: Context, ev: QuestionAsked) -> ImageDrawn | None:
        client = OpenAI()
        response = client.images.generate(
            model="dall-e-3",
            prompt=ev.query,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        # Get the URL of the generated image
        return ImageDrawn(image=response.data[0].url)  # type: ignore


async def main():
    w = UIWorkflow()
    result = await w.run(query="draw a picture of a black labrador retriever")
    print(result)


if __name__ == "__main__":
    # import asyncio

    # asyncio.run(main())

    from llama_viz import DashBackend

    be = DashBackend(UIWorkflow())
    be.run(debug=True)
