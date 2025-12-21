import os

def test_requirements_exists_and_valid():
    if not os.path.exists("requirements.txt"):
        print("FAIL: requirements.txt does not exist")
        exit(1)
        
    with open("requirements.txt", "r") as f:
        content = f.read()
    
    required_packages = [
        "runpod",
        "fastapi",
        "uvicorn",
        "diffusers", 
        "transformers",
        "accelerate"
    ]
    
    missing = []
    for pkg in required_packages:
        if pkg not in content:
            missing.append(pkg)
            
    if missing:
        print(f"FAIL: requirements.txt missing packages: {missing}")
        exit(1)

    print("SUCCESS: requirements.txt looks good")
    exit(0)

if __name__ == "__main__":
    test_requirements_exists_and_valid()
