from fastapi import FastAPI, Header, HTTPException, Request, Depends
from pydantic import BaseModel
import httpx
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from services.gateway import db

app = FastAPI(title="Aegis SaaS Gateway")

# Core Service URLs
ENC_URL = "http://localhost:8001"
PROXY_URL = "http://localhost:8002"
ACCESS_URL = "http://localhost:8008"
AUDIT_URL = "http://localhost:8006"

@app.on_event("startup")
def startup():
    db.init_db()
    # Ensure default tenant exists for demo
    if not db.get_tenant_by_apikey("sk_demo_tenant"):
        # Manually insert for determinism
        conn = db.get_db_connection()
        conn.execute("INSERT OR IGNORE INTO tenants (id, name, plan, api_key) VALUES (?, ?, ?, ?)",
                     ("t_demo", "Acme Corp", "enterprise", "sk_demo_tenant"))
        conn.commit()
        conn.close()

@app.get("/health")
def health():
    return {"status": "gateway_ok", "mode": "saas"}

# --- Middleware / Dependency for Auth ---

async def verify_tenant(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    
    tenant = db.get_tenant_by_apikey(x_api_key)
    if not tenant:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    if tenant['status'] != 'active':
        raise HTTPException(status_code=403, detail="Tenant Suspended")
        
    return tenant

# --- SaaS Admin APIs ---

class CreateTenantReq(BaseModel):
    name: str
    plan: str = "starter"

@app.post("/admin/tenants")
def register_tenant(req: CreateTenantReq):
    return db.create_tenant(req.name, req.plan)

# --- Proxy Endpoints (The "Gateway" Logic) ---

@app.post("/files/encrypt")
async def encrypt_file(request: Request, tenant: dict = Depends(verify_tenant)):
    # 1. Enforce Plan Limits (Mock logic)
    if tenant['plan'] == 'starter':
        # Check quota... (skipped for MVP)
        pass

    # 2. Forward to Internal Encryption Service
    # We inject tenant_id into metadata
    body = await request.json()
    if 'meta' not in body:
        body['meta'] = {}
    body['meta']['tenant_id'] = tenant['id']
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{ENC_URL}/encrypt", json=body, timeout=10)
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/share")
async def share_file(request: Request, tenant: dict = Depends(verify_tenant)):
    # Forward to Proxy Load Balancer
    # Future: Check if 'recipient' is in same tenant or allowed external
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            # Re-map: Public API /share -> Internal /gen_rekey
            # In real app, we'd map emails to user IDs here
            resp = await client.post(f"{PROXY_URL}/gen_rekey", json=body, timeout=10)
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/decrypt")
async def decrypt_file(request: Request, tenant: dict = Depends(verify_tenant)):
    # Forward to Internal Decryption Service
    # In a real SaaS, we'd verify the user owns the key or has permission
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{ENC_URL}/decrypt", json=body, timeout=10)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
