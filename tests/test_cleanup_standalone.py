import os
import sys

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
        "Dockerfile.bak",
        # "Dockerfile", # We are keeping Dockerfile for now but overwriting it later, actually spec says remove old implementation files. 
        # But Dockerfile might be useful reference? No, spec says "Create a new Dockerfile".
        "Dockerfile",
        "requirements.txt",
        ".env.client.example",
        ".env.example",
        "key_single_line.txt"
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

    if found_files or found_dirs:
        print(f"FAIL: Old files still exist: {found_files}")
        print(f"FAIL: Old directories still exist: {found_dirs}")
        sys.exit(1)
    
    print("SUCCESS: All old files and directories removed.")
    sys.exit(0)

if __name__ == "__main__":
    test_old_files_removed()
