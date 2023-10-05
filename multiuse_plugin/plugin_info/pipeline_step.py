# General imports
from typing import Callable, Optional, Tuple, Type, Union

# Relative imports
from .plugin_info import PluginInfo

"""
This module provides the function-type of a pipeline-step, a decorator for naming it and other utility functions.
"""


PipelineStep = Callable[[PluginInfo], Union[bool, Tuple[bool, str]]]  # type-alias

def name_pipeline_step(name: str) -> Callable[[PipelineStep], PipelineStep]:
    """
    Decorator which sets a custom name for the pipeline-step function.
    """
    def named_step(step: PipelineStep):
        step.pipeline_step_name = name
        return step
    
    return named_step

def name_lambda_pipeline_step(step: PipelineStep, name: str):
    step.pipeline_step_name = name 
    return step 

def get_pipeline_step_name(step: PipelineStep) -> str:
    if hasattr(step, "pipeline_step_name"):
        name: str = step.pipeline_step_name
    else:
        name: str = step.__name__
    return name
