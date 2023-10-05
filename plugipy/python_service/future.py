from abc import ABC, abstractmethod
import threading
from typing import Any, Optional, Callable, Tuple
import concurrent.futures as cf


class Future(ABC):
    @abstractmethod
    def result(self, timeout=None) -> Any:
        ...
    
    @abstractmethod
    def exception(self) -> Optional[BaseException]:
        ...

    @abstractmethod
    def done(self) -> bool:
        ...

    @abstractmethod
    def running(self) -> bool:
        ...


class FutureWrapper(Future):
    """
    Future which wraps concurrent.futures.Future
    """
    def __init__(self, future: cf.Future) -> None:
        super().__init__()
        self._future = future
    
    def result(self, timeout=None) -> Any:
        return self._future.result(timeout)

    def exception(self, timeout=None) -> Optional[BaseException]:
        return self._future.exception(timeout)
    
    def done(self) -> bool:
        return self._future.done()
    
    def running(self) -> bool:
        return self._future.running()

class ResultFuture(Future):
    """
    Future which immediately holds the result 
    """

    def __init__(self, result) -> None:
        super().__init__()
        self._result = result
    
    def result(self, timeout=None) -> Any:
        return self._result
    
    def exception(self) -> Optional[BaseException]:
        return None  # may change in the future

    def done(self) -> bool:
        return True
    
    def running(self) -> bool:
        return False

class RemoteFuture(Future):
    def __init__(self, id: int, wait_for_result: Callable[[int], None]) -> None:
        super().__init__()
        self._id = id

        self._result: Any = None 
        self._exception: Any = None
        self._done = False

        self._wait_for_result = wait_for_result
    
    def set_result(self, result, exception):
        self._result = result
        self._exception = exception
        self._done = True
    
    def result(self, timeout: Optional[float] = None) -> Any:
        if not self.done():
            self._wait_for_result(self._id)

        if self._result:
            return self._result
        else:
            raise self._exception
        
    def exception(self, timeout: Optional[float] = None) -> Optional[BaseException]:
        if not self.done():
            self._wait_for_result(self._id)
        
        return self._exception

    def done(self) -> bool:
        """
        Return True if either the exception or the result value is not None.
        """
        return self._done
    
    def running(self) -> bool:
        ...

    
class Future_:
    def __init__(self):
        self._result = None
        self.exception = None
        self._done_event = threading.Event()

    def set_result(self, result):
        self._result = result
        self._done_event.set()

    def set_exception(self, exception):
        self.exception = exception
        self._done_event.set()

    def result(self, timeout=None) -> Any:
        self._done_event.wait(timeout)
        if self.exception:
            raise self.exception
        return self._result

    def done(self) -> bool:
        return self._done_event.is_set()

    def __str__(self):
        return f"CustomFuture(result={self._result}, exception={self.exception})"
