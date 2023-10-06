from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
import io
import uuid
from plugipy.python_service.future import Future, FutureWrapper, ResultFuture, RemoteFuture
import concurrent.futures as cf
import importlib
import os
from typing import Callable, Dict, Any, Optional, Protocol, Tuple, Type
import queue
import threading
from ..plugin_info.plugin_info import PluginInfo
import rpyc
import pickle

from .filesystem_resource import FilesystemResource
from ..util.directory_encoder import decode_directory, encode_directory
# from multiuse_plugin.util.python_module_loader import dynamically_load_as_new_python_module


class PythonService(ABC):
    def __init__(self, *args, **kw_args) -> None:
        ...


class ServiceDescription:
    def __init__(self, service_class: Type[PythonService], plugin_info: PluginInfo, /, *service_args, **service_kw_args) -> None:
        self._service_cls = service_class
        
        class PythonModuleRequirement(Protocol):
            python_module_file: str

        self._plugin_path = plugin_info.full_path

        properties = plugin_info.properties(PythonModuleRequirement, expect_attributes=True)
        self._plugin_module_name = properties.python_module_file

        self._service_args = service_args
        self._service_kw_args = service_kw_args
    
    @property
    def service_class_module(self):
        return self._service_cls.__module__
    
    @property
    def service_class_name(self):
        return self._service_cls.__name__
    
    @property
    def service_class(self):
        return self._service_cls
    
    @property
    def plugin_directory_path(self):
        return self._plugin_path
    
    @property
    def plugin_module_name(self):
        return self._plugin_module_name
    
    @property
    def plugin_module_path(self):
        return os.path.join(self.plugin_directory_path, self.plugin_module_name)
    
    def get_all_service_args(self):
        return self._service_args, self._service_kw_args

    


class ServiceExecutor(ABC):
    def __init__(self) -> None:
        ...

    @abstractmethod
    def run_task(self, fname: str, *args, **kw_args) -> Any:
        ...
    
    def start_task_scheduling(self):
        ...
    
    def stop_task_scheduling(self):
        ...

    @abstractmethod
    def submit_task(self, fname: str, *args, **kw_args) -> Future:
        """
        Enqueues the task for execution. It returns an id which identifies the task and allows retrieval of its results
        using the get_task_result function.
        """
        ...

class LocalServiceExecutor(ServiceExecutor):
    def __init__(self, service_description: ServiceDescription) -> None:
        super().__init__()

        service_class = service_description.service_class
        plugin_module_path = service_description.plugin_module_path
        service_args, service_kw_args = service_description.get_all_service_args()

        self._service: Optional[PythonService] = service_class(plugin_module_path, *service_args, **service_kw_args)
    
    def run_task(self, fname: str, *args, **kw_args):
        f = getattr(self._service, fname)
        return f(*args, **kw_args)
    
    def submit_task(self, fname: str, *args, **kw_args) -> Future:
        return ResultFuture(self.run_task(fname, *args, **kw_args))
    

class ThreadedServiceExecutor(ServiceExecutor):
    def __init__(self, service_description: ServiceDescription) -> None:
        super().__init__()

        service_class = service_description.service_class
        plugin_module_path = service_description.plugin_module_path
        service_args, service_kw_args = service_description.get_all_service_args()

        self._service: Optional[PythonService] = service_class(plugin_module_path, *service_args, **service_kw_args)

        self._executor = ThreadPoolExecutor(max_workers=1)
    
    def run_task(self, fname: str, *args, **kw_args):
        # blocks anyways -> might as well be executed in the same thread
        f = getattr(self._service, fname)
        return f(*args, **kw_args)
    
    def submit_task(self, fname: str, *args, **kw_args) -> Future:
        f = getattr(self._service, fname)
        concurrent_future = self._executor.submit(f, *args, **kw_args)
        return FutureWrapper(concurrent_future)
    
