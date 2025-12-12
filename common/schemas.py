from pydantic import BaseModel
from typing import Optional, Dict

class EncryptRequest(BaseModel):
    plaintext: str  # Base64 encoded
    meta: Optional[Dict[str, str]] = None

class EncryptResponse(BaseModel):
    cipher_id: str
    cipher: str     # Base64 encoded
    key_id: str

class DecryptRequest(BaseModel):
    cipher: str     # Base64 encoded
    key_id: str

class DecryptResponse(BaseModel):
    plaintext: str  # Base64 encoded

class ReKeyRequest(BaseModel):
    from_user: str
    to_user: str

class ReKeyResponse(BaseModel):
    rekey_id: str
    rk_blob: str

class ReEncryptRequest(BaseModel):
    cipher_blob: str
    rekey_id: str

class ReEncryptResponse(BaseModel):
    cipher_re: str
