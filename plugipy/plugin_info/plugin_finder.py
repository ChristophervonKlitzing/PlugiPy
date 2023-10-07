# General imports
from typing import Iterable, Optional, Sequence, Tuple, Union, TypeVar, Generic
import os 

# Relative imports
from .plugin_info import PluginInfo
from .pipeline_step import PipelineStep, get_pipeline_step_name


def _chained(sequences: Sequence[Sequence[PipelineStep]]):
    for seq in sequences:
        yield from seq

T = TypeVar('T')
class PluginFinder(Generic[T]):
    def __init__(self, search_path: str, /, *, pipeline_steps: Sequence[PipelineStep] = []) -> None:
        if not os.path.isdir(search_path):
                raise ValueError(f"The given search path \"{search_path}\" is not a valid directory path")
        
        self._search_path = os.path.abspath(search_path)  # store as an absolute path
        self._pipeline_steps = [step for step in pipeline_steps]  # store as list of steps to ensure mutability inside class
        self._error_string = ""
    
    @property
    def error_string(self) -> str:
        return self._error_string

    def add_to_pipeline(self, step: PipelineStep) -> None:
        self._pipeline_steps.append(step)
    
    def find_all(self, extra_steps: Sequence[PipelineStep] = []) -> Iterable[PluginInfo]:
        plugin_names = os.listdir(self._search_path)
        
        for plugin_name in plugin_names:
            if plugin_name in (os.path.curdir, os.path.pardir):
                continue
            
            plugin_info = self._find_by_name_implementation(plugin_name, extra_steps)
            if not plugin_info:
                continue
            
            yield plugin_info

    
    def find_by_name(self, plugin_name: str, extra_steps: Sequence[PipelineStep] = []) -> Optional[PluginInfo]:
        self._error_string = ""  # reset error-string

        plugin_names = os.listdir(self._search_path)
        
        if plugin_name in (os.path.curdir, os.path.pardir):
            self._error_string = f"The plugin \"{plugin_name}\" cannot be of name \".\" or \"..\""
            return None
        
        if plugin_name not in plugin_names:
            self._error_string = f"The plugin \"{plugin_name}\" could not be found in the search directory"
            return None
        
        pinfo = self._find_by_name_implementation(plugin_name, extra_steps, create_error_string=True)
        return pinfo
            
            
    def _find_by_name_implementation(self, plugin_name: str, extra_steps: Sequence[PipelineStep], create_error_string = False) -> Optional[PluginInfo]:
        pinfo = PluginInfo(self._search_path, plugin_name)

        # Process pinfo through pipeline
        for i, step in enumerate(_chained([self._pipeline_steps, extra_steps])):
            result = step(pinfo)

            if isinstance(result, bool):
                success = result
                error_description = None
            else:
                success, error_description = result
            
            if success:
                continue
            else:
                if create_error_string:
                    # define an expressive error-message
                    if error_description:
                        error_string = f"The plugin \"{plugin_name}\" is invalid due to pipeline-step {i} with name \"{get_pipeline_step_name(step)}\" which failed with error-message \"{error_description}\""
                    else:
                        error_string = f"The plugin \"{plugin_name}\" is invalid due to pipeline-step {i} with name \"{get_pipeline_step_name(step)}\""
                    
                    self._error_string = error_string
                return None
        
        # Pipeline finished and successful
        return pinfo