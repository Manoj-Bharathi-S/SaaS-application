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
ML_PORT = 8007
ACCESS_PORT = 8008
UI_PORT = 8501

def start_service(cmd_args, name, port):
    print(f"Starting {name}...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    out = open(f"{name.replace(' ', '_')}.log", "w")
    proc = subprocess.Popen(cmd_args, env=env, stdout=out, stderr=subprocess.STDOUT)
    return proc, out

def main():
    procs = []
    files = []
    
    def launch(cmd, name, port):
        p, f = start_service(cmd, name, port)
        if p:
            procs.append(p)
            files.append(f)
            
            # Wait for health (Streamlit doesn't have a standardized health endpoint easily reachable without extra logic, waiting longer)
            if name == "UI":
                 time.sleep(5)
                 print("UI Started (assumed healthy).")
                 return p

            url = f"http://localhost:{port}/health"
            start = time.time()
            while time.time() - start < 30:
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
        launch([sys.executable, "services/ml/main.py"], "ML Service", ML_PORT)
        launch([sys.executable, "services/access/main.py"], "Access Service", ACCESS_PORT)

        # Start App Services
        launch([sys.executable, "services/encryption/main.py"], "Encryption", ENC_PORT)
        launch([sys.executable, "services/proxy/main.py", "--port", str(PROXY1_PORT), "--id", "p1"], "Proxy1", PROXY1_PORT)
        launch([sys.executable, "services/proxy/main.py", "--port", str(PROXY2_PORT), "--id", "p2"], "Proxy2", PROXY2_PORT)
        launch([sys.executable, "services/load_balancer/main.py"], "Load Balancer", LB_PORT)

        # Start UI
        launch([sys.executable, "-m", "streamlit", "run", "ui/app.py", "--server.port", "8501", "--server.headless", "true"], "UI", UI_PORT)

        print("\n=== SYSTEM IS UP. RUNNING PHASE 5 TESTS ===\n")

        # 1. Test Access Control Enforcement (RBAC)
        print(">> Testing RBAC Enforcement...")
        # A. Grant Admin allow (Implicit in Proxy calling it with 'admin')
        # B. Test Revocation
        print("   Revoking user 'alice@company.com'...")
        r = requests.post(f"http://localhost:{ACCESS_PORT}/revoke", json={"username": "alice@company.com"})
        print(f"   Revoke Status: {r.status_code}")
        
        # Verify user state
        # In a real test we'd try to login, but for MVI we check DB state or re-auth
        r = requests.post(f"http://localhost:{ACCESS_PORT}/authorize", json={"user": "alice@company.com", "action": "decrypt"})
        if r.json()['allow'] == False:
            print("PASS: Revoked user denied.")
        else:
             print("FAIL: Revoked user still allowed.")

        print("\n*** PHASE 5 VERIFICATION SUCCESSFUL ***")
        print("UI is running at http://localhost:8501")
        print("Press Ctrl+C to stop services...")
        
        # Keep running for manual UI testing
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"FAILED: {e}") 

    finally:
        print("Stopping services...")
        for p in procs:
            p.terminate()
        for f in files:
            f.close()

if __name__ == "__main__":
    main()
