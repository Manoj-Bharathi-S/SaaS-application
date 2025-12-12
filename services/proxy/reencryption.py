import base64
import uuid
import datetime

# In-memory store for re-encryption keys
# rk_id -> {from, to, created_at}
REKEY_STORE = {}

def generate_rekey(from_user: str, to_user: str) -> dict:
    """
    Generates a mock re-encryption key.
    """
    rk_id = f"rk_{uuid.uuid4().hex[:8]}"
    
    # In a real system, this would produce a mathematical key delta
    # key_A -> key_B. For MVI, we just store the permission intent.
    rekey_record = {
        "rk_id": rk_id,
        "from": from_user,
        "to": to_user,
        "created_at": datetime.datetime.now().isoformat()
    }
    REKEY_STORE[rk_id] = rekey_record
    
    # Return a blob that the client would *send* to the proxy
    # Here, the ID is sufficient for the proxy to look up the intent
    return {
        "rekey_id": rk_id,
        "rk_blob": base64.b64encode(f"mock_rk_blob_from_{from_user}_to_{to_user}".encode()).decode()
    }

def reencrypt(cipher_blob: str, rekey_id: str) -> str:
    """
    Simulates re-encryption.
    Takes a ciphertext (base64) and a rekey_id.
    Returns a new ciphertext (base64).
    """
    if rekey_id not in REKEY_STORE:
        raise ValueError("Invalid Re-Key ID")
        
    record = REKEY_STORE[rekey_id]
    
    # Check if the blob is valid (simple check)
    try:
        raw = base64.b64decode(cipher_blob).decode()
    except:
        raw = "invalid_blob"
        
    # Valid transformation mock:
    # Append the re-encryption metadata so the recipient knows it was transformed
    # Real PRE would mathematically alter the capsule.
    # We add a tag that Client B (or Encryption Service) can treat as "validly re-encrypted"
    
    # We assume the input format is nonce|ciphertext|tag (from Encryption Service)
    # We will just verify it looks right and pretend to transform it.
    # In MVI, we return the SAME ciphertext but wrapped or tagged.
    # NOTE: Our Encryption Service 'decrypt' expects nonce|cipher|tag.
    # It splits by |.  If we change it, decrypt might fail.
    # BUT, if we *don't* change it, it's not much of a demo.
    
    # Let's say the proxy logs the access and passes it through for Phase 1 MVI.
    # To prove "Re-Encryption" happened, we can append a metadata field that 'decrypt' ignores?
    # Or better: `decrypt` in `crypto.py` splits by `|`.
    # We can append `|reencrypted_for_<user>` and update `decrypt` to ignore extra fields.
    
    # However, `crypto.py` does `if len(parts) != 3: raise`.
    # So we must return exactly 3 parts for the current `decrypt` to work without modification.
    # OR we modify `crypto.py` (simulating the client software update).
    
    # Let's simple pass-through for MVI but Log it.
    # A real PRE produces a ciphertext that decrypts to the SAME plaintext 
    # but using B's key.
    # Since we are using a centralized KEY_STORE, B calls decrypt(key_id), 
    # and KEY_STORE has key_id. So it works.
    
    return cipher_blob
