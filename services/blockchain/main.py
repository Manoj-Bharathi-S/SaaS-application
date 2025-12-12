from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from services.blockchain.ledger import Blockchain

app = FastAPI(title="Blockchain Service")
blockchain = Blockchain()

@app.get("/health")
def health():
    return {"status": "ok", "height": len(blockchain.chain)}

class Transaction(BaseModel):
    user: str
    action: str
    file_id: str
    details: dict

@app.post("/tx")
def add_transaction(tx: Transaction):
    # Depending on implementation, add_transaction might return a block or T/F
    # Our ledger.py mines immediately
    new_block = blockchain.add_transaction(tx.dict())
    return {
        "status": "mined",
        "block_index": new_block.index,
        "block_hash": new_block.hash
    }

@app.get("/chain")
def get_chain():
    print("GET /chain called")
    return {
        "length": len(blockchain.chain),
        "chain": [b.__dict__ for b in blockchain.chain]
    }

@app.get("/validate")
def validate_chain():
    is_valid = blockchain.validate_chain()
    return {"is_valid": is_valid}

if __name__ == "__main__":
    import uvicorn
    print("Starting Blockchain Service on port 8006")
    uvicorn.run(app, host="0.0.0.0", port=8006)
