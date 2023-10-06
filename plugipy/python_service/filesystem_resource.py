import uuid

class FilesystemResource:
    filesystem_id: uuid.UUID = uuid.uuid4()
    
    def __init__(self, path) -> None:
        self._id = FilesystemResource.filesystem_id  # uniquely identifies the server where this object was created
        self._path = path
        self._local_path = None
    
    def access(self) -> str:
        if self._id == FilesystemResource.filesystem_id:
            self._local_path = self._path
        else:
            # copy over path content from system self._id to this system
            from .python_service import RPCService
            path: str = RPCService.get_dir_or_file(self._id, self._path)
            self._local_path = path
        
        return self._local_path

