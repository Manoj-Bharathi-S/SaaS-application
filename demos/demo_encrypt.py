import requests
import base64
import sys

ENC_URL = "http://localhost:8001"

def demo_encryption():
    print("--- Demo: Encryption Service ---")
    
    # 1. Encrypt
    plaintext = "Secret Message! Highly Confidential."
    print(f"Original: {plaintext}")
    
    payload = {
        "plaintext": base64.b64encode(plaintext.encode()).decode(),
        "meta": {"owner": "Alice"}
    }
    
    try:
        resp = requests.post(f"{ENC_URL}/encrypt", json=payload)
        resp.raise_for_status()
        enc_data = resp.json()
        print(f"Encrypted: ID={enc_data['cipher_id']} KeyID={enc_data['key_id']}")
        print(f"Cipher Blob: {enc_data['cipher'][:30]}...")
        
        # 2. Decrypt
        dec_payload = {
            "cipher": enc_data['cipher'],
            "key_id": enc_data['key_id']
        }
        
        resp2 = requests.post(f"{ENC_URL}/decrypt", json=dec_payload)
        resp2.raise_for_status()
        dec_data = resp2.json()
        
        decrypted_text = base64.b64decode(dec_data['plaintext']).decode()
        print(f"Decrypted: {decrypted_text}")
        
        assert plaintext == decrypted_text
        print("SUCCESS: Plaintext matches!")
        return enc_data, plaintext
        
    except Exception as e:
        print(f"FAILED: {e}")
        return None, None

if __name__ == "__main__":
    demo_encryption()
