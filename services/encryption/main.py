from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks, Body
from pydantic import BaseModel
import base64
import sys
import os

# Add project root to sys.path to import common
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from common.schemas import EncryptRequest, EncryptResponse, DecryptRequest, DecryptResponse
from services.encryption import crypto, wrappers

app = FastAPI(title="Encryption Service")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/encrypt", response_model=EncryptResponse)
def encrypt(req: EncryptRequest, background_tasks: BackgroundTasks):
    try:
        data = base64.b64decode(req.plaintext)
        result = crypto.encrypt_data(data)
        
        # We pack nonce+ciphertext+tag into a single blob for the client
        # Format: nonce|ciphertext|tag (all base64)
        combined_cipher = f"{result['nonce']}|{result['ciphertext']}|{result['tag']}"
        
        cid = f"c_{base64.urlsafe_b64encode(os.urandom(4)).decode().strip('=')}"
        
        # Log to Blockchain
        owner = req.meta.get("owner", "unknown") if req.meta else "unknown"
        file_id = req.meta.get("file_id", "unknown") if req.meta else "unknown"
        
        background_tasks.add_task(crypto.log_event, owner, "ENC_FILE", file_id, {"key_id": result['key_id'], "cid": cid})
        
        return EncryptResponse(
            cipher_id=cid,
            cipher=base64.b64encode(combined_cipher.encode()).decode(), # Return as one blob
            key_id=result['key_id']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/decrypt", response_model=DecryptResponse)
def decrypt(req: DecryptRequest):
    try:
        # Unpack the blob
        raw_cipher_str = base64.b64decode(req.cipher).decode()
        parts = raw_cipher_str.split('|')
        if len(parts) != 3:
            raise ValueError("Invalid cipher format")
            
        payload = {
            'nonce': parts[0],
            'ciphertext': parts[1],
            'tag': parts[2]
        }
        
        plaintext_bytes = crypto.decrypt_data(payload, req.key_id)
        return DecryptResponse(plaintext=base64.b64encode(plaintext_bytes).decode())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class WrapRequest(BaseModel):
    key_id: str
    identity: str

@app.post("/wrap_key/ibe")
def wrap_ibe(req: WrapRequest):
    try:
        key_bytes = crypto.get_key_from_kms(req.key_id)
        wrapped = wrappers.ibe_wrap_key(key_bytes, req.identity)
        return {"wrapped": wrapped, "key_id": req.key_id}
    except ValueError:
        raise HTTPException(status_code=404, detail="Key not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
