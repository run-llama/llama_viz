import asyncio
import datetime
import json
from typing import Any, Dict, List, Type

import dash_bootstrap_components as dbc
import diskcache
import pandas as pd
from dash import Dash, DiskcacheManager, Input, Output, State, html
from dash.dependencies import Component
from dash.exceptions import PreventUpdate
from llama_index.core import __version__ as llama_index_version
from llama_index.core.workflow import StopEvent, Workflow
from pydantic import BaseModel, HttpUrl

from .components import get_input_component, get_output_component
from .utils import get_external_stylesheets, get_workflow_inputs, get_workflow_outputs


class Viz:
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
        self._app = Dash(__name__, external_stylesheets=get_external_stylesheets(theme))
        self._theme = theme
        self._cache = diskcache.Cache("./cache")
        self._background_callback_manager = DiskcacheManager(self._cache)
        # Setup and introspect workflow
        self._workflow = workflow
        self._inputs: dict[str, type] = get_workflow_inputs(self._workflow)
        self._outputs: dict[str, type] = get_workflow_outputs(self._workflow)
        # Dash data
        self._input_components = []
        self._output_components = []
        self._state_components = []
        self._get_components()
        self._create_callback()
        # App layout
        self._app.layout = self._get_layout()

    def _get_components(self) -> None:
        """Set up dash components for inputs and outputs"""
        self._input_components = [
            Input(component_id="button-run", component_property="n_clicks")
        ]

        # Create input components
        self._input_widgets = []
        for name, _type in self._inputs.items():
            component, property_name = get_input_component(name, _type)
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
            component, property_name = get_output_component(name, _type)
            self._output_widgets.append(
                dbc.CardGroup([dbc.Label(f"Output: {name.capitalize()}"), component])
            )
            self._output_components.append(
                Output(component_id=f"output-{name}", component_property=property_name)
            )

    def _get_layout(self) -> Component:
        """Creates the default layout for the app"""
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
                # Events stream pane
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Events"),
                                dbc.Textarea(
                                    id="events-stream",
                                    placeholder="Events streamed will appear here...",
                                    style={"width": "100%", "minHeight": "200px"},
                                    className="mb-3",
                                    readOnly=True,
                                ),
                            ],
                            md=12,
                        ),
                    ]
                ),
                # Modal for human input
                dbc.Modal(
                    [
                        dbc.ModalHeader("Input Required"),
                        dbc.ModalBody(
                            [
                                html.P(
                                    id="modal-prompt", children="Please provide input:"
                                ),
                                dbc.Textarea(
                                    id="modal-input",
                                    placeholder="Your response...",
                                    style={"width": "100%", "minHeight": "100px"},
                                ),
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button("Submit", id="modal-submit", color="primary")
                        ),
                    ],
                    id="input-modal",
                    is_open=False,
                ),
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

    def _create_callback(self):
        """Create the main callback for the workflow"""

        @self._app.callback(
            output=self._output_components,
            inputs=self._input_components,
            state=self._state_components,
            background=True,
            manager=self._background_callback_manager,
            prevent_initial_call=True,
            progress=[Output(component_id="events-stream", component_property="value")],
        )
        def _run_workflow(set_progress, n_clicks, *args):
            if n_clicks is None:
                raise PreventUpdate

            # Parse input values
            run_params = {}
            for i, (input_name, input_type) in enumerate(self._inputs.items()):
                parsed_value = self._parse_input_value(args[i], input_type)
                if parsed_value is not None:  # Only add non-None values
                    run_params[input_name] = parsed_value

            # Run the workflow with event collection
            async def run_stream_events():
                events_log = []
                handler = self._workflow.run(**run_params)
                async for event in handler.stream_events():
                    if isinstance(event, StopEvent):
                        continue

                    events_log.append(json.dumps(event, default=str))
                    set_progress("\n".join(events_log))

                return await handler

            result = asyncio.run(run_stream_events())

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
