import asyncio
import datetime
import json
from typing import Any, Dict, List, Type

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, Input, Output, State, dash_table, dcc, html
from dash.dependencies import Component
from dash.exceptions import PreventUpdate
from llama_index.core.workflow import Workflow
from pydantic import BaseModel, HttpUrl

from .utils import get_workflow_inputs, get_workflow_outputs


class DashBackend:
    def __init__(self, workflow: Workflow, theme: str = "bootstrap") -> None:
        """
        Initialize the Dash backend for the workflow.

        Args:
            workflow: The workflow to visualize
            theme: The dash-bootstrap-components theme to use. Options include:
                  bootstrap, cerulean, cosmo, cyborg, darkly, flatly, journal, litera,
                  lumen, lux, materia, minty, pulse, sandstone, simplex, sketchy,
                  slate, solar, spacelab, superhero, united, yeti
        """
        theme_map = {
            "bootstrap": dbc.themes.BOOTSTRAP,
            "cerulean": dbc.themes.CERULEAN,
            "cosmo": dbc.themes.COSMO,
            "cyborg": dbc.themes.CYBORG,
            "darkly": dbc.themes.DARKLY,
            "flatly": dbc.themes.FLATLY,
            "journal": dbc.themes.JOURNAL,
            "litera": dbc.themes.LITERA,
            "lumen": dbc.themes.LUMEN,
            "lux": dbc.themes.LUX,
            "materia": dbc.themes.MATERIA,
            "minty": dbc.themes.MINTY,
            "pulse": dbc.themes.PULSE,
            "sandstone": dbc.themes.SANDSTONE,
            "simplex": dbc.themes.SIMPLEX,
            "sketchy": dbc.themes.SKETCHY,
            "slate": dbc.themes.SLATE,
            "solar": dbc.themes.SOLAR,
            "spacelab": dbc.themes.SPACELAB,
            "superhero": dbc.themes.SUPERHERO,
            "united": dbc.themes.UNITED,
            "yeti": dbc.themes.YETI,
        }

        external_stylesheets = [theme_map.get(theme.lower(), dbc.themes.BOOTSTRAP)]

        self._app = Dash(__name__, external_stylesheets=external_stylesheets)
        self._workflow = workflow
        self._theme = theme

        self._inputs: dict[str, type] = get_workflow_inputs(self._workflow)
        self._outputs: dict[str, type] = get_workflow_outputs(self._workflow)

        self._input_components = []
        self._output_components = []
        self._state_components = []
        self._get_components()

        self._app.layout = self._get_layout()
        self._create_callback()

    def _get_input_component(self, name: str, type_hint: Type) -> tuple[Component, str]:
        """
        Get the appropriate input component for the given type hint.

        Returns:
            A tuple of (component, property_name)
        """
        if type_hint is str:
            return (
                dbc.Input(
                    id=f"input-{name}",
                    type="text",
                    placeholder=f"Enter {name}...",
                    className="mb-2",
                ),
                "value",
            )
        elif type_hint is int:
            return (
                dbc.Input(
                    id=f"input-{name}",
                    type="number",
                    step=1,
                    placeholder=f"Enter {name} (number)...",
                    className="mb-2",
                ),
                "value",
            )
        elif type_hint is float:
            return (
                dbc.Input(
                    id=f"input-{name}",
                    type="number",
                    step=0.1,
                    placeholder=f"Enter {name} (decimal)...",
                    className="mb-2",
                ),
                "value",
            )
        elif type_hint is bool:
            return (
                dbc.Checkbox(id=f"input-{name}", label=name, className="mb-2"),
                "value",
            )
        elif type_hint is datetime.date:
            return (
                dcc.DatePickerSingle(
                    id=f"input-{name}",
                    date=datetime.date.today(),
                    display_format="YYYY-MM-DD",
                    className="mb-2",
                ),
                "date",
            )
        elif (
            type_hint is list
            or type_hint is List
            or hasattr(type_hint, "__origin__")
            and type_hint.__origin__ is list
        ):
            return (
                dbc.Textarea(
                    id=f"input-{name}",
                    placeholder=f"Enter {name} as JSON list...",
                    className="mb-2",
                    rows=3,
                ),
                "value",
            )
        elif (
            type_hint is dict
            or type_hint is Dict
            or hasattr(type_hint, "__origin__")
            and type_hint.__origin__ is dict
        ):
            return (
                dbc.Textarea(
                    id=f"input-{name}",
                    placeholder=f"Enter {name} as JSON object...",
                    className="mb-2",
                    rows=4,
                ),
                "value",
            )
        elif issubclass(type_hint, BaseModel):
            return (
                dbc.Textarea(
                    id=f"input-{name}",
                    placeholder=f"Enter {name} as JSON object...",
                    className="mb-2",
                    rows=4,
                ),
                "value",
            )
        else:
            # Default to text input for unknown types
            return (
                dbc.Input(
                    id=f"input-{name}",
                    type="text",
                    placeholder=f"Enter {name}...",
                    className="mb-2",
                ),
                "value",
            )

    def _get_output_component(
        self, name: str, type_hint: Type
    ) -> tuple[Component, str]:
        """
        Get the appropriate output component for the given type hint.

        Returns:
            A tuple of (component, property_name)
        """
        if type_hint is str:
            return (
                dbc.Textarea(
                    id=f"output-{name}",
                    placeholder="Output will appear here...",
                    style={"width": "100%", "minHeight": "100px"},
                    className="mb-2",
                    readOnly=True,
                ),
                "value",
            )
        elif type_hint is int or type_hint is float:
            return (
                dbc.Input(id=f"output-{name}", type="text", className="mb-2"),
                "value",
            )
        elif type_hint is bool:
            return (
                dbc.Input(id=f"output-{name}", type="text", className="mb-2"),
                "value",
            )
        elif type_hint is HttpUrl or type_hint.__name__ == "HttpUrl":
            return (
                html.Img(
                    id=f"output-{name}",
                    style={
                        "maxWidth": "100%",
                        "maxHeight": "500px",
                        "marginTop": "10px",
                    },
                    className="mb-2",
                ),
                "src",
            )
        elif (
            type_hint is list
            or type_hint is List
            or hasattr(type_hint, "__origin__")
            and type_hint.__origin__ is list
        ):
            return (
                dbc.Textarea(
                    id=f"output-{name}",
                    placeholder="Output will appear here...",
                    style={"width": "100%", "minHeight": "100px"},
                    className="mb-2",
                    readOnly=True,
                ),
                "value",
            )
        elif (
            type_hint is dict
            or type_hint is Dict
            or hasattr(type_hint, "__origin__")
            and type_hint.__origin__ is dict
        ):
            return (
                dbc.Textarea(
                    id=f"output-{name}",
                    placeholder="Output will appear here...",
                    style={"width": "100%", "minHeight": "100px"},
                    className="mb-2",
                    readOnly=True,
                ),
                "value",
            )
        elif type_hint is pd.DataFrame:
            return (
                dash_table.DataTable(
                    id=f"output-{name}",
                    page_size=10,
                    style_table={"overflowX": "auto"},
                ),
                "data",
            )
        elif (
            type_hint.__name__ == "Figure"
            or hasattr(type_hint, "__name__")
            and "Figure" in type_hint.__name__
        ):
            return (
                dcc.Graph(id=f"output-{name}", figure=go.Figure(), className="mb-2"),
                "figure",
            )
        else:
            # Default to JSON output for complex types
            return (
                dbc.Textarea(
                    id=f"output-{name}",
                    placeholder="Output will appear here...",
                    style={"width": "100%", "minHeight": "100px"},
                    className="mb-2",
                    readOnly=True,
                ),
                "value",
            )

    def _get_components(self) -> None:
        """Set up dash components for inputs and outputs"""
        self._input_components = [
            Input(component_id="button-run", component_property="n_clicks")
        ]

        # Create input components
        self._input_widgets = []
        for name, _type in self._inputs.items():
            component, property_name = self._get_input_component(name, _type)
            self._input_widgets.append(
                dbc.CardGroup([dbc.Label(name.capitalize()), component])
            )
            self._state_components.append(
                State(component_id=f"input-{name}", component_property=property_name)
            )
            # Clear inputs after submission
            self._output_components.append(
                Output(component_id=f"input-{name}", component_property=property_name)
            )

        # Create output components
        self._output_widgets = []
        for name, _type in self._outputs.items():
            component, property_name = self._get_output_component(name, _type)
            self._output_widgets.append(
                dbc.CardGroup([dbc.Label(f"Output: {name.capitalize()}"), component])
            )
            self._output_components.append(
                Output(component_id=f"output-{name}", component_property=property_name)
            )

    def _get_layout(self) -> Component:
        """Creates the default layout for the app"""
        # Get LlamaIndex version
        try:
            from llama_index.core import __version__ as llama_index_version
        except ImportError:
            llama_index_version = "unknown"

        return dbc.Container(
            [
                # Header with title and theme info
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1(
                                    f"{self._workflow.__class__.__name__}",
                                    className="mt-4 mb-2",
                                ),
                                html.P(
                                    f"Running with theme: {self._theme}",
                                    className="text-muted",
                                ),
                            ],
                            md=12,
                        ),
                    ]
                ),
                # Main content
                dbc.Row(
                    [
                        # Input column
                        dbc.Col(
                            [
                                html.H3("Inputs"),
                                dbc.Form(self._input_widgets),
                                dbc.Button(
                                    "Run Workflow",
                                    id="button-run",
                                    color="primary",
                                    className="mt-3 mb-4",
                                ),
                            ],
                            md=5,
                        ),
                        # Output column
                        dbc.Col([html.H3("Outputs"), *self._output_widgets], md=7),
                    ]
                ),
                # Loading spinner
                dbc.Spinner(html.Div(id="loading-output"), color="primary"),
                # Footer
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.P(
                                    [
                                        "Built with ",
                                        html.A(
                                            "LlamaIndex",
                                            href="https://www.llamaindex.ai/",
                                            target="_blank",
                                        ),
                                        f" (v{llama_index_version})",
                                        " | Workflow UI package",
                                    ],
                                    className="text-center text-muted",
                                )
                            ]
                        )
                    ]
                ),
            ],
            fluid=True,
            className="p-5",
        )

    def _parse_input_value(self, value: Any, type_hint: Type) -> Any:
        """
        Parse the input value based on the expected type.

        Args:
            value: The raw input value from the dash component
            type_hint: The expected type

        Returns:
            The parsed value
        """
        if value is None or value == "":
            if type_hint is bool:
                return False
            return None

        if type_hint is str:
            return str(value)
        elif type_hint is int:
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0
        elif type_hint is float:
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        elif type_hint is bool:
            return bool(value)
        elif type_hint is datetime.date:
            if isinstance(value, str):
                try:
                    return datetime.datetime.strptime(value, "%Y-%m-%d").date()
                except ValueError:
                    return datetime.date.today()
            return value
        elif (
            type_hint is list
            or type_hint is List
            or hasattr(type_hint, "__origin__")
            and type_hint.__origin__ is list
        ):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        elif (
            type_hint is dict
            or type_hint is Dict
            or hasattr(type_hint, "__origin__")
            and type_hint.__origin__ is dict
        ):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {}
        elif issubclass(type_hint, BaseModel):
            try:
                return type_hint.parse_raw(value)
            except Exception:
                return None
        else:
            # For unknown types, return as is
            return value

    def _format_output_value(self, value: Any, type_hint: Type) -> Any:
        """
        Format the output value based on the component type.

        Args:
            value: The raw output value from the workflow
            type_hint: The expected type

        Returns:
            The formatted value appropriate for the dash component
        """
        if value is None:
            return "" if type_hint is str else None

        if (
            type_hint is str
            or type_hint is int
            or type_hint is float
            or type_hint is bool
        ):
            return str(value)
        elif type_hint is HttpUrl or type_hint.__name__ == "HttpUrl":
            return str(value)
        elif type_hint is pd.DataFrame:
            if isinstance(value, pd.DataFrame):
                return value.to_dict("records")
            return []
        elif (
            type_hint.__name__ == "Figure"
            or hasattr(type_hint, "__name__")
            and "Figure" in type_hint.__name__
        ):
            return value
        elif isinstance(value, (dict, list)) or type_hint is dict or type_hint is list:
            try:
                return json.dumps(value, indent=2, default=str)
            except Exception:
                return str(value)
        else:
            # For complex objects, try JSON serialization
            try:
                if hasattr(value, "json"):
                    return value.json(indent=2)
                elif hasattr(value, "model_dump_json"):
                    return value.model_dump_json(indent=2)
                else:
                    return json.dumps(value, indent=2, default=str)
            except Exception:
                return str(value)

    async def _run_workflow_async(self, input_data: dict[str, Any]) -> Any:
        """Run the workflow with the provided input data"""
        result = await self._workflow.run(**input_data)
        return result

    def _create_callback(self):
        """Create the main callback for the workflow"""

        @self._app.callback(
            output=self._output_components,
            inputs=self._input_components,
            state=self._state_components,
        )
        def _run_workflow(n_clicks, *args):
            if n_clicks is None:
                raise PreventUpdate

            # Parse input values
            run_params = {}
            for i, (input_name, input_type) in enumerate(self._inputs.items()):
                parsed_value = self._parse_input_value(args[i], input_type)
                if parsed_value is not None:  # Only add non-None values
                    run_params[input_name] = parsed_value

            # Run the workflow
            result = asyncio.run(self._run_workflow_async(run_params))

            # Format output values
            output_values = []

            # First, add empty values for input clearing
            for _ in range(len(self._inputs)):
                output_values.append(None)

            # Then add the formatted output values
            if len(self._outputs) == 1 and "result" in self._outputs:
                # Special case for simple workflows with just a "result" output
                output_values.append(
                    self._format_output_value(result, self._outputs["result"])
                )
            else:
                # For more complex workflows with multiple outputs
                for output_name, output_type in self._outputs.items():
                    if hasattr(result, output_name):
                        output_value = getattr(result, output_name)
                    elif isinstance(result, dict) and output_name in result:
                        output_value = result[output_name]
                    else:
                        output_value = result  # Use the whole result if we can't find a specific attribute

                    output_values.append(
                        self._format_output_value(output_value, output_type)
                    )

            return output_values

    def run(self, *args, **kwargs):
        """Run the Dash app"""
        self._app.run(*args, **kwargs)
