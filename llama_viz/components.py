import datetime
from typing import Dict, List, Type

import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import dash_table, dcc, html
from dash.development.base_component import Component
from pydantic import BaseModel, HttpUrl

from .utils import MissingType

try:
    import pandas as pd

    dataframe_type = pd.DataFrame
except ImportError:
    dataframe_type = MissingType


def get_output_component(name: str, type_hint: Type) -> tuple[Component, str]:
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
            dbc.Input(id=f"output-{name}", type="number", className="mb-2"),
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
                    "maxHeight": "300px",
                    "marginTop": "10px",
                    "objectFit": "contain",
                    "display": "block",
                    "marginLeft": "auto",
                    "marginRight": "auto",
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
    elif type_hint is dataframe_type:
        return (
            dash_table.DataTable(
                id=f"output-{name}",
                page_size=10,
                style_table={"overflowX": "auto"},
                style_cell={
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'maxWidth': 0,
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
            ),
            "data",
        )
    elif (
        type_hint.__name__ == "Figure"
        or hasattr(type_hint, "__name__")
        and "Figure" in type_hint.__name__
    ):
        return (
            dcc.Graph(
                id=f"output-{name}", 
                figure=go.Figure(), 
                className="mb-2",
                style={"height": "400px"},
            ),
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


def get_input_component(name: str, type_hint: Type) -> tuple[Component, str]:
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
                date=datetime.datetime.today(),
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
