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
    
    # out = open(f"{name.replace(' ', '_')}.log", "w")
    # proc = subprocess.Popen(cmd_args, env=env, stdout=out, stderr=subprocess.STDOUT)
    # Stream to console for interactive debugging
    proc = subprocess.Popen(cmd_args, env=env)
    return proc, None

def main():
    procs = []
    files = []
    
    def launch(cmd, name, port):
        p, f = start_service(cmd, name, port)
        if p:
            procs.append(p)
            files.append(f)
            return p
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

        # Start UI (Interactive Mode)
        print("\n>> Launching Streamlit UI...")
        launch([sys.executable, "-m", "streamlit", "run", "ui/app.py", "--server.port", "8501"], "UI", UI_PORT)

        print("\n=== SYSTEM IS RUNNING ===")
        print(f"Dashboard: http://localhost:{UI_PORT}")
        print("Keep this terminal open.")
        print("Press Ctrl+C to stop all services.")
        
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
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
