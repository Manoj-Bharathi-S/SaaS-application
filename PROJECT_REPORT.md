# Secure Cloud Storage: Project Report

## 1. Executive Summary
This project delivers a secure, scalable cloud storage system enabling **end-to-end encrypted sharing**. Unlike traditional systems where the server holds decryption keys, this architecture uses **Proxy Re-Encryption (PRE)** to facilitate sharing without exposing plaintext. Integrated **Blockchain Auditing** ensures accountability, while **ML-based Anomaly Detection** provides proactive threat mitigation.

## 2. Architecture Design
The system relies on a microservices architecture:

### 2.1 Core Services
- **Encryption Service**: Handles AES-GCM encryption. Keys are never stored locally by the user but fetched securely from KMS.
- **Key Management Service (KMS)**: Centralized, secure storage for keys. In a production environment, this would be backed by an HSM. It supports "Key Wrapping" to cryptographically bind keys to user identities.
- **Proxy Service**: The heart of the sharing capability. It uses a re-encryption key ($rk_{A \to B}$) to convert ciphertext from Alice's key to Bob's key. **Critically, the proxy cannot decrypt the data.**

### 2.2 Security & Compliance
- **Blockchain Service**: A SHA-256 linked ledger records every `Encrypt`, `Re-Encrypt`, and `Revoke` event. This provides a non-repudiatable audit trail.
- **Access Control (RBAC)**: A dedicated service enforces role-based policies (e.g., "Only Admin can revoke").

### 2.3 AI Security Layer
- **ML Service**: An `IsolationForest` model (Scikit-Learn) analyzes access patterns (Time of Day, Data Size, Frequency).
- **Automatic Response**: If an anomaly is detected (e.g., 500MB download at 3 AM), the system proactively calls the Access Service to **revoke** the user's permissions immediately.

## 3. Technology Stack
- **Backend Framework**: FastAPI (High performance, async).
- **Cryptography**: PyCryptodome (AES-GCM).
- **Database**: SQLite (MVI for state persistence).
- **ML**: Scikit-Learn, Pandas.
- **UI**: Streamlit (Responsive web dashboard).

## 4. Evaluation & Metrics
(Measured on local test environment, average over 20 iterations)
- **Encryption Latency**: ~6.1 seconds/op. (High due to synchronous KMS key generation and local network overhead).
- **Re-Encryption Overhead**: ~4.5 seconds/op. (Includes ~2s ML anomaly check latency).
- **ML Latency**: ~2.0 seconds/req. (Scoring overhead + HTTP latency).
- **Scalability**: The system successfully handles sequential requests, though latency optimization (optimizing KMS roundtrips and async ML calls) is a recommended future improvement.

## 5. Conclusion
The implemented system successfully balances **usability** (web dashboard, seamless sharing) with **hardened security** (PRE, Blockchain, AI). It meets all functional requirements for a modern, secure cloud storage prototype.
