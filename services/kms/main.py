from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import os
import sys
import datetime
from Crypto.Random import get_random_bytes

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from services.kms import db
from services.encryption import wrappers # Reuse wrappers for now

app = FastAPI(title="Key Management Service")

@app.on_event("startup")
def startup():
    db.init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

class GenerateKeyRequest(BaseModel):
    key_len: int = 32

class GenerateKeyResponse(BaseModel):
    key_id: str

@app.post("/generate_key", response_model=GenerateKeyResponse)
def generate_key(req: GenerateKeyRequest):
    key = get_random_bytes(req.key_len)
    key_id = f"k_{base64.urlsafe_b64encode(get_random_bytes(6)).decode().strip('=')}"
    
    conn = db.get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO keys (key_id, key_bytes, created_at) VALUES (?, ?, ?)",
              (key_id, key, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return GenerateKeyResponse(key_id=key_id)

class GetKeyRequest(BaseModel):
    key_id: str

class GetKeyResponse(BaseModel):
    key_bytes_b64: str

@app.post("/get_key", response_model=GetKeyResponse)
def get_key(req: GetKeyRequest):
    conn = db.get_db_connection()
    row = conn.execute("SELECT key_bytes FROM keys WHERE key_id = ?", (req.key_id,)).fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Key not found")
        
    return GetKeyResponse(key_bytes_b64=base64.b64encode(row['key_bytes']).decode())

@app.get("/debug/keys")
def debug_keys():
    conn = db.get_db_connection()
    rows = conn.execute("SELECT key_id FROM keys").fetchall()
    conn.close()
    return {"keys": [row['key_id'] for row in rows]}

class WrapKeyRequest(BaseModel):
    key_id: str
    identity: str

@app.post("/wrap_key/ibe")
def wrap_ibe(req: WrapKeyRequest):
    # Fetch key
    conn = db.get_db_connection()
    row = conn.execute("SELECT key_bytes FROM keys WHERE key_id = ?", (req.key_id,)).fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Key not found")
        
    # Wrap
    wrapped = wrappers.ibe_wrap_key(row['key_bytes'], req.identity)
    return {"wrapped": wrapped, "key_id": req.key_id}

if __name__ == "__main__":
    import uvicorn
    print("Starting KMS on port 8005")
    uvicorn.run(app, host="0.0.0.0", port=8005)