class ProcessServiceExecutor(ServiceExecutor):
    def __init__(self, service_description: ServiceDescription) -> None:
        super().__init__()

        service_class = service_description.service_class
        plugin_module_path = service_description.plugin_module_path
        service_args, service_kw_args = service_description.get_all_service_args()

        self._service: Optional[PythonService] = service_class(plugin_module_path, *service_args, **service_kw_args)

        self._executor = ProcessPoolExecutor(max_workers=1)
    
    def run_task(self, fname: str, *args, **kw_args):
        # blocks anyways -> might as well be executed in the same thread
        f = getattr(self._service, fname)
        return f(*args, **kw_args)
    
    def submit_task(self, fname: str, *args, **kw_args) -> Future:
        f = getattr(self._service, fname)
        concurrent_future = self._executor.submit(f, *args, **kw_args)
        return FutureWrapper(concurrent_future)

class RemoteServiceExecutor(ServiceExecutor):
    """
    Some services may need resources which are not available locally (like GPUs)
    or the service is itself connected to some other server and benefits from the physical proximity to it.
    """

    def __init__(self, service_description: ServiceDescription, address: str, port: int) -> None:
        # TODO: Add option for secure connection
        super().__init__()

        # Connect to remote server
        conn = rpyc.connect(address, port)

        # set network reference object for remote server access outside of the constructor
        self._remote_service_executor: RPCService = conn.root  # actually just a proxy of the remote RemoteRPCServiceExecutor instance

        # convert plugin directory into a streamable data-block
        plugin_data = service_description.plugin_directory_path  # TODO: replace with actual data

        # register this process for filesystem access
        self._remote_service_executor.register_filesystem_access(FilesystemResource.filesystem_id, self.convert_dir_or_file_to_bytes)

        # transfer plugin data to remote server
        self._remote_service_executor.copy_plugin(plugin_data)

        # initialize the service on the remote server
        service_class_module = service_description.service_class_module
        service_class_name = service_description.service_class_name
        plugin_module_name = service_description.plugin_module_name
        service_args, service_kw_args = service_description.get_all_service_args()
        encoded_args_and_kw_args = self._encode_args(service_args, service_kw_args)
        self._remote_service_executor.init_service(service_class_module, service_class_name, plugin_module_name, encoded_args_and_kw_args)

        # attributes for submit task
        self._next_id = 0
        self._future_buffer: Dict[int, RemoteFuture] = dict()
        self._future_buffer_lock = threading.Lock()
    
    def convert_dir_or_file_to_bytes(self, path: str) -> bytes:
        dir_path = os.path.dirname(path)
        object_name = os.path.basename(path)
        encoded_directory = encode_directory(os.path.dirname(path), whitelist={object_name}, ignore_patterns={"__pycache__"})
        
        return pickle.dumps(encoded_directory)

    # ============ helper functions ================:
    def _encode_args(self, args, kw_args):
        # TODO: Allows the extension to pass objects by reference on purpose
        return pickle.dumps(tuple((args, kw_args)))

    # ========== run task ==========================:
    
    def run_task(self, fname: str, *args, **kw_args):
        args_and_kw_args = self._encode_args(args, kw_args)

        # This is a call on a proxy object which passes it to the remote RemoteRPCService object
        pickled_result = self._remote_service_executor.call_func(fname, args_and_kw_args)
        result = pickle.loads(pickled_result)
        return result

    # ========= submit task implementation ==========:

    def _get_next_id(self) -> int:
        id = self._next_id
        self._next_id += 1
        return id
    
    def _get_result(self, id: int) -> None: 
        with self._future_buffer_lock:
            pickled_results = self._remote_service_executor.get_results(id)
            results: Dict[int, RPCServiceResult] = pickle.loads(pickled_results)

            for id, res in results.items():
                future = self._future_buffer.pop(id)
                future.set_result(res.result, res.exception)
    
    def submit_task(self, fname: str, *args, **kw_args) -> Future:
        """
        Works well if the remote server is on the web with a significant round-trip-time
        and the service requires some time for execution.

        It buffers the results from the service and only sends them in batches
        if a result gets requested from a returned future object. Futhermore,
        the asynchronous computation and buffering enables doing other stuff 
        in parallel to the service without waiting for it.
        """
        args_and_kw_args = self._encode_args(args, kw_args)
        id = self._get_next_id()

        future = RemoteFuture(id, self._get_result)
        with self._future_buffer_lock:
            self._future_buffer[id] = future
        self._remote_service_executor.submit_func(id, fname, args_and_kw_args)
        return future



@dataclass
class RPCServiceResult:
    result: Any
    exception: Optional[Exception]
    id: int

