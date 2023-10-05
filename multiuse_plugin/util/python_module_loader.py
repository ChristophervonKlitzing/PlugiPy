import importlib.util
from types import ModuleType
import sys 
from typing import Optional, Tuple
import uuid 
import os
from dataclasses import dataclass
import importlib

def __import_module(module_name, module_path) -> Optional[ModuleType]:
    spec = importlib.util.spec_from_file_location(module_name, module_path, submodule_search_locations=[])

    if spec is None:
        return None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    
    # This allows relative imports
    sys.modules[module_name] = module
    
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError as e:
        raise RuntimeError(f"Failed loading the module with error message: {str(e)}")

    return module


class PythonModuleLoadError(RuntimeError):
    ...


def dynamically_load_as_new_python_module(module_path: str, /,*, module_name: Optional[str] = None, name_hint: Optional[str] = None) -> Tuple[ModuleType, str]:
    """
    Allows importing a module using its path. The same path can be imported twice which results in two different modules.
    This means that moduleA (path /a/foo.py) and moduleB (path /a/foo.py) have no side-effect on each other. However, keep in mind
    that a python module cannot be unloaded and keeps requiring resources. Therefore, creating a module just once and creating multiple
    instances of a modules class instead of loading the module itself multiple times can safe resources.

    ===========

    Parameters
        - module_path: str
            The path pointing to a valid python module
        - module_name: Optional[str]
            If this parameter is given it must be unique! Otherwise, a potential race-condition may occur or the wrong module gets returned.
            If this parameter is None, the created module name will be uniquely generated.
        - name_hint: Optional[str]
            This is an addition name-hint for debugging purposes. It is added to the module-name of the created module as a plain text
            if 'module_name' is None.
    
    Returns
        A module result object
        - The attribute 'module' is None in case of errors otherwise a valid ModuleType object.
        - The attribute 'module_name' contains the module name of the created module or an empty string if the module file is not existing.
        - The attribute 'error_string' contains a best-efford error description in case the module could not be loaded.
    """

    if not os.path.isfile(module_path):
        raise PythonModuleLoadError(f"No such python module: '{module_path}'")

    if module_name is None:
        if name_hint is None:
            # encode filename in module_name for debugging purposes (if filename is not empty)
            name_hint = os.path.basename(module_path).split(".")[0]

        if len(name_hint) > 0:
                name_hint = "_" + name_hint
        
        # create globally unique module_name
        module_name = "DynamicModuleLoader_" + str(uuid.uuid4()) + name_hint

    if module_name is not None and module_name in sys.modules:
        raise PythonModuleLoadError(f"The module with name {module_name} is already existing")

    # Potential race-condition between last if-check and module-creation!
    # This only happens if 'module_name' is given and not guaranteed to be unique 
    # and somewhere else a module is imported with the same name in between.
    # This case should not happen -> 'module_name' MUST must be unique!

    # check for dots in the name:
    if module_name.find(".") != -1:
        raise PythonModuleLoadError(f"The module_name '{module_name}' is invalid because it contains a dot ('.')")
    
    module = __import_module(module_name, module_path)
    if module is None:
        raise PythonModuleLoadError(f"Failed loading the module at path \"{module_path}\"")
    
    return module, module_name


    

