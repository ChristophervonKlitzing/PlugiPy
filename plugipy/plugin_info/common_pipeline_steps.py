# General imports
import os
from typing import Tuple 

# Relative imports
from .plugin_info import PluginInfo
from .pipeline_step import PipelineStep, name_pipeline_step

@name_pipeline_step("directory-filter")
def directory_filter(pinfo: PluginInfo) -> Tuple[bool, str]:
    """
    PipelineStep which only lets through directories
    """
    plugin_path = pinfo.full_path
    return os.path.isdir(plugin_path), f"The path '{plugin_path}' is not a directory"


@name_pipeline_step("file-filter")
def file_filter(pinfo: PluginInfo) -> Tuple[bool, str]:
    """
    PipelineStep which only lets through files
    """
    plugin_path = pinfo.full_path
    return os.path.isfile(plugin_path), f"The path '{plugin_path}' is not a file"


def create_has_file_filter(filename: str, alias = None) -> PipelineStep:
    """
    Creates PipelineStep which checks for the existence of the given file specified by the 'filename' parameter
    """
    
    @name_pipeline_step("contains-file-filter")
    def has_file(pinfo: PluginInfo):
        filepath = os.path.join(pinfo.full_path, filename)
        isfile = os.path.isfile(filepath)

        if isfile and alias:
            setattr(pinfo.properties(), alias, filename)
        
        return isfile, f"The file '{filepath}' is not existing"
    
    return has_file


def create_has_directory_filter(dirname: str, alias = None) -> PipelineStep:
    """
    Creates PipelineStep which checks for the existence of the given directory specified by the 'dirname' parameter
    """
    
    @name_pipeline_step("contains-directory-filter")
    def has_dir(pinfo: PluginInfo):
        dirpath = os.path.join(pinfo.full_path, dirname)
        isdir = os.path.isdir(dirpath)

        if isdir and alias:
            setattr(pinfo.properties(), alias, dirname)
        
        return isdir, f"The directory '{dirpath}' is not existing"
    
    return has_dir

