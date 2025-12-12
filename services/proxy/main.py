from fastapi import FastAPI, HTTPException, BackgroundTasks
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
def gen_rekey(req: ReKeyRequest, background_tasks: BackgroundTasks):
    from services.proxy import reencryption
    result = reencryption.generate_rekey(req.from_user, req.to_user)
    
    background_tasks.add_task(reencryption.log_event, req.from_user, "GEN_REKEY", "na", 
                             {"to": req.to_user, "rk_id": result['rekey_id']})
    
    return result

@app.post("/reencrypt", response_model=ReEncryptResponse)
def reencrypt_proxy(req: ReEncryptRequest, background_tasks: BackgroundTasks):
    from services.proxy import reencryption
    try:
        new_cipher = reencryption.reencrypt(req.cipher_blob, req.rekey_id)
        
        # Log event
        background_tasks.add_task(reencryption.log_event, "proxy", "PROXY_REENC", "unknown", 
                                 {"rk_id": req.rekey_id})
                                 
        return {"cipher_re": new_cipher}
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
