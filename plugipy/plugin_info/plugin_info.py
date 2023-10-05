# General imports
import os
from typing import Any, TypeVar, Type


class _Properties:  
    ...
    

class PluginInfo:
    def __init__(self, base_path, plugin_name) -> None:
        self._base_path = base_path
        self._plugin_name = plugin_name

        self._properties = _Properties()
    
    @property
    def base_path(self):
        return self._base_path
    
    @property
    def name(self):
        return self._plugin_name
    
    @property
    def full_path(self):
        return os.path.join(self._base_path, self._plugin_name)
    
    T = TypeVar('T')
    def properties(self, type: Type[T] = Any, expect_attributes=False) -> T:
        if expect_attributes:
            self.expect_property_attributes(type)
        
        return self._properties  # type: ignore  # is necessary to prevent a static type-error. The typed-return-feature is mainly for type-hinting for allowing auto-completion.
    
    def expect_property_attributes(self, type: Type[Any]) -> None:
        anns = type.__dict__["__annotations__"] if "__annotations__" in type.__dict__ else dict()
        for name, type in anns.items():
            if name not in self._properties.__dict__:
                raise RuntimeError(f"The properties object is missing the expected attribute \"{name}\" of type \"{type.__name__}\"")
            
            attribute = self._properties.__dict__[name]
            
            if not isinstance(attribute, type):
                raise RuntimeError(f"The property attribute \"{name}\" of type \"{attribute.__class__.__name__}\" is incompatible with the expected type \"{type.__name__}\"")
    