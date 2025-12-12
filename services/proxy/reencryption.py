import base64
import uuid
import datetime
from services.proxy import db

def generate_rekey(from_user: str, to_user: str) -> dict:
    """
    Generates a mock re-encryption key and stores it in SQLite.
    """
    rk_id = f"rk_{uuid.uuid4().hex[:8]}"
    blob = base64.b64encode(f"mock_rk_blob_from_{from_user}_to_{to_user}".encode()).decode()
    
    conn = db.get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO rekeys (rk_id, from_user, to_user, blob, created_at) VALUES (?, ?, ?, ?, ?)",
              (rk_id, from_user, to_user, blob, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return {
        "rekey_id": rk_id,
        "rk_blob": blob
    }

def reencrypt(cipher_blob: str, rekey_id: str) -> str:
    """
    Simulates re-encryption using state from SQLite.
    """
    conn = db.get_db_connection()
    row = conn.execute("SELECT * FROM rekeys WHERE rk_id = ?", (rekey_id,)).fetchone()
    conn.close()
    
    if not row:
        raise ValueError("Invalid Re-Key ID")
        
    # Check validity (mock)
    try:
        raw = base64.b64decode(cipher_blob).decode()
    except:
        pass
        
    return cipher_blob
