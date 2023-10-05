# General imports
from typing import Callable, List, Optional, Protocol, Dict, Any, Type, TypeVar

# Relative imports
from ..plugin_info.plugin_info import PluginInfo
from ..util.parameters import Parameter, get_standard_parameter_types, parameters_from_dict
 

class ConfigHandle:
    def __init__(self, 
                 pinfo: PluginInfo, 
                 supported_parameter_types: Dict[str, Type[Parameter[Any]]] = get_standard_parameter_types(), 
                 on_parameter_value_change: Optional[Callable[[Dict[str, Any]], Any]] = None
                 ) -> None:
        print("init configurable-plugin")

        class PropertiesRequirement(Protocol):
            config_specification: dict

        self._config_specification_dict: dict = pinfo.properties(type=PropertiesRequirement, expect_attributes=True).config_specification

        self._parameters: Dict[str, Parameter[Any]] = {
            param.name: param 
            for param in  parameters_from_dict(self._config_specification_dict, supported_parameter_types)
            }
        
        self._supported_types = supported_parameter_types
        self._on_param_value_change = on_parameter_value_change
    
    
    def set_parameter_value(self, parameter_name: str, value: Any):
        """
        Alters the parameter value if possible. Returns True on success, else False.
        """
        success = self._parameters[parameter_name].set_value(value)
        if success and self._on_param_value_change:
            self._on_param_value_change({parameter_name: self._parameters[parameter_name].get_value()})
        return success
    
    T = TypeVar('T')
    def get_parameter_value(self, parameter_name: str, type: Type[T] = Any) -> T:
        """
        Returns the parameter value 
        """
        return self._parameters[parameter_name].get_value()
    
    def get_all_parameter_values(self) -> Dict[str, Any]:
        return {name: self.get_parameter_value(name) for name in self.get_all_parameter_names()}

    def get_all_parameter_names(self) -> List[str]:
        """
        Return the names of the parameters
        """
        return list(self._parameters.keys())
    
    def get_all_parameter_specifications(self) -> Dict[str, Dict[str, Any]]:
        return self._config_specification_dict
    
    def get_parameter_specification(self, parameter_name: str) -> Dict[str, Any]:
        return self._config_specification_dict[parameter_name]
    
    def get_supported_parameters_dict(self) -> Dict[str, Type[Parameter]]:
        return self._supported_types
    
    def get_parameter_description(self, parameter_name: str) -> str:
        return self._parameters[parameter_name].description
    
    def get_all_parameter_descriptions(self) -> Dict[str, str]:
        return {param.name: param.description for param in self._parameters.values()}
    
    def set_multiple_parameter_values(self, key_value_dict: Dict[str, Any]) -> Dict[str, bool]:
        success_dict = {param_name: self._parameters[param_name].set_value(key_value_dict[param_name]) for param_name in key_value_dict}

        if self._on_param_value_change:
            changed_parameters: Dict[str, Any] = {}
            for param_name, success in success_dict.items():
                if success:
                    changed_parameters[param_name] = self._parameters[param_name].get_value()
            
            if len(changed_parameters) > 0:
                self._on_param_value_change(changed_parameters)
        
        return success_dict