import datetime
import json
from typing import Any, Dict, List, Type

import dash_bootstrap_components as dbc
import pandas as pd
from llama_index.core.workflow import StopEvent, Workflow
from pydantic import BaseModel
from pydantic.networks import HttpUrl

THEMES = {
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


class MissingType:
    """A stub used when a type depends on a package that's not installed."""


def get_workflow_inputs(workflow: Workflow) -> dict[str, type]:
    inputs = {}
    for name, info in workflow._start_event_class.model_fields.items():
        if info.annotation is Any:
            inputs[name] = str
        else:
            inputs[name] = info.annotation

    return inputs


def get_workflow_outputs(workflow: Workflow) -> dict[str, type]:
    if workflow._stop_event_class is StopEvent:
        return {"result": str}

    outputs = {}
    for name, info in workflow._stop_event_class.model_fields.items():
        if info.annotation is Any:
            outputs[name] = str
        else:
            outputs[name] = info.annotation

    return outputs


def get_external_stylesheets(theme_name: str) -> List[str | Dict[str, Any]]:
    stylesheet = THEMES.get(theme_name.lower())
    if stylesheet is None:
        raise ValueError(f"Unknown theme: {theme_name}")
    return [stylesheet]


def parse_input_value(value: Any, type_hint: Type) -> Any:
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


def format_output_value(value: Any, type_hint: Type) -> Any:
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

    if type_hint is str or type_hint is int or type_hint is float or type_hint is bool:
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
