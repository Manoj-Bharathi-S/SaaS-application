from fastapi import FastAPI, HTTPException, BackgroundTasks
import httpx
import asyncio
import sys
import os
from typing import List

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from common.schemas import ReEncryptRequest, ReEncryptResponse, ReKeyRequest, ReKeyResponse

app = FastAPI(title="Load Balancer Service")

# Configuration (In a real app, load from config/env)
PROXY_NODES = [
    "http://localhost:8003",
    "http://localhost:8004"
]

class LoadBalancer:
    def __init__(self, nodes: List[str]):
        self.nodes = nodes
        self.healthy_nodes = []
        self.current_idx = 0
        self._lock = asyncio.Lock()

    async def update_health(self):
        healthy = []
        async with httpx.AsyncClient() as client:
            for node in self.nodes:
                try:
                    resp = await client.get(f"{node}/health", timeout=2.0)
                    if resp.status_code == 200:
                        healthy.append(node)
                except:
                    pass
        
        async with self._lock:
            self.healthy_nodes = healthy
            # print(f"Healthy nodes: {self.healthy_nodes}")

    async def get_next_node(self):
        async with self._lock:
            if not self.healthy_nodes:
                return None
            
            node = self.healthy_nodes[self.current_idx % len(self.healthy_nodes)]
            self.current_idx += 1
            return node

lb = LoadBalancer(PROXY_NODES)

@app.on_event("startup")
async def startup_event():
    # Initial health check
    await lb.update_health()
    # Start background loop
    asyncio.create_task(health_check_loop())

async def health_check_loop():
    while True:
        await asyncio.sleep(5)
        await lb.update_health()

@app.get("/health")
def health():
    return {
        "status": "ok", 
        "healthy_upstreams": len(lb.healthy_nodes),
        "total_upstreams": len(lb.nodes)
    }

@app.post("/reencrypt", response_model=ReEncryptResponse)
async def map_reencrypt(req: ReEncryptRequest):
    node = await lb.get_next_node()
    if not node:
        raise HTTPException(status_code=503, detail="No healthy proxies available")
    
    async with httpx.AsyncClient() as client:
        try:
            # Forward the request
            resp = await client.post(f"{node}/reencrypt", json=req.dict())
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Proxy error")
            return resp.json()
        except httpx.RequestError:
             raise HTTPException(status_code=502, detail="Proxy communication failed")

@app.post("/gen_rekey", response_model=ReKeyResponse)
async def map_genrekey(req: ReKeyRequest):
    node = await lb.get_next_node()
    if not node:
        raise HTTPException(status_code=503, detail="No healthy proxies available")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{node}/gen_rekey", json=req.dict())
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Proxy error")
            return resp.json()
        except httpx.RequestError:
             raise HTTPException(status_code=502, detail="Proxy communication failed")

if __name__ == "__main__":
    import uvicorn
    # Load Balancer runs on 8002 (Taking over the original Proxy port? -> No, original used 8002)
    # The Plan said LB runs on separate port? Original demos used 8002 for Proxy.
    # To keep demos compatible, we should run LB on 8002, and move Proxies to 8003/8004.
    print("Starting Load Balancer on port 8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
