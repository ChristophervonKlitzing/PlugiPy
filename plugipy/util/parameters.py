# General imports
from typing import Generic, Iterable, List, Optional, Dict, Any, Type, TypeVar, Union
from abc import ABC, abstractmethod

# Relative imports


class ParameterConfigError(RuntimeError):
    pass 

T = TypeVar('T')
class Parameter(Generic[T], ABC):
    """
    Interface which defines how a minimal parameter should look like.
    """

    _get_type = type  # type function alias to allow type as one of the arguments in the constructor and type() being callable

    def __init__(self, name: str, type: str, description="") -> None:
        if not isinstance(name, str):
            raise ParameterConfigError(f"A parameter must have a name of type \"str\" but got \"{Parameter._get_type(name)}\"")
        if not isinstance(type, str):
            raise ParameterConfigError(f"A parameter must have a type-specification of type \"str\" but got \"{Parameter._get_type(type)}\"")
        if len(name) == 0:
            raise ParameterConfigError(f"A parameter name cannot be the empty string")
        if len(type) == 0:
            raise ParameterConfigError(f"A parameter type cannot be the empty string")
        if not isinstance(description, str):
            raise ParameterConfigError(f"The parameter {name} got an invalid argument \"description\" of type \"{Parameter._get_type(description)}\" but must be of type \"str\"")

        self._name = name
        self._type = type
        self._description = description

    @property
    def type(self) -> str:
        """
        Returns the type-string of this parameter type.
        """
        return self._type
    
    @property
    def name(self) -> str:
        """
        Returns the name of this parameter.
        """
        return self._name
    
    @property
    def description(self) -> str:
        """
        Returns an optional description of this parameter.
        """
        return self._description

    @abstractmethod
    def set_value(self, value: T) -> bool:
        """
        Sets the value if possible/valid. If the value is valid and is set, True is returned, else False.

        Potential checks are:
            - range (min, max)
            - type of input value
            - ...
        """
        ...
    
    @abstractmethod
    def get_value(self) -> T:
        ...



class IntParameter(Parameter[int]):
    """
    An IntParameter holds a single int value. Optionally, some constraints like limits can be added.
    """

    def __init__(self, default: int, min: Optional[int] = None, max: Optional[int] = None, **args) -> None:
        super().__init__(**args)

        if min and not isinstance(min, int):
            raise ParameterConfigError(f"The paramater {self.name} got an invalid argument \"min\" of type \"{type(min)}\" but must be of type \"int\"")
        if max and not isinstance(max, int):
            raise ParameterConfigError(f"The paramater {self.name} got an invalid argument \"max\" of type \"{type(max)}\" but must be of type \"int\"")
        
        self._value = 0
        self._min = min
        self._max = max

        if not self.set_value(default):
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"default\" which does not satisfy the given conditions")

    def set_value(self, value: int) -> bool:
        if not isinstance(value, int):
            return False
        
        if self._min and value < self._min:
            return False
        
        if self._max and value > self._max:
            return False

        self._value = value
        return True
    
    def get_value(self) -> int:
        return self._value


class FloatParameter(Parameter[float]):
    """
    A FloatParameter holds a single float value. Optionally, some constraints like limits can be added.
    """

    def __init__(self, default: float, min: Optional[float] = None, max: Optional[float] = None, **args) -> None:
        super().__init__(**args)

        if min and not isinstance(min, float):
            raise ParameterConfigError(f"The paramater {self.name} got an invalid argument \"min\" of type \"{type(min)}\" but must be of type \"float\"")
        if max and not isinstance(max, float):
            raise ParameterConfigError(f"The paramater {self.name} got an invalid argument \"max\" of type \"{type(max)}\" but must be of type \"float\"")
        
        self._value = 0.0
        self._min = min
        self._max = max

        if not self.set_value(default):
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"default\" which does not satisfy the given conditions")

    def set_value(self, value: float) -> bool:
        if not isinstance(value, float):
            return False
        
        if self._min and value < self._min:
            return False
        
        if self._max and value > self._max:
            return False

        self._value = value
        return True
    
    def get_value(self) -> float:
        return self._value


class OptionsParameter(Parameter[str]):
    """
    An OptionsParameter holds a list of options in form of strings. At every moment, exactly one option is selected.
    """

    def __init__(self, options: List[str], default: Optional[Union[str, int]] = None, **args) -> None:
        super().__init__(**args)

        if not isinstance(options, list):
            raise ParameterConfigError(f"The paramater {self.name} got an invalid argument \"choices\" of type \"{type(options)}\" but must be of type \"list\"")
        if len(options) == 0:
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"choices\" which must contain at least one element")
        if not all([isinstance(c, str) for c in options]):
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"choices\" which must only contain string elements")
        if len(set(options)) < len(options):
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"choices\" which must not contain duplicate elements")
        
        self._options = options
        self._choice: int = 0

        if default and not self.set_value(default):
            num_options = len(self._options)
            raise ParameterConfigError(
                f"The paramater {self.name} got an invalid argument \"default\" which must either be one of the options "
                f"or the index of an option e.g. i from (0, ..., #options - 1) = (0, ..., {num_options - 1})"
                )

    def set_value(self, value: Union[str, int]) -> bool:
        if not isinstance(value, (str, int)):
            return False
        
        if isinstance(value, str):
            if value not in self._options:
                return False
            
            index = self._options.index(value)
        else:
            index = value

            if not (0 <= index < len(self._options)):
                return False
        
        self._choice = index
        return True
    
    def get_value(self) -> str:
        return self._options[self._choice]


