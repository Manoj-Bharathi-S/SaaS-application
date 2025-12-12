from fastapi import FastAPI, HTTPException
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from common.schemas import ReKeyRequest, ReKeyResponse, ReEncryptRequest, ReEncryptResponse
from services.proxy import reencryption

app = FastAPI(title="Proxy Service")

@app.on_event("startup")
def startup():
    from services.proxy import db
    db.init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/gen_rekey", response_model=ReKeyResponse)
def gen_rekey(req: ReKeyRequest):
    try:
        result = reencryption.generate_rekey(req.from_user, req.to_user)
        return ReKeyResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reencrypt", response_model=ReEncryptResponse)
def reencrypt_ep(req: ReEncryptRequest):
    try:
        new_cipher = reencryption.reencrypt(req.cipher_blob, req.rekey_id)
        return ReEncryptResponse(cipher_re=new_cipher)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--id", type=str, default="proxy_1")
    args = parser.parse_args()
    
    print(f"Starting Proxy Service {args.id} on port {args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
