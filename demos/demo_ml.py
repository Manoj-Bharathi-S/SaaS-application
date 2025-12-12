import requests
import json
import sys

ML_URL = "http://localhost:8007"

def demo_ml():
    print("--- Demo: ML Anomaly Detection ---")
    
    # 1. Train Model
    print("Training Model...")
    try:
        resp = requests.post(f"{ML_URL}/train", json={"contamination": 0.05})
        print(f"Train Response: {resp.json()}")
    except Exception as e:
        print(f"FAILED to train: {e}")
        sys.exit(1)

    # 2. Score Normal
    print("\nScoring Normal Event (12pm, 10MB)...")
    normal_payload = {
        "features": {
            "hour": 14,
            "download_mb": 5,
            "failed_logins": 0,
            "role_mismatch": 0
        }
    }
    resp = requests.post(f"{ML_URL}/score", json=normal_payload)
    print(f"Result: {resp.json()}")
    if resp.json()['is_anomaly']:
        print("FAIL: False Positive")
    else:
        print("PASS: Correctly identified as Normal")

    # 3. Score Anomaly
    print("\nScoring Anomaly (3am, 500MB)...")
    anom_payload = {
        "features": {
            "hour": 3,
            "download_mb": 500,
            "failed_logins": 5,
            "role_mismatch": 1
        }
    }
    resp = requests.post(f"{ML_URL}/score", json=anom_payload)
    print(f"Result: {resp.json()}")
    if resp.json()['is_anomaly']:
        print("PASS: Correctly identified as Anomaly")
    else:
        print("FAIL: False Negative")

if __name__ == "__main__":
    demo_ml()
