import asyncio
import json
import datetime

import dash
import dash_bootstrap_components as dbc
import diskcache
from dash import Dash, DiskcacheManager, Input, Output, State, html, set_props, dcc
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate
from llama_index.core import __version__ as llama_index_version
from llama_index.core.workflow import Context, StopEvent, Workflow
from llama_index.core.workflow.events import HumanResponseEvent, InputRequiredEvent

from .components import get_input_component, get_output_component
from .utils import (
    format_output_value,
    get_external_stylesheets,
    get_workflow_inputs,
    get_workflow_outputs,
    parse_input_value,
)


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
        self._ctx: Context | None = None
        # Dash data
        self._input_components = []
        self._output_components = []
        self._state_components = []
        self._get_components()
        self._create_callbacks()
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

        # Create output components - separating text and non-text outputs
        self._output_widgets = []
        self._text_output_ids = []  # Track text output IDs
        self._artifact_components = []  # For artifact view
        
        # Initialize output components - will be populated below
        self._output_components = []
        
        # First add input clearing outputs
        for name, _type in self._inputs.items():
            _, property_name = get_input_component(name, _type)
            self._output_components.append(
                Output(component_id=f"input-{name}", component_property=property_name)
            )
            
        # Now add output components
        for name, _type in self._outputs.items():
            component, property_name = get_output_component(name, _type)
            is_text_output = _type is str
            
            if is_text_output:
                # Track text output IDs for chat view
                self._text_output_ids.append(name)
            
            # All outputs go to the artifacts view
            self._artifact_components.append(
                dbc.Card(
                    dbc.CardBody([
                        html.H5(name.capitalize(), className="card-title"),
                        component
                    ]),
                    className="mb-3"
                )
            )
            
            # Add to output components for callback
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
                        # Left column: Chat view and Input
                        dbc.Col(
                            [
                                # Chat messages view
                                html.H3("Chat"),
                                dbc.Card(
                                    dbc.CardBody(
                                        id="chat-messages",
                                        children=[],
                                        style={
                                            "minHeight": "400px", 
                                            "maxHeight": "600px", 
                                            "overflowY": "auto",
                                            "padding": "15px"
                                        }
                                    ),
                                    className="mb-3",
                                ),
                                
                                # Input section
                                html.H3("Input"),
                                dbc.Form(self._input_widgets),
                                dbc.Button(
                                    "Run Workflow",
                                    id="button-run",
                                    color="primary",
                                    className="mt-3 mb-4",
                                ),
                            ],
                            md=6,
                        ),
                        
                        # Right column: Artifacts view
                        dbc.Col(
                            [
                                html.H3("Artifacts"),
                                # Non-text outputs as cards
                                *self._artifact_components,
                                
                                # Events stream
                                html.H4("Events", className="mt-3"),
                                dbc.Card([
                                    # Events summary bar
                                    dbc.CardHeader(
                                        html.Div([
                                            html.Span("Event Stream", className="h6"),
                                            html.Div([
                                                html.Span(
                                                    id="events-counter", 
                                                    children="0 events",
                                                    className="badge bg-secondary me-2"
                                                ),
                                                dbc.Button(
                                                    "Clear",
                                                    id="clear-events",
                                                    color="light",
                                                    size="sm",
                                                    className="py-0 px-2"
                                                )
                                            ], className="d-flex align-items-center")
                                        ]),
                                        className="d-flex justify-content-between align-items-center"
                                    ),
                                    dbc.CardBody(
                                        html.Div(
                                            id="events-stream-container",
                                            children=[],
                                            style={
                                                "maxHeight": "400px",
                                                "overflowY": "auto",
                                                "padding": "5px"
                                            }
                                        )
                                    )],
                                    className="mb-3",
                                ),
                            ],
                            md=6,
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
                # Storage for events data
                dcc.Store(id='events-data', data={'events': [], 'count': 0}),
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
                # Hidden div for storing busy state
                html.Div(id="busy-output", style={"display": "none"}),
            ],
            fluid=True,
            className="p-5",
        )

    def _create_callbacks(self):
        """Create the main callback for the workflow"""

        # Add callback for collapsible json sections
        @self._app.callback(
            Output({'type': 'collapse-content', 'index': dash.dependencies.MATCH}, 'style'),
            [Input({'type': 'collapse-button', 'index': dash.dependencies.MATCH}, 'n_clicks')],
            [State({'type': 'collapse-content', 'index': dash.dependencies.MATCH}, 'style')],
        )
        def toggle_collapse(n_clicks, current_style):
            if n_clicks is None:
                return current_style
                
            if n_clicks % 2 == 1:
                # Hide content
                return {'display': 'none'}
            else:
                # Show content
                return {'display': 'block'}

        # Callback to clear events
        @self._app.callback(
            [
                Output("events-data", "data"),
            ],
            Input("clear-events", "n_clicks"),
            prevent_initial_call=True
        )
        def clear_events(n_clicks):
            if n_clicks:
                return [{'events': [], 'count': 0}]
            raise PreventUpdate
            
        # Callback to update UI from events-data store
        @self._app.callback(
            [
                Output("events-stream-container", "children"),
                Output("events-counter", "children")
            ],
            Input("events-data", "data"),
            prevent_initial_call=True
        )
        def update_events_ui(data):
            events = data.get('events', [])
            count = data.get('count', 0)
            return events, f"{count} event{'s' if count != 1 else ''}"

        @self._app.callback(
            output=self._output_components
            + [Output("input-modal", component_property="is_open")]
            + [Output("chat-messages", component_property="children", allow_duplicate=True)]
            + [Output("events-data", "data", allow_duplicate=True)],
            inputs=self._input_components
            + [Input("modal-submit", component_property="n_clicks")],
            state=self._state_components 
            + [State("modal-input", "value")]
            + [State("chat-messages", "children")]
            + [State("events-data", "data")],
            background=True,
            manager=self._background_callback_manager,
            prevent_initial_call=True,
            progress=[Output("busy-output", component_property="children")],
            running=[
                (Output("button-run", "disabled"), True, False),
            ],
        )
        def _run_workflow(set_progress, run_clicks, modal_clicks, *args):
            ctx = dash.callback_context
            triggered_id = (
                ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
            )

            if not triggered_id:
                raise PreventUpdate

            # Split args into input values, modal input, chat messages, and events data
            input_values = args[:len(self._inputs)]
            modal_input_value = args[len(self._inputs)] if len(args) > len(self._inputs) else ""
            chat_messages = args[-2] if len(args) > 1 and isinstance(args[-2], list) else []
            events_data = args[-1] if len(args) > 0 else {'events': [], 'count': 0}
                
            if triggered_id == "button-run":
                self._ctx = None
                
                # Clear events data when starting a new run
                events_data = {'events': [], 'count': 0}
                
                # Add user query to chat - use the input value based on the workflow
                query_data = {}
                for i, (input_name, input_type) in enumerate(self._inputs.items()):
                    if i < len(input_values) and input_values[i]:
                        parsed_value = parse_input_value(input_values[i], input_type)
                        if parsed_value is not None:
                            query_data[input_name] = parsed_value
                
                # Only add to chat if there's actual input data
                if query_data:
                    # Format user message based on number of inputs
                    if len(query_data) == 1:
                        # Single input - show simple message
                        input_name = list(query_data.keys())[0]
                        query_text = str(query_data[input_name])
                        chat_content = query_text
                    else:
                        # Multiple inputs - show formatted JSON
                        query_text = json.dumps(query_data, indent=2)
                        chat_content = [
                            html.Small("Input parameters:"),
                            html.Pre(query_text, style={"marginBottom": 0})
                        ]
                        
                    # Add user message to chat
                    chat_messages.append(
                        dbc.Card(
                            dbc.CardBody(chat_content),
                            className="mb-2 border-primary",
                            style={
                                "backgroundColor": "#f8f9fa", 
                                "marginLeft": "auto", 
                                "marginRight": "0", 
                                "maxWidth": "80%",
                                "borderRadius": "15px 15px 0 15px"
                            }
                        )
                    )
                    
            elif triggered_id == "modal-submit":
                # Add user response to chat
                if modal_input_value:
                    chat_messages.append(
                        dbc.Card(
                            dbc.CardBody(modal_input_value),
                            className="mb-2 border-primary",
                            style={
                                "backgroundColor": "#f8f9fa", 
                                "marginLeft": "auto", 
                                "marginRight": "0", 
                                "maxWidth": "80%",
                                "borderRadius": "15px 15px 0 15px"
                            }
                        )
                    )

            # Parse input values for running the workflow
            run_params = {}
            for i, (input_name, input_type) in enumerate(self._inputs.items()):
                if i < len(input_values):
                    parsed_value = parse_input_value(input_values[i], input_type)
                    if parsed_value is not None:  # Only add non-None values
                        run_params[input_name] = parsed_value

            # Run the workflow with event collection
            async def run_stream_events():
                events_list = events_data.get('events', [])
                event_count = events_data.get('count', 0)
                
                if self._ctx:
                    run_params["ctx"] = self._ctx
                handler = self._workflow.run(**run_params)
                if modal_input_value:
                    assert handler._ctx
                    handler._ctx.send_event(
                        HumanResponseEvent(response=modal_input_value)
                    )
                self._ctx = handler.ctx
                
                # Create a simple event card for each event
                async for event in handler.stream_events():
                    if isinstance(event, StopEvent):
                        continue
                    if isinstance(event, InputRequiredEvent):
                        return None

                    # Create a simple text description of the event
                    event_count += 1
                    event_type = event.__class__.__name__
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    
                    # TODO: Choose background color based on event type?
                    bg_color, icon = "#f5f5f5", "🔄"  # Light gray for other events
                    
                    # Get event data as a JSON string
                    try:
                        # Extract event data using appropriate method
                        event_data = event.model_dump()
                            
                        # Convert to a pretty JSON string
                        try:
                            event_json = json.dumps(event_data, indent=2, default=str)
                        except:
                            event_json = str(event_data)
                    except Exception as e:
                        # Fallback to simple string representation
                        event_json = f"Error serializing event: {str(e)}\nEvent: {str(event)}"
                    
                    # Create a simple card to display the event
                    card = html.Div([
                        dbc.Card(
                            dbc.CardBody([
                                html.Div([
                                    html.Span(f"{icon} {event_type}", style={"fontWeight": "bold"}),
                                    html.Small(f"  {timestamp}", className="text-muted")
                                ]),
                                html.Pre(
                                    event_json,
                                    style={
                                        "marginTop": "10px",
                                        "padding": "10px",
                                        "backgroundColor": "rgba(0,0,0,0.04)",
                                        "borderRadius": "4px", 
                                        "fontSize": "0.85rem",
                                        "whiteSpace": "pre-wrap",
                                        "overflow": "auto"
                                    }
                                )
                            ]),
                            className="mb-2",
                            style={"backgroundColor": bg_color}
                        )
                    ])
                    
                    # Add card to events list (must be serializable HTML components)
                    events_list.append(card)
                    
                    # Create updated events data
                    updated_events_data = {'events': events_list, 'count': event_count}
                    
                    # Update the events data store
                    set_props("events-data", {"data": updated_events_data})

                return await handler

            result = asyncio.run(run_stream_events())

            output_values = []
            # First, add empty values for input clearing
            for _ in range(len(self._inputs)):
                output_values.append(None)

            # Create workflow response card for chat (if there is result data)
            workflow_responses = []
            has_response = False
            
            # Then handle the formatted output values
            if result is not None:
                # Handle various result types based on workflow structure
                if len(self._outputs) == 1 and "result" in self._outputs:
                    # Simple workflow with just a "result" output
                    output_val = format_output_value(result, self._outputs["result"])
                    output_values.append(output_val)
                    
                    # Add to workflow responses for chat
                    if result:
                        has_response = True
                        if self._outputs["result"] is str:
                            workflow_responses.append(output_val)
                        elif isinstance(result, (dict, list)):
                            workflow_responses.append(html.Pre(json.dumps(result, indent=2, default=str)))
                        else:
                            workflow_responses.append(str(result))
                else:
                    # Complex workflow with multiple outputs
                    for output_name, output_type in self._outputs.items():
                        # Extract output value
                        if hasattr(result, output_name):
                            output_value = getattr(result, output_name)
                        elif isinstance(result, dict) and output_name in result:
                            output_value = result[output_name]
                        else:
                            output_value = None
                            
                        # Format and add to output components
                        formatted_output = format_output_value(output_value, output_type)
                        output_values.append(formatted_output)
                        
                        # Add to workflow responses if there's content
                        if output_value is not None:
                            has_response = True
                            
                            # Format display based on output type
                            if output_name in self._text_output_ids and output_type is str:
                                # Text output goes directly to chat with label
                                workflow_responses.append(
                                    html.Div([
                                        html.Strong(f"{output_name.capitalize()}: ") if len(self._outputs) > 1 else "",
                                        formatted_output
                                    ])
                                )
                            elif isinstance(output_value, (dict, list)):
                                # Format complex data as JSON
                                workflow_responses.append(
                                    html.Div([
                                        html.Strong(f"{output_name.capitalize()}: "),
                                        html.Pre(formatted_output if isinstance(formatted_output, str) else json.dumps(output_value, indent=2, default=str))
                                    ])
                                )
                            else:
                                # Other outputs with simple formatting
                                workflow_responses.append(
                                    html.Div([
                                        html.Strong(f"{output_name.capitalize()}: "),
                                        str(output_value)
                                    ])
                                )
            
            # Add the workflow response to chat if there's content
            if has_response:
                chat_messages.append(
                    dbc.Card(
                        dbc.CardBody(workflow_responses),
                        className="mb-2 text-white",
                        style={
                            "backgroundColor": "#007bff", 
                            "marginRight": "auto", 
                            "marginLeft": "0", 
                            "maxWidth": "80%",
                            "borderRadius": "15px 15px 15px 0"
                        }
                    )
                )

            # Add modal state to outputs
            if result is None:
                # Workflow didn't finish, show the modal
                output_values.append(True)
            else:
                output_values.append(False)
            
            # Add updated chat messages to output
            output_values.append(chat_messages)
            
            # Add events data to output
            output_values.append(events_data)

            return output_values

    def run(self, *args, **kwargs):
        """Run the Dash app"""
        self._app.run(*args, **kwargs)
