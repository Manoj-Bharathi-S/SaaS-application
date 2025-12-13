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
        # Phase 5: Access Control Check (RBAC)
        # Verify if the proxy (acting on behalf of user) is allowed.
        # In a real system, we'd check the destination user's permission.
        # MVI: Check if "proxy" role is authorized to reencrypt.
        import requests
        try:
            auth_resp = requests.post("http://localhost:8008/authorize", 
                                    json={"user": "admin", "action": "reencrypt"}, timeout=1)
            if auth_resp.status_code == 200 and not auth_resp.json().get("allow"):
                 raise HTTPException(status_code=403, detail="Access Denied: Re-encryption not allowed")
        except requests.exceptions.ConnectionError:
            pass # Fail open if Access Service down for MVI/Demo, or Fail Closed? Fail open for robustness.

        # Phase 4: ML Anomaly Check
        # detailed Mock features for now. In real system, fetch from history.
        import random
        
        # 10% chance of anomaly for demo purposes if not specified
        hour = 23 if random.random() < 0.1 else 14 
        download_size = 500 if hour == 23 else 5
        
        score_payload = {
            "features": {
                "hour": hour,
                "download_mb": download_size,
                "failed_logins": 0,
                "role_mismatch": 0
            }
        }
        
        is_anomaly = False
        try:
            ml_resp = requests.post("http://localhost:8007/score", json=score_payload, timeout=1)
            if ml_resp.status_code == 200:
                is_anomaly = ml_resp.json().get("is_anomaly", False)
                
                # Phase 5: Auto-Revoke Integration
                if is_anomaly:
                    # In real flow, revoke the DESTINATION user. 
                    # For MVI demo, we just log revocation call
                    try:
                        requests.post("http://localhost:8008/revoke", json={"username": "alice@company.com"})
                    except:
                        pass
        except:
            pass # Fail open if ML service down
            
        new_cipher = reencryption.reencrypt(req.cipher_blob, req.rekey_id)
        
        # Log event
        action = "PROXY_REENC"
        details = {"rk_id": req.rekey_id}
        
        if is_anomaly:
            action = "ANOMALY_DETECTED"
            details["warning"] = "Suspicious activity detected by ML"
            details["score"] = ml_resp.json().get("score")
            
        background_tasks.add_task(reencryption.log_event, "proxy", action, "unknown", details)
                                 
        return {"cipher_re": new_cipher}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
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
