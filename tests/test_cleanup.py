import os
import pytest

def test_old_files_removed():
    # List of files that should be removed
    files_to_remove = [
        "handler.py",
        "generate_i2v.py",
        "base64_converter.py",
        "client_example.py",
        "config.py",
        "gui.py",
        "uploader.py",
        "utils.py",
        "validation.py",
        "test_workflow.py",
        "runpod1",
        "runpod1.pub",
        "Dockerfile.bak"
    ]
    
    # List of directories to remove
    dirs_to_remove = [
        "v1",
        "_OLD",
        "output"
    ]

    found_files = []
    for f in files_to_remove:
        if os.path.exists(f):
            found_files.append(f)
            
    found_dirs = []
    for d in dirs_to_remove:
        if os.path.exists(d):
            found_dirs.append(d)

    assert not found_files, f"Old files still exist: {found_files}"
    assert not found_dirs, f"Old directories still exist: {found_dirs}"
