from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from openai import OpenAI
from pydantic import HttpUrl

from llama_viz import Viz


class QueryEvent(StartEvent):
    """The `query` parameter will be shown as an input text box in the UI."""

    query: str


class ImageDrawn(StopEvent):
    """The `image` parameter will be shown as an image coming from an url in the UI."""

    image: HttpUrl


class ImageDrawWorkflow(Workflow):
    @step
    async def chat(self, ctx: Context, ev: QueryEvent) -> ImageDrawn | None:
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
        return ImageDrawn(image=HttpUrl(image_url))


if __name__ == "__main__":
    # Wrap the workflow in a Viz object.
    be = Viz(ImageDrawWorkflow())
    # Run the UI, the workflow will run in the background.
    be.run(debug=True)
