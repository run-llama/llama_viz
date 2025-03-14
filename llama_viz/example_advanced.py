"""
Advanced example showcasing the enhanced UI package with various input and output types.
"""

import datetime
from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step

from llama_viz import DashBackend


class AnalysisRequest(StartEvent):
    """Input event with various data types."""

    text: str
    number_of_points: int = 100
    date: datetime.date
    use_line_chart: bool = True
    categories: List[str] = []
    properties: Dict[str, str] = {}


class AnalysisResult(StopEvent):
    """Output event with various data types."""

    summary: str
    chart: go.Figure
    data_table: pd.DataFrame
    analysis_date: datetime.date
    processed_categories: List[str]

    def _get_result(self) -> Dict:
        """Return the complete result as a dictionary."""
        return {
            "summary": self.summary,
            "chart": self.chart,
            "data_table": self.data_table,
            "analysis_date": self.analysis_date,
            "processed_categories": self.processed_categories,
        }


class AdvancedWorkflow(Workflow):
    """A workflow that demonstrates various input and output types."""

    @step
    async def analyze_data(self, ctx: Context, ev: AnalysisRequest) -> AnalysisResult:
        """Process the input data and generate various output types."""
        # Create a simple dataframe
        df = pd.DataFrame(
            {
                "Category": ev.categories * 2,  # Repeat categories to get more data
                "Value": [i * 10 for i in range(len(ev.categories) * 2)],
                "Date": [
                    ev.date + datetime.timedelta(days=i)
                    for i in range(len(ev.categories) * 2)
                ],
            }
        )

        # Create a chart based on the dataframe
        fig = go.Figure()
        if ev.use_line_chart:
            fig.add_trace(
                go.Scatter(
                    x=df["Category"],
                    y=df["Value"],
                    mode="lines+markers",
                    name="Value by Category",
                )
            )
        else:
            fig.add_trace(
                go.Bar(x=df["Category"], y=df["Value"], name="Value by Category")
            )

        fig.update_layout(
            title=f"Analysis of {len(ev.categories)} categories",
            xaxis_title="Category",
            yaxis_title="Value",
            template="plotly_white",
        )

        # Process categories based on properties
        processed_categories = []
        for category in ev.categories:
            if category in ev.properties:
                processed_categories.append(f"{category}: {ev.properties[category]}")
            else:
                processed_categories.append(f"{category}: No property")

        # Create and return the result
        return AnalysisResult(
            summary=f"Analyzed {ev.text} with {ev.number_of_points} data points on {ev.date}",
            chart=fig,
            data_table=df,
            analysis_date=datetime.date.today(),
            processed_categories=processed_categories,
        )


async def main():
    """Run the workflow normally."""
    workflow = AdvancedWorkflow()
    result = await workflow.run(
        text="Sample analysis",
        number_of_points=50,
        date=datetime.date.today(),
        use_line_chart=True,
        categories=["Category A", "Category B", "Category C"],
        properties={"Category A": "Important", "Category C": "Critical"},
    )
    print(f"Analysis summary: {result.summary}")
    print(f"Processed categories: {result.processed_categories}")


if __name__ == "__main__":
    # Run the CLI version
    # asyncio.run(main())

    # Run the UI version with a custom theme
    # Available themes: bootstrap, cerulean, cosmo, cyborg, darkly, flatly, journal, litera,
    # lumen, lux, materia, minty, pulse, sandstone, simplex, sketchy, slate, solar,
    # spacelab, superhero, united, yeti
    backend = DashBackend(AdvancedWorkflow(), theme="darkly")
    backend.run(debug=True, port=8050)
