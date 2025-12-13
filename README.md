# Secure Cloud Storage with Proxy Re-Encryption & AI Audit

## Overview
This system implements a secure file sharing architecture using **Proxy Re-Encryption (PRE)**, allowing users to share encrypted files without revealing plaintexts to the server. It includes **Blockchain Auditing** for tamper-evident logs and an **AI/ML Anomaly Detection** system to flag suspicious access patterns.

## Features
- **Zero-Knowledge Sharing**: Files are encrypted with AES + PRE. The proxy transforms ciphertexts for recipients without seeing the data.
- **Robust Security**: Hybrid encryption scheme (AES-GCM + PRE/Key Wrapping).
- **Auditability**: All critical actions (Encrypt, Share, Download) are logged to a local Blockchain.
- **AI Defense**: Isolation Forest model detects anomalies (e.g., unusual download times or sizes) and triggers automatic revocation.
- **Access Control**: RBAC system to enforce permissions.
- **High Availability**: Load Balancer distributes requests across multiple proxies.

## Components
| Service | Port | Description |
|---------|------|-------------|
| **Encryption** | 8001 | Encrypts/Decrypts files, manages wrapping. |
| **Proxy** | 8003/4 | Performs re-encryption transformation. |
| **Load Balancer** | 8002 | Distributes requests to proxies. |
| **KMS** | 8005 | Manages encryption keys. |
| **Blockchain** | 8006 | Immutable audit ledger. |
| **ML Service** | 8007 | Anomaly detection engine. |
| **Access** | 8008 | RBAC and Policy enforcement. |
| **Dashboard** | 8501 | Web UI for user interaction. |

## Prerequisites
- Python 3.9+
- `pip` or `uv`

## Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Start the System
Launch the interactive dashboard and all backend services:
```bash
python demos/start_dashboard.py
```
Open **http://localhost:8501** in your browser.

### 2. Run Verification Tests
To verify individual components or phases:
```bash
# Verify Phase 4 (ML)
python demos/run_phase4_verification.py

# Verify Phase 5 (RBAC)
python demos/run_phase5_verification.py
```

### 3. Performance Benchmarks
To measure system latency (requires running services):
```bash
python tests/performance_test.py
```

## Architecture Flow
1. **Alice** encrypts file -> KMS generates key -> Key wrapped for Alice.
2. **Alice** shares with **Bob** -> Proxy generates Re-Encryption Key (RK).
3. **Bob** requests file -> Proxy uses RK to transform ciphertext -> Bob decrypts with his key.
4. **ML Service** monitors metadata -> Flags anomalies -> Automates revocation.