@rpyc.service
class RPCService(rpyc.Service):
    @dataclass
    class Task:
        fname: str
        args: Tuple[Any]
        kw_args: Dict[str, Any]
        id: int
    
    dir_file_getters: Dict[str, Callable[[str], bytes]] = dict()

    @classmethod
    def get_dir_or_file(cls, id: uuid.UUID, path: str):
        dir_file_getter = cls.dir_file_getters[str(id)]
        
        # retrieve data from client
        path_content_data: bytes = dir_file_getter(path)
        encoded_directory = pickle.loads(path_content_data)

        folder_id = str("instance_id")
        target_dir = f"./tmp/{folder_id}"

        # decodes into directory target_dir
        decode_directory(encoded_directory, target_dir, clean_target_dir=True)

        target_object_name = os.path.basename(path)
        return os.path.join(target_dir, target_object_name)
        

    def __init__(self) -> None:
        super().__init__()

        self._executor = ThreadPoolExecutor(max_workers=1)
        self._results_buffer: Dict[int, RPCServiceResult] = dict()
        self._get_results_cond = threading.Condition()

    @rpyc.exposed
    def register_filesystem_access(self, id: uuid.UUID, get_dir_or_file: Callable[[str], bytes]):
        if id in self.dir_file_getters:
            raise RuntimeError(f"Filesystem access with id {id} is already existing")
        
        self.dir_file_getters[str(id)] = get_dir_or_file

    @rpyc.exposed
    def copy_plugin(self, plugin_data: Any):
        print("copied over plugin directory")
        self._plugin_path = plugin_data  # TODO: Replace with path to deserialized plugin folder

    @rpyc.exposed
    def init_service(self, service_class_module: str, service_class_name: str, plugin_module_name: str, encoded_args_and_kw_args: bytes): # this is an exposed method
        # Get service class from module
        service_module = importlib.import_module(service_class_module)
        service_class = getattr(service_module, service_class_name)

        service_args, service_kw_args = self._decode_args(encoded_args_and_kw_args)
        
        print(f"initialize service remotely {service_args} {service_kw_args}")
        plugin_module_path = os.path.join(self._plugin_path, plugin_module_name)
        self._service = service_class(plugin_module_path, *service_args, **service_kw_args)

    def call_service_func(self, fname: str, *args, **kw_args) -> Any:
        f = getattr(self._service, fname)
        result = f(*args, **kw_args)
        return result
    
    @rpyc.exposed
    def call_func(self, fname: str, args_and_kw_args: bytes) -> bytes:
        args, kw_args = self._decode_args(args_and_kw_args)
        
        result = self.call_service_func(fname, *args, **kw_args)
        # by default rpyc does not transfer items but only creates a proxy object for mutable objects (pass by reference).
        # pickle.dumps creates an immutable bytes object which forces rpyc to transfer it by value instead of by reference.
        return pickle.dumps(result)  
        
    # ============ submit implementation: ================

    def call_service_func_wrapper(self, id: int, fname: str, *args, **kw_args) -> RPCServiceResult:
        """
        Wrapper function to include an id in the Future result from the ThreadPoolExecutor.
        """
        try:
            result = self.call_service_func(fname, *args, **kw_args)
            return RPCServiceResult(result, None, id)
        except Exception as e:
            return RPCServiceResult(None, e, id)
    
    def done_callback(self, future: cf.Future):
        # all exceptions already handled by target function; exceptions are encoded in the result
        result: RPCServiceResult = future.result()

        with self._get_results_cond:
            self._results_buffer[result.id] = result
            self._get_results_cond.notify()

    def _decode_args(self, args_and_kw_args: bytes):
        args, kw_args = pickle.loads(args_and_kw_args)
        return args, kw_args
        
    @rpyc.exposed
    def submit_func(self, id: int, fname: str, args_and_kw_args: bytes):
        args, kw_args = self._decode_args(args_and_kw_args)

        concurrent_future = self._executor.submit(self.call_service_func_wrapper, id, fname, *args, **kw_args)
        concurrent_future.add_done_callback(self.done_callback)
    
    @rpyc.exposed
    def get_results(self, id: int) -> bytes:
        with self._get_results_cond:
            while id not in self._results_buffer:
                self._get_results_cond.wait()
            
            results = self._results_buffer
            self._results_buffer = dict()
        
        return pickle.dumps(results)
