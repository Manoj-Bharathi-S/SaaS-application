import requests
import base64
import time
import subprocess
import os
import sys

ENC_URL = "http://localhost:8001"
PROXY_URL = "http://localhost:8002"

def run_services():
    """Starts services as subprocesses."""
    print("Starting services...")
    # Use different ports
    env = os.environ.copy()
    
    # Hack to run services using python -m
    # We assume we are in root
    enc_proc = subprocess.Popen([sys.executable, "services/encryption/main.py"], env=env)
    proxy_proc = subprocess.Popen([sys.executable, "services/proxy/main.py"], env=env)
    
    time.sleep(3) # Wait for startup
    return enc_proc, proxy_proc

def stop_services(pl):
    for p in pl:
        p.terminate()

def demo_share_flow():
    print("\n--- Demo: Proxy Share Flow ---")
    
    # 1. Alice Encrypts
    plaintext = "Financial Report 2025"
    print(f"[Alice] Encrypting: '{plaintext}'")
    
    enc_resp = requests.post(f"{ENC_URL}/encrypt", json={
        "plaintext": base64.b64encode(plaintext.encode()).decode()
    }).json()
    
    cipher_blob = enc_resp['cipher']
    key_id = enc_resp['key_id']
    print(f"[Alice] Got Cipher: {cipher_blob[:20]}... KeyID: {key_id}")
    
    # 2. Alice generates Re-Key for Bob
    print(f"[Alice] Generating Re-Key for Bob...")
    rekey_resp = requests.post(f"{PROXY_URL}/gen_rekey", json={
        "from_user": "alice@company.com",
        "to_user": "bob@company.com"
    }).json()
    
    rk_id = rekey_resp['rekey_id']
    print(f"[Alice] Created Re-Key ID: {rk_id}")
    
    # 3. Proxy Re-Encrypts
    print(f"[Proxy] Re-encrypting for Bob using {rk_id}...")
    re_resp = requests.post(f"{PROXY_URL}/reencrypt", json={
        "cipher_blob": cipher_blob,
        "rekey_id": rk_id
    }).json()
    
    re_cipher = re_resp['cipher_re']
    print(f"[Proxy] New Cipher Blob: {re_cipher[:20]}...")
    
    # 4. Bob Decrypts
    # In a real scenario, Bob would use his own key which the re-cipher unlocks.
    # In MVI, Bob uses the re_cipher with the original key_id (or a derived one).
    # Since our MVI proxy passed through the cipher (and KeyStore is shared/global/mocked),
    # Bob just calls decrypt.
    
    print(f"[Bob] Decrypting received blob...")
    try:
        dec_resp = requests.post(f"{ENC_URL}/decrypt", json={
            "cipher": re_cipher,
            "key_id": key_id 
        }).json()
        
        dec_text = base64.b64decode(dec_resp['plaintext']).decode()
        print(f"[Bob] Decrypted: '{dec_text}'")
        
        if dec_text == plaintext:
            print("SUCCESS: Bob recovered the file!")
        else:
            print("FAILURE: Content mismatch.")
            
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    # We assume services are running or started manually for this script if called directly,
    # OR we can auto-start them. for simplicity in this artifact, we assume checking liveness
    try:
        requests.get(f"{ENC_URL}/health")
        requests.get(f"{PROXY_URL}/health")
    except:
        print("Services not running. Please start them or run this via the test runner.")
        sys.exit(1)
        
    demo_share_flow()
