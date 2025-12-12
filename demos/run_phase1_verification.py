import subprocess
import sys
import time
import requests
import os

# Define service ports
ENC_PORT = 8001
PROXY_PORT = 8002
ENC_URL = f"http://localhost:{ENC_PORT}"
PROXY_URL = f"http://localhost:{PROXY_PORT}"

def install_deps():
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def start_service(path, port):
    print(f"Starting service at {path} on port {port}...")
    # Use sys.executable to ensure we use the same python env
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    # We assume the service main.py uses uvicorn.run internally on port 8001/8002
    # But wait, main.py hardcodes the port in __main__ execution.
    # encryption/main.py -> 8001
    # proxy/main.py -> 8002
    
    proc = subprocess.Popen([sys.executable, path], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def wait_for_health(url, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{url}/health")
            if r.status_code == 200:
                print(f"Service at {url} is healthy.")
                return True
        except:
            pass
        time.sleep(1)
    print(f"Service at {url} failed to start.")
    return False

def run_demos():
    print("\n=== Running Encryption Demo ===")
    try:
        subprocess.check_call([sys.executable, "demos/demo_encrypt.py"])
        print("Encryption Demo: PASSED")
    except subprocess.CalledProcessError:
        print("Encryption Demo: FAILED")
        return False

    print("\n=== Running Share Flow Demo ===")
    try:
        subprocess.check_call([sys.executable, "demos/demo_share_flow.py"])
        print("Share Flow Demo: PASSED")
    except subprocess.CalledProcessError:
        print("Share Flow Demo: FAILED")
        return False
        
    return True

def main():
    # 1. Start Services
    enc_proc = start_service("services/encryption/main.py", ENC_PORT)
    proxy_proc = start_service("services/proxy/main.py", PROXY_PORT)
    
    try:
        # 2. Wait for health
        if not wait_for_health(ENC_URL) or not wait_for_health(PROXY_URL):
            print("Services failed to start. checking logs...")
            # Print stderr
            print(f"Encryption Err: {enc_proc.stderr.read().decode()}")
            print(f"Proxy Err: {proxy_proc.stderr.read().decode()}")
            return
            
        # 3. Run Demos
        success = run_demos()
        
        if success:
            print("\n*** PHASE 1 VERIFICATION SUCCESSFUL ***")
        else:
            print("\n*** PHASE 1 VERIFICATION FAILED ***")
            
    finally:
        print("\nStopping services...")
        enc_proc.terminate()
        proxy_proc.terminate()
        
if __name__ == "__main__":
    main()
