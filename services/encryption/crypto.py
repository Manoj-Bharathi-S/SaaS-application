import base64
import requests
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from fastapi import BackgroundTasks

KMS_URL = "http://localhost:8005"
BLOCKCHAIN_URL = "http://localhost:8006"

def log_event(user: str, action: str, file_id: str, details: dict):
    try:
        requests.post(f"{BLOCKCHAIN_URL}/tx", json={
            "user": user,
            "action": action,
            "file_id": file_id,
            "details": details
        }, timeout=1)
    except:
        pass # Fire and forget failure for MVI

def get_key_from_kms(key_id: str) -> bytes:
    try:
        resp = requests.post(f"{KMS_URL}/get_key", json={"key_id": key_id}, timeout=2)
        resp.raise_for_status()
        key_b64 = resp.json()["key_bytes_b64"]
        return base64.b64decode(key_b64)
    except Exception as e:
        raise ValueError(f"Failed to fetch key from KMS: {e}")

def create_key_in_kms() -> str:
    try:
        resp = requests.post(f"{KMS_URL}/generate_key", json={"key_len": 32}, timeout=2)
        resp.raise_for_status()
        return resp.json()["key_id"]
    except Exception as e:
        raise ValueError(f"Failed to generate key in KMS: {e}")

def encrypt_data(data: bytes, key_id: str = None) -> dict:
    """
    Encrypts data using AES-GCM.
    Uses KMS to generate or fetch keys.
    """
    if not key_id:
        key_id = create_key_in_kms()
    
    key = get_key_from_kms(key_id)

    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data)

    return {
        "key_id": key_id,
        "nonce": base64.b64encode(cipher.nonce).decode('utf-8'),
        "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
        "tag": base64.b64encode(tag).decode('utf-8')
    }

def decrypt_data(encrypted_payload: dict, key_id: str) -> bytes:
    """
    Decrypts data using AES-GCM.
    Fetches key from KMS.
    """
    key = get_key_from_kms(key_id)
    
    nonce = base64.b64decode(encrypted_payload['nonce'])
    ciphertext = base64.b64decode(encrypted_payload['ciphertext'])
    tag = base64.b64decode(encrypted_payload['tag'])

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    
    return plaintext
