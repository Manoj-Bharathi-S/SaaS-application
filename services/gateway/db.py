import sqlite3
import uuid
import datetime

DB_PATH = "saas_gateway.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tenants Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            plan TEXT DEFAULT 'starter',
            api_key TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT
        )
    ''')
    
    # SaaS Users Table (Maps to Tenants)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            email TEXT UNIQUE,
            role TEXT DEFAULT 'user',
            password_hash TEXT,
            created_at TEXT,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_tenant(name: str, plan: str = 'starter') -> dict:
    tenant_id = f"t_{uuid.uuid4().hex[:8]}"
    api_key = f"sk_{uuid.uuid4().hex}"
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO tenants (id, name, plan, api_key, created_at) VALUES (?, ?, ?, ?, ?)",
        (tenant_id, name, plan, api_key, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    
    return {"id": tenant_id, "name": name, "plan": plan, "api_key": api_key}

def create_user(tenant_id: str, email: str, role: str = 'user') -> dict:
    user_id = f"u_{uuid.uuid4().hex[:8]}"
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (id, tenant_id, email, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, tenant_id, email, role, datetime.datetime.now().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return None # Duplicate email
    finally:
        conn.close()
        
    return {"id": user_id, "email": email, "tenant_id": tenant_id, "role": role}

def get_tenant_by_apikey(api_key: str):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tenants WHERE api_key = ?", (api_key,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None
