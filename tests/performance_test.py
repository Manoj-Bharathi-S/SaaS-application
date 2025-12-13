import time
import requests
import json
import base64
import statistics

# Configuration
ITERATIONS = 20
ENC_URL = "http://localhost:8001"
PROXY_URL = "http://localhost:8002"
ML_URL = "http://localhost:8007"
CHAIN_URL = "http://localhost:8006"

def measure_encryption():
    latencies = []
    payload = {
        "plaintext": base64.b64encode(b"Performance Test Data Payload " * 10).decode(), # ~300 bytes
        "meta": {"owner": "perf_test"}
    }
    
    for i in range(ITERATIONS):
        start = time.time()
        requests.post(f"{ENC_URL}/encrypt", json=payload, timeout=10)
        latencies.append((time.time() - start) * 1000)
        print(".", end="", flush=True)
    print(" Done!")
    return latencies

def measure_reencryption():
    # Setup: Create initial ciphertext and rekey
    try:
        pt_payload = {"plaintext": base64.b64encode(b"Re-Enc Test").decode(), "meta": {"owner": "alice"}}
        enc_res = requests.post(f"{ENC_URL}/encrypt", json=pt_payload, timeout=10).json()
        cipher_blob = enc_res['cipher']
        
        rekey_res = requests.post(f"{PROXY_URL}/gen_rekey", json={"from_user": "alice", "to_user": "bob"}, timeout=10).json()
        rekey_id = rekey_res['rekey_id']
    except Exception as e:
        print(f"\nSetup failed: {e}")
        return []
    
    latencies = []
    reenc_payload = {"cipher_blob": cipher_blob, "rekey_id": rekey_id}
    
    print("Re-Encrypting", end="", flush=True)
    for i in range(ITERATIONS):
        start = time.time()
        requests.post(f"{PROXY_URL}/reencrypt", json=reenc_payload, timeout=10)
        latencies.append((time.time() - start) * 1000)
        print(".", end="", flush=True)
    print(" Done!")
        
    return latencies

def measure_ml_score():
    features = {"features": {"hour": 14, "download_mb": 10, "failed_logins": 0, "role_mismatch": 0}}
    latencies = []
    print("Scoring ML", end="", flush=True)
    for i in range(ITERATIONS):
        start = time.time()
        requests.post(f"{ML_URL}/score", json=features, timeout=10)
        latencies.append((time.time() - start) * 1000)
        print(".", end="", flush=True)
    print(" Done!")
    return latencies

def warmup():
    print("Warming up services...", end="", flush=True)
    try:
        requests.get(f"{ENC_URL}/health", timeout=5)
        requests.get(f"{PROXY_URL}/health", timeout=5)
        requests.get(f"{ML_URL}/health", timeout=5)
        print(" Done!")
    except Exception as e:
        print(f"\nWarmup failed: {e}")

def run_benchmarks():
    warmup()
    print(f"Running benchmarks ({ITERATIONS} iterations)...")
    
    try:
        # Check health first
        requests.get(f"{ENC_URL}/health", timeout=5)
    except:
        print("Error: Services not running? Cannot connect.")
        return

    enc_times = measure_encryption()
    reenc_times = measure_reencryption()
    ml_times = measure_ml_score()
    
    metrics = {
        "encryption_ms": {
            "avg": statistics.mean(enc_times),
            "p95": statistics.quantiles(enc_times, n=20)[-1] if len(enc_times) >= 20 else max(enc_times),
            "min": min(enc_times),
            "max": max(enc_times)
        },
        "reencryption_ms": {
            "avg": statistics.mean(reenc_times),
            "p95": statistics.quantiles(reenc_times, n=20)[-1] if len(reenc_times) >= 20 else max(reenc_times),
            "note": "Includes ML Anomaly Check overhead"
        },
        "ml_scoring_ms": {
            "avg": statistics.mean(ml_times),
            "max": max(ml_times)
        }
    }
    
    print("\n=== Performance Metrics ===")
    print(json.dumps(metrics, indent=2))
    
    import os
    os.makedirs("metrics", exist_ok=True)
    with open("metrics/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("\nSaved to metrics/metrics.json")

if __name__ == "__main__":
    run_benchmarks()
