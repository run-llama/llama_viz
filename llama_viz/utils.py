from typing import Any, Dict, List

import dash_bootstrap_components as dbc
from llama_index.core.workflow import StopEvent, Workflow

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
