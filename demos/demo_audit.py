import requests
import time
import sys
import json

CHAIN_URL = "http://localhost:8006"

def demo_audit():
    print("--- Demo: Blockchain Audit ---")
    
    print("Fetching chain from Blockchain Service...")
    # 1. Fetch Chain
    try:
        resp = requests.get(f"{CHAIN_URL}/chain", timeout=5)
        print(f"Status: {resp.status_code}")
        chain_data = resp.json()
    except Exception as e:
        print(f"FAILED to contact Blockchain Service: {e}")
        sys.exit(1)

    print(f"Chain Height: {chain_data['length']}")
    print("Events Recorded:")
    
    for block in chain_data['chain']:
        if block['index'] == 0: continue # Skip genesis
        
        # Each block has 1 tx in our MVI
        for tx in block['transactions']:
            print(f"- [Block {block['index']}] User: {tx['user']} | Action: {tx['action']} | File: {tx['file_id']}")
            print(f"  Hash: {block['hash']}")

    # 2. Verify Integrity
    v_resp = requests.get(f"{CHAIN_URL}/validate").json()
    print(f"\nIntegrity Check: {'PASS' if v_resp['is_valid'] else 'FAIL'}")

if __name__ == "__main__":
    demo_audit()
