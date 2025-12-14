import requests
import base64
import json
import time

GATEWAY_URL = "http://localhost:8000"

def run_demo():
    print("=== Aegis SaaS Platform Demo ===\n")
    
    # 1. Admin: Provision a new Tenant
    print("[1] Provisioning 'TechCorp' Tenant...")
    try:
        res = requests.post(f"{GATEWAY_URL}/admin/tenants", json={"name": "TechCorp", "plan": "pro"})
        res.raise_for_status()
        tenant = res.json()
        print(f"    SUCCESS: Created Tenant '{tenant['name']}'")
        print(f"    API Key: {tenant['api_key']}")
        print(f"    Plan:    {tenant['plan']}")
    except Exception as e:
        print(f"    FAILED: {e}")
        return

    api_key = tenant['api_key']
    
    # 2. Tenant: Encrypt a File
    print("\n[2] Encrypting file as 'TechCorp'...")
    headers = {"X-API-Key": api_key}
    payload = {
        "plaintext": base64.b64encode(b"Sensitive Corporate Data").decode(),
        "meta": {"classification": "secret"}
    }
    
    try:
        res = requests.post(f"{GATEWAY_URL}/files/encrypt", json=payload, headers=headers)
        if res.status_code == 200:
            data = res.json()
            print(f"    SUCCESS: Encrypted via Gateway")
            print(f"    File ID: {data.get('file_id', 'N/A')}")
            print(f"    Cipher:  {data.get('cipher', '')[:20]}...")
        else:
            print(f"    FAILED: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 3. Decrypt the File
    print("\n[3] Decrypting file...")
    try:
        if 'cipher' in locals().get('data', {}):
            dec_payload = {"cipher": data['cipher'], "key_id": data['key_id']}
            res = requests.post(f"{GATEWAY_URL}/files/decrypt", json=dec_payload, headers=headers)
            if res.status_code == 200:
                pt = base64.b64decode(res.json()['plaintext']).decode()
                print(f"    SUCCESS: Decrypted Content: '{pt}'")
            else:
                print(f"    FAILED: {res.text}")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 4. Unauthorized Access Attempt
    print("\n[4] Attempting Access without API Key...")
    try:
        res = requests.post(f"{GATEWAY_URL}/files/encrypt", json=payload)
        if res.status_code == 401:
            print("    SUCCESS: Blocked (401 Unauthorized)")
        else:
            print(f"    FAILED: Expected 401, got {res.status_code}")
    except:
        pass

if __name__ == "__main__":
    # Wait for service to be ready
    for i in range(5):
        try:
            requests.get(f"{GATEWAY_URL}/health")
            break
        except:
            time.sleep(1)
            
    run_demo()
