from typing import Any

from llama_index.core.workflow import StopEvent, Workflow


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
