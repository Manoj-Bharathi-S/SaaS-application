import subprocess
import sys
import time
import requests
import os

# Ports
ENC_PORT = 8001
LB_PORT = 8002
PROXY1_PORT = 8003
PROXY2_PORT = 8004
KMS_PORT = 8005
CHAIN_PORT = 8006

ENC_URL = f"http://localhost:{ENC_PORT}"
LB_URL = f"http://localhost:{LB_PORT}"
KMS_URL = f"http://localhost:{KMS_PORT}"
CHAIN_URL = f"http://localhost:{CHAIN_PORT}"

def start_service(cmd_args, name, port):
    print(f"Starting {name}...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    # Open log files
    out = open(f"{name.replace(' ', '_')}.log", "w")
    
    proc = subprocess.Popen(cmd_args, env=env, stdout=out, stderr=subprocess.STDOUT)
    return proc, out
    url = f"http://localhost:{port}/health"
    start = time.time()
    while time.time() - start < 15:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                print(f"{name} is HEALTHY.")
                return proc
        except:
            pass
        time.sleep(1)
    
    print(f"{name} failed to start.")
    proc.terminate()
    return None

def main():
    procs = []
    files = []
    
    def launch(cmd, name, port):
        p, f = start_service(cmd, name, port)
        if p:
            procs.append(p)
            files.append(f)
            
            # Wait for health
            url = f"http://localhost:{port}/health"
            start = time.time()
            while time.time() - start < 15:
                try:
                    r = requests.get(url)
                    if r.status_code == 200:
                        print(f"{name} is HEALTHY.")
                        return p
                except:
                    pass
                time.sleep(1)
            print(f"{name} failed to start.")
            p.terminate()
            return None
        return None

    try:
        # Start DBs/Core
        launch([sys.executable, "services/kms/main.py"], "KMS", KMS_PORT)
        launch([sys.executable, "services/blockchain/main.py"], "Blockchain", CHAIN_PORT)

        # Start App Services
        launch([sys.executable, "services/encryption/main.py"], "Encryption", ENC_PORT)
        launch([sys.executable, "services/proxy/main.py", "--port", str(PROXY1_PORT), "--id", "p1"], "Proxy1", PROXY1_PORT)
        launch([sys.executable, "services/proxy/main.py", "--port", str(PROXY2_PORT), "--id", "p2"], "Proxy2", PROXY2_PORT)
        launch([sys.executable, "services/load_balancer/main.py"], "Load Balancer", LB_PORT)

        print("\n=== SYSTEM IS UP. RUNNING PHASE 3 TESTS ===\n")

        # 1. Run Share Flow (Generates Events)
        print(">> Running demo_share_flow.py (Should generate events)...")
        # Ensure demo_share_flow uses valid ports (LB 8002, Enc 8001) - default
        subprocess.check_call([sys.executable, "demos/demo_share_flow.py"])
        print("PASS: Share Flow")
        
        # 2. Run Audit
        print(">> Running demo_audit.py...")
        subprocess.check_call([sys.executable, "demos/demo_audit.py"])
        print("PASS: Audit")

        print("\n*** PHASE 3 VERIFICATION SUCCESSFUL ***")

    except Exception as e:
        print(f"FAILED: {e}")
        for p in procs:
            if p.poll() is not None:
                print(f"Process Output ({p.args}): \n{p.stderr.read().decode()}")

    finally:
        print("Stopping services...")
        for p in procs:
            p.terminate()
        for f in files:
            f.close()

if __name__ == "__main__":
    main()
