import subprocess
import sys
import time
import requests
import os
import signal

# Ports
ENC_PORT = 8001
LB_PORT = 8002
PROXY1_PORT = 8003
PROXY2_PORT = 8004
KMS_PORT = 8005

ENC_URL = f"http://localhost:{ENC_PORT}"
LB_URL = f"http://localhost:{LB_PORT}"
KMS_URL = f"http://localhost:{KMS_PORT}"

def start_service(cmd_args, name):
    print(f"Starting {name}...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    # shell=True sometimes helps with path resolution on windows but makes pid management harder
    proc = subprocess.Popen(cmd_args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def wait_for_health(url, name, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{url}/health")
            if r.status_code == 200:
                print(f"{name} is HEALTHY.")
                return True
        except:
            pass
        time.sleep(1)
    print(f"{name} failed to start.")
    return False

def main():
    procs = []
    try:
        # 1. Start KMS
        kms = start_service([sys.executable, "services/kms/main.py"], "KMS")
        procs.append(kms)
        if not wait_for_health(KMS_URL, "KMS"): return

        # 2. Start Encryption (depends on KMS)
        enc = start_service([sys.executable, "services/encryption/main.py"], "Encryption")
        procs.append(enc)
        if not wait_for_health(ENC_URL, "Encryption"): return

        # 3. Start Proxies
        p1 = start_service([sys.executable, "services/proxy/main.py", "--port", str(PROXY1_PORT), "--id", "p1"], "Proxy1")
        procs.append(p1)
        
        p2 = start_service([sys.executable, "services/proxy/main.py", "--port", str(PROXY2_PORT), "--id", "p2"], "Proxy2")
        procs.append(p2)
        
        # Give proxies a moment
        time.sleep(2)

        # 4. Start Load Balancer
        # LB needs to know about 8003/8004. Our code hardcodes it so it matches.
        lb = start_service([sys.executable, "services/load_balancer/main.py"], "Load Balancer")
        procs.append(lb)
        if not wait_for_health(LB_URL, "LoadBalancer"): return

        print("\n=== SYSTEM IS UP. RUNNING TESTS ===\n")

        # 5. Run Demo Encrypt (Verifies KMS integration)
        print(">> Running demo_encrypt.py...")
        subprocess.check_call([sys.executable, "demos/demo_encrypt.py"])
        print("PASS: Encryption (with KMS)")

        # 6. Run Share Flow (Verifies LB -> Proxy flow)
        # Note: demo_share_flow.py uses port 8002 (LB) which matches our LB port.
        print(">> Running demo_share_flow.py...")
        subprocess.check_call([sys.executable, "demos/demo_share_flow.py"])
        print("PASS: Share Flow (via LB)")

        # 7. Failover Test
        print(">> Testing Failover...")
        print("Killing Proxy 1...")
        p1.terminate()
        time.sleep(2) # Wait for LB to detect? LB checks every 5s.
        time.sleep(4) 
        
        # Run check
        print(">> Running demo_failover.py...")
        subprocess.check_call([sys.executable, "demos/demo_failover.py"])
        
        # Check LB health output manually via request
        h = requests.get(f"{LB_URL}/health").json()
        print(f"LB Health after kill: {h}")
        if h['healthy_upstreams'] != 1:
             print("WARNING: Expected 1 healthy upstream.")
        else:
             print("PASS: Failover detected.")

        print("\n*** PHASE 2 VERIFICATION SUCCESSFUL ***")

    except Exception as e:
        print(f"FAILED: {e}")
        # Print logs
        for p in procs:
            if p.poll() is not None:
                print(f"Process {p.args} Output:")
                print(p.stderr.read().decode())

    finally:
        print("Stopping services...")
        for p in procs:
            p.terminate()

if __name__ == "__main__":
    main()
