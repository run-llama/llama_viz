# LlamaViz

Turn your LlamaIndex Workflows into beautiful UIs!

![Screenshot of a UI built with LlamaViz.](./img/screenshot.png)

## Installation

Just `pip install llama-viz` and you are in business.

## Quick start

To build a UI over an existing workflow is a two step process:

1. Wrap your workflow in a `Viz` instance.
2. Call the `Viz.run()` method to start the UI.

> [!TIP]
> Using [custom Start and Stop events](https://docs.llamaindex.ai/en/stable/module_guides/workflow/#customizing-entry-and-exit-points)
> in your workflow will let you take full control over the generated UI.

Example code:

```py
# Put this code in a script, for example 'image_workflow.py'
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
```

To build and run the UI, from a terminal:
```sh
$ python image_workflow
```

If there are no errors, point your browser to `http://127.0.0.1:8050/`.
