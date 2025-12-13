from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI(title="Access Control Service")
DB_PATH = "access.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Users: id, username, role, active
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, role TEXT, active INTEGER)''')
    # Roles: role, permissions (comma-separated actions)
    c.execute('''CREATE TABLE IF NOT EXISTS roles
                 (role TEXT PRIMARY KEY, permissions TEXT)''')
    
    # Check if admin exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES ('admin', 'admin', 1)")
        c.execute("INSERT INTO roles VALUES ('admin', 'decrypt,reencrypt,revoke')")
        c.execute("INSERT INTO roles VALUES ('user', 'decrypt')")
    
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

class AuthorizeRequest(BaseModel):
    user: str
    action: str # decrypt, reencrypt

@app.post("/authorize")
def authorize(req: AuthorizeRequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check user active
    c.execute("SELECT role, active FROM users WHERE username=?", (req.user,))
    row = c.fetchone()
    if not row:
        conn.close()
        return {"allow": False, "reason": "User not found"}
    
    role, active = row
    if not active:
        conn.close()
        return {"allow": False, "reason": "User is revoked"}
    
    # Check role permissions (Simple MVI)
    c.execute("SELECT permissions FROM roles WHERE role=?", (role,))
    role_row = c.fetchone()
    conn.close()
    
    if not role_row:
        return {"allow": False, "reason": "Role definition missing"}
    
    perms = role_row[0].split(',')
    if req.action in perms or "all" in perms:
        return {"allow": True}
    
    return {"allow": False, "reason": "Insufficient permissions"}

class UserRequest(BaseModel):
    username: str
    role: str = "user"

@app.post("/users")
def create_user(req: UserRequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, 1)", (req.username, req.role))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="User exists")
    conn.close()
    return {"status": "created", "username": req.username}

class RevokeRequest(BaseModel):
    username: str

@app.post("/revoke")
def revoke_user(req: RevokeRequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET active=0 WHERE username=?", (req.username,))
    conn.commit()
    conn.close()
    return {"status": "revoked", "username": req.username}

if __name__ == "__main__":
    import uvicorn
    print("Starting Access Service on port 8008")
    uvicorn.run(app, host="0.0.0.0", port=8008)
