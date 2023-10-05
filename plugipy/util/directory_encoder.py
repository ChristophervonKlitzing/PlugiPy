from typing import List, Optional, Set
import zipfile
import os
import io
from functools import partial
import re
import shutil

def _is_subpath(base_path: str, subpath: str) -> bool:
    return subpath.startswith(base_path) and len(base_path) < len(subpath)

def _clean_path(root_dir: str, path: str) -> str:
    if os.path.isabs(path):
        return os.path.relpath(path, root_dir)
    else:
        return os.path.relpath(os.path.join(root_dir, path), root_dir)  # removes unnecessary "./", "/", etc


def _whitelist_walk(root_dir: str, whitelist_paths: Optional[Set[str]], ignore_patterns: Optional[Set[str]] = None):
    """
    Walks through the directory structure starting at root_dir. It only iterates over the directories and files specified
    """

    # Prepare parameters for implementation:
    if whitelist_paths:
        # make all paths relative to root directory
        whitelist_paths = {_clean_path(root_dir, path) for path in whitelist_paths}

        # extend whitelist_paths to include add the prefixes of the whitelist paths
        # otherwise they would be ignored and the white-listed subdirectories would never be iterated over.
        parent_extensions = set()
        for path in whitelist_paths:
            parent_path = os.path.dirname(path)
            while len(parent_path) > 0:
                parent_extensions.add(parent_path)
                parent_path = os.path.dirname(parent_path)
        
        # extend whitelist_path to include all parent directories
        whitelist_paths.update(parent_extensions)
    
    if ignore_patterns:
        compiled_ignore_patterns = {re.compile(pattern) for pattern in ignore_patterns}
    else:
        compiled_ignore_patterns = {}

    
    # implementation
    def _whitelist_walk_impl(root_dir: str, whitelist_paths: Optional[Set[str]], curr_dir: str):
        filenames = []
        dirpaths = []
        for entry_name in os.listdir(curr_dir):
            if entry_name in [os.path.pardir, os.path.curdir]:
                continue
            
            # make path relative to root directory
            entry_root_path = os.path.relpath(os.path.join(curr_dir, entry_name), root_dir)
            entry_complete_path = os.path.join(root_dir, entry_root_path)

            if whitelist_paths and entry_root_path not in whitelist_paths:
                continue
            
            # ignore entry if at least one pattern matches the file or directory name
            if any({pattern.match(entry_name) for pattern in compiled_ignore_patterns}):
                continue
            
            if os.path.isdir(entry_complete_path):
                dirpaths.append(entry_root_path)
            else:
                assert os.path.isfile(entry_complete_path), f"{entry_complete_path} must be a file"
                filenames.append(entry_name)

        yield curr_dir, None, filenames

        for dirpath in dirpaths:
            if whitelist_paths:
                # filter out all paths which are not part of the sub-directory entry_root_path
                filtered_whitelist_paths = {path for path in whitelist_paths if _is_subpath(dirpath, path)}
                if len(filtered_whitelist_paths) == 0:
                    filtered_whitelist_paths = None
            else:
                filtered_whitelist_paths = None

            yield from _whitelist_walk_impl(root_dir, filtered_whitelist_paths, os.path.join(root_dir, dirpath))
    
    # use implementation
    yield from _whitelist_walk_impl(root_dir, whitelist_paths, root_dir)


def encode_directory(source_directory: str, whitelist: Optional[Set[str]]=None, ignore_patterns: Optional[Set[str]] = None):
    """
    Parameters:
      - source_directory:
            The directory which should be encoded. This directory can either be relative to the current working directory or absolute.
      - white_list: 
            A set of paths relative to the source_directory or absolute which should be included or None.
            If the set is None, everything is included, else only the directories and files specified in white_list
            are included. It can happen that one path in white_list is a sub-directory of another path in white_list.
            In such cases, the most specific path is used. 
            
            E.g. whitelist=["dirA", "dirA/dirB"] and dirA contains dirB and dirC, only dirB is included because "dirA/dirB" is more
            specific than "dirA".
      - ignore_patterns:
            A set of string regex patterns. A file- or directory-name which matches at least one regex in the set, is ignored/excluded.
            If the ignored object is a directory, all its content is ignored too, even if some of its content is white-listed.
            This option is useful to exclude folders like "__pycache__".
    """
    zip_buffer = io.BytesIO()
    
    if whitelist or ignore_patterns:
        directory_walker = partial(_whitelist_walk, source_directory, whitelist, ignore_patterns)
    else:
        directory_walker = partial(os.walk, source_directory)
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, _, filenames in directory_walker():
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                archive_path = os.path.relpath(file_path, source_directory)
                zipf.write(file_path, archive_path)

    zip_buffer.seek(0)
    return zip_buffer

def decode_directory(zip_buffer: io.BytesIO, target_directory: str, /, *, clean_target_dir=False):
    # remove target directory if existing to prevent artifacts from prior executions
    if clean_target_dir and os.path.exists(target_directory) and os.path.isdir(target_directory):
        shutil.rmtree(target_directory)

    # Create a target directory where you want to extract the ZIP contents
    os.makedirs(target_directory, exist_ok=True)

    # Reset the position of the zip_buffer to the beginning
    zip_buffer.seek(0)

    # Create a ZipFile object for reading from the in-memory binary stream
    with zipfile.ZipFile(zip_buffer, 'r') as zipf:
        # Extract all contents from the ZIP archive
        zipf.extractall(target_directory)

if __name__ == "__main__":
    whitelist={"./plugin_handles", "util"}
    ignore_patterns = {"__pycache__"}

    buffer = encode_directory("multiuse_plugin", whitelist=whitelist, ignore_patterns=ignore_patterns)
    decode_directory(buffer, "decoded", clean_target_dir=True)
