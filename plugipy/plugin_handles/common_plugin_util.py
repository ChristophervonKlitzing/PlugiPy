# General imports
from typing import Any, Protocol
from abc import ABC, abstractmethod


# Relative imports
from ..plugin_info.plugin_info import PluginInfo


class PluginInfoAccessible:
    def __init__(self, pinfo: PluginInfo) -> None:
        self.__pinfo = pinfo
        print("init python-info-accessible")
    
    def get_info(self) -> PluginInfo:
        return self.__pinfo





class PersistablePlugin(ABC):
    def __init__(self) -> None:
        print("init persistable-plugin")

    @abstractmethod
    def load_state_from_storage(self, instance_identifier: Any):
        ...
    
    @abstractmethod
    def save_state_to_storage(self, instance_identifier: Any):
        ...