class StringParameter(Parameter[str]):
    """
    A StringParameter holds a string. Optionally, some extra constraints like a regular expression or size-constraints can be provided.
    """

    def __init__(self, default: str, regex: Optional[str] = None, min_length: Optional[int] = None, max_length: Optional[int] = None, **args) -> None:
        
        super().__init__(**args)

        if regex and not isinstance(regex, str):
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"regex\" of type \"{type(regex)}\" but must be of type \"str\"")
        if not isinstance(default, str):
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"default\" of type \"{type(default)}\" but must be of type \"str\"")
        
        if min_length and not isinstance(min_length, int):
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"min_length\" of type \"{type(min_length)}\" but must be of type \"int\"")
        if max_length and not isinstance(max_length, int):
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"max_length\" of type \"{type(max_length)}\" but must be of type \"int\"")
        
        if regex:
            import re 
            self._pattern = re.compile(regex)
        else:
            self._pattern = None
        
        self._value = ""
        self._min_length = min_length
        self._max_length = max_length
        self._error_string = ""

        if not self.set_value(default, create_error_string=True):
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"default\" because {self._error_string}")
        
    def set_value(self, value: str, /,*, create_error_string=False) -> bool:
        self._error_string = ""  # reset error-string
        
        if not isinstance(value, str):
            if create_error_string:
                self._error_string = "the input value is not of type \"str\""
            return False
        
        if self._pattern and not self._pattern.match(value):
            if create_error_string:
                self._error_string = "the input value did not match the regex pattern"
            return False
        
        if self._min_length and len(value) < self._min_length:
            if create_error_string:
                self._error_string = "the input value is shorter than the specified minimum length"
            return False
        
        if self._max_length and len(value) > self._max_length:
            if create_error_string:
                self._error_string = "the input value is longer than the specified maximum length"
            return False
        
        self._value = value
        return True
    
    def get_value(self) -> str:
        return self._value


class BoolParameter(Parameter[bool]):
    """
    A BoolParameter holds exactly one of two values: True and False.
    """

    def __init__(self, default: bool, **args) -> None:
        super().__init__(**args)
        
        if not isinstance(default, bool):
            raise ParameterConfigError(f"The parameter {self.name} got an invalid argument \"default\" of type \"{type(default)}\" but must be of type \"bool\"")

        self._value = default
    
    def set_value(self, value: bool) -> bool:
        if not isinstance(value, bool):
            return False
        
        self._value = value
        return True

    def get_value(self) -> bool:
        return self._value

# Potentially also: ListParameter and DictParameter

def get_standard_parameter_types() -> Dict[str, Type[Parameter]]:
    """
    Returns a dict which represents a set of standard parameter types. The returned dict object can optionally be expanded
    with custom Parameter classes and passed into functions like :func:`parameters_from_dict`.
    """
    return {
        "int": IntParameter, 
        "float": FloatParameter,
        "options": OptionsParameter,
        "string": StringParameter,
        "bool": BoolParameter,
        }

    
def parameters_from_dict(
        parameter_dict_specification: Dict[str, Dict[str, Any]],
        supported_parameter_types: Dict[str, Type[Parameter]]
        ) -> Iterable[Parameter]:
    """
    Creates a list of parameters from the given specification (parameter_dict_specification)
    using the supported parameter types (supported_parameter_types).

    Parameters
    ------------
        - parameter_dict_specification:
            A dict which maps the unique parameter names to their individual specification. 
            A parameter specification is a dict which must hold a "type" : <parameter-type-name> (e.g. "type": "int").
            Optionally also a description entry can be provided in the form "description": "<some-text-description>".
            The parameter specification must also fulfil the requirements of specified parameter type.

        - supported_parameter_types:
            This dict defines which parameter types are supported by this function.
            A dict which maps the supported parameter-type-names to their parameter class (e.g. {"int": IntParameter, "float": FloatParameter}).
    
    Return
    -----------
        parameters:
            - The list of parameters objects created from the parameter-specification and the supported parameter types.
    """

    type_to_parameter_class = supported_parameter_types

    for param_name, spec in parameter_dict_specification.items():
        # Check if parameter name is of type string
        if not isinstance(param_name, str):
            raise ParameterConfigError(f"The parameter name {param_name} is not of type \"str\"")
        
        # Check if parameter name is not the empty string
        if len(param_name) == 0:
            raise ParameterConfigError(f"A parameter name cannot be the empty string")
        
        # Check if the parameter-specification of that parameter is a dict
        if not isinstance(spec, dict):
            raise ParameterConfigError(f"The parameter {param_name} has a specification which is not of type \"dict\"")
        
        # Check if parameter-specification contain a valid type attribute
        if "type" not in spec:
            raise ParameterConfigError(f"The parameter {param_name} is missing the \"type\" specification")
        
        param_type = spec["type"]

        if not isinstance(param_type, str):
            raise ParameterConfigError(f"The type value of parameter {param_name} is not of type \"str\"")
        if len(param_type) == 0:
            raise ParameterConfigError(f"The type value of parameter {param_name} cannot be the empty string")
        if not spec["type"] in type_to_parameter_class:
            raise ParameterConfigError(f"The parameter type \"{spec['type']}\" of parameter {param_name} is not supported")

        # TODO: Maybe use the inspect module to check the constructor arguments and improve the error-messages
        # Parse parameter into Parameter instance  
        parameter = type_to_parameter_class[param_type](name=param_name, **spec)

        # output parameter
        yield parameter