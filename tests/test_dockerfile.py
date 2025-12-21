import os

def test_dockerfile_content():
    if not os.path.exists("Dockerfile"):
        print("FAIL: Dockerfile does not exist")
        exit(1)
        
    with open("Dockerfile", "r") as f:
        content = f.read()
        
    required_strings = [
        "FROM runpod/pytorch",
        "git clone https://github.com/Lightricks/LTX-Video.git",
        "pip install -e .[inference]",
        "COPY requirements.txt",
        "pip install -r requirements.txt"
    ]
    
    missing = []
    for s in required_strings:
        if s not in content:
            missing.append(s)
            
    if missing:
        print(f"FAIL: Dockerfile missing instructions: {missing}")
        exit(1)
        
    print("SUCCESS: Dockerfile looks good")
    exit(0)

if __name__ == "__main__":
    test_dockerfile_content()
