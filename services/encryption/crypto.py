import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# In-memory "Key Management" for Phase 1 MVI
# Stores key_id -> bytes
KEY_STORE = {}

def generate_aes_key(key_len=32):
    return get_random_bytes(key_len)

def encrypt_data(data: bytes, key_id: str = None) -> dict:
    """
    Encrypts data using AES-GCM.
    If key_id is None, generates a new key.
    Stores the key in global KEY_STORE for MVI.
    """
    if key_id and key_id in KEY_STORE:
        key = KEY_STORE[key_id]
    else:
        key = generate_aes_key()
        if not key_id:
            key_id = f"k_{base64.urlsafe_b64encode(get_random_bytes(6)).decode().strip('=')}"
        KEY_STORE[key_id] = key

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
    Expects encrypted_payload to contain nonce, ciphertext, tag.
    """
    if key_id not in KEY_STORE:
        raise ValueError(f"Key {key_id} not found")

    key = KEY_STORE[key_id]
    
    nonce = base64.b64decode(encrypted_payload['nonce'])
    ciphertext = base64.b64decode(encrypted_payload['ciphertext'])
    tag = base64.b64decode(encrypted_payload['tag'])

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    
    return plaintext
