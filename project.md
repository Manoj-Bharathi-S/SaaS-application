# Project plan — modular, step-by-step, AI-agent friendly (very detailed)

Below is an **in-depth, modular breakdown** you can give to an AI agent (or follow yourself). Each module/phase is self-contained and testable, and modules can be coupled together incrementally. I’ve included **APIs, data schemas, test cases, acceptance criteria, minimal viable implementation (MVI)** and **optional enhancements** so the agent can build reliably without having to rewrite everything later.

---

# Overview & priorities

Goal: implement the system from your paper in small, verifiable modules:

1. **Encryption core** (AES + IBE + ABE wrappers)
2. **Proxy Re-Encryption** (single proxy → multiple proxies)
3. **Key Management (post-quantum wrapper)**
4. **Blockchain audit ledger** (simple private chain)
5. **ML anomaly detection** (synth dataset + Isolation Forest)
6. **RBAC/Access control + orchestration + UI**
7. **Integration, testing, performance & demo**

Build in that order — each phase has clear handoffs so later phases reuse earlier modules.

---

# Conventions for the AI agent

* Language: **Python 3.10+** (primary). Use **FastAPI** for microservices.
* Storage: **SQLite** for local dev (switchable to Postgres later).
* Containers: **Docker** optional; provide Dockerfile for each microservice.
* Repo structure: `services/{encryption,proxy,blockchain,ml,access,ui}`, `common/{schemas,utils}`, `tests/`.
* Communication: JSON over HTTP; internal services use REST.
* Auth: simple token header `X-API-Key` for internal calls (replaceable later).
* Logging: structured JSON logs to file.
* Tests: unit tests (pytest), integration tests (requests), and demo scripts.

---

# Module 0 — Bootstrap (Phase 0)

**Purpose:** create codebase skeleton, CI, and local dev environment.

**Deliverables**

* Monorepo structure
* `README.md` with run instructions
* `docker-compose.yml` with skeleton services
* Basic CI file (`.github/workflows/ci.yaml`) running tests and lint

**Acceptance**

* `docker-compose up` starts placeholder services that respond on health endpoint `/health` → `{"status":"ok"}`.

---

# Module 1 — Encryption Core (Phase 1)

**Purpose:** implement hybrid encryption primitives and wrappers: AES file encryption + wrappers for IBE/ABE (or mocks if full crypto library unavailable).

## Responsibilities / Components

1. **AES service**

   * API: `POST /encrypt` (body: `{ "plaintext": base64, "meta": {...} }`) → returns `{ "cipher": base64, "key_id": "<key-id>" }`
   * `POST /decrypt` (body: `{ "cipher": base64, "key_id": "<key-id>" }`) → returns `{ "plaintext": base64 }`
   * AES keys stored encrypted by Key Management (Module 3) or in memory for MVI.

2. **IBE/ABE wrappers**

   * For MVI you can implement simplified wrappers: store a mapping `{identity -> public_key}`, and implement `encrypt_key_with_ibe(key, id)` and `encrypt_key_with_abe(key, policy)` that return base64 blobs (can be symmetric key wrapped).
   * API endpoints for generating IBE/ABE-encrypted key blobs:

     * `POST /wrap_key/ibe` → `{ "key_id": "...", "identity": "user@example.com" }` → `{ "wrapped": base64 }`
     * `POST /wrap_key/abe` → `{ "key_id": "...", "policy": "role:manager" }`

## Data schemas

* AES response:

```json
{ "cipher_id":"c123", "cipher":"<base64>", "key_id":"k123" }
```

* Key wrap:

```json
{ "wrapped": "<base64>", "scheme": "ibe" }
```

## Tests & Acceptance

* Unit test: encrypt→decrypt returns original plaintext.
* Acceptance: CLI script `python demo_encrypt.py` that encrypts a sample file, wraps key for identity and policy, and outputs artifacts.

## MVI notes

* Use PyCryptodome for AES-GCM.
* IBE/ABE can be mocked initially; later replace with charm-crypto or lattice-based libs.

---

# Module 2 — Single Proxy Re-Encryption (Phase 1B)

**Purpose:** implement a proxy service that receives an encrypted AES key wrapped for one identity and re-encrypts it to another identity using a rekey (RK). For MVI, implement transformation that does NOT reveal AES key.

## API

* `POST /gen_rekey` (owner only) body: `{ "from": "idA", "to": "idB" }` → `{ "rekey_id": "rk123", "rk_blob": "..."}`
* `POST /reencrypt` body: `{ "ciphertext": "...", "rekey_id": "rk123" }` → `{ "ciphertext_re": "..." }`

## Data model

* Re-encryption entry:

```json
{ "rk_id":"rk123", "from":"idA", "to":"idB", "created_at":"..." }
```

## Tests

* Simulate: owner encrypts AES key for idA → send to proxy + rekey → proxy returns rewrapped blob for idB → idB can unwrap and access AES key (mock unwrap).

## Acceptance

* End-to-end demo where a Data Owner shares a file with User B via proxy re-encryption and User B can decrypt.

---

# Module 3 — Multi-Proxy and Load Balancer (Phase 2)

**Purpose:** scale single proxy to multiple instances with a lightweight load balancer and failover.

## Components

1. **Proxy instances** (identical service) run on different ports.
2. **Load balancer (round-robin)** service:

   * API `POST /reencrypt` forwards the request to next healthy proxy, aggregates success/fail metrics.
   * Health checking: `GET /health` on each proxy; maintain proxy pool.

## Data schemas

* Proxy pool config:

```json
{ "proxies": [ "http://localhost:5001", "http://localhost:5002" ] }
```

## Tests & Acceptance

* Start 3 proxies; run 100 re-encrypt requests; verify distribution across proxies (simple counter).
* Stop one proxy; LB continues with remaining proxies and logs an unhealthy event.

## Optional enhancements

* Weighted round-robin
* Retry policy with exponential backoff

---

# Module 4 — Key Management & Post-Quantum Wrapper (Phase 2B)

**Purpose:** manage keys and optionally integrate lattice-based encryption (MVI may use simplified wrapper).

## Components

* Key store (SQLite table): keys, key_id, owner, created_at, wrapped_by (ibe/abe/lattice)
* API:

  * `POST /generate_key?type=aes|lattice` → returns key_id
  * `POST /wrap_key` → wrap with IBE/ABE/Lattice (calls Module 1 wrappers or PQ library)
  * `GET /key/<key_id>` admin-only

## Tests & Acceptance

* Create AES key, wrap it with IBE, unwrap it using the right identity simulation.

## MVI approach

* For PQ you can provide a **wrapper** that calls a mock lattice library or uses an available LWE/LWE-like library if accessible; otherwise note a TODO with clear interface so the agent can later swap in a true lattice library.

---

# Module 5 — Blockchain Audit Ledger (Phase 3)

**Purpose:** implement private blockchain for immutable audit logs as in your paper.

## Minimal design (MVI)

* Simple Python chain with REST API:

  * `POST /tx` body `{ "type":"access","user":"U1","file":"F1","details":{...} }` → validate, compute tx hash, append new block
  * `GET /chain` → full chain
  * `GET /block/<index>` → single block

## Block schema

```json
{
  "index": 3,
  "timestamp": "2025-12-11T12:00:00Z",
  "transactions": [ {...}, {...} ],
  "prev_hash": "abc123",
  "hash": "def456",
  "nonce": 0
}
```

## Consensus

* MVI: single-node chain (no consensus) OR simple majority among N nodes (if you run multiple blockchain nodes with a trivial consensus algorithm).
* Option: implement simple Proof-of-Authority (PoA) or just sign transactions with node keys.

## API integration points

* Every major action (encrypt, re-encrypt, access, revoke, anomaly detected) must call `POST /tx` with event details.

## Tests & Acceptance

* Verify append-only: try to modify a block → subsequent hash mismatch detection.
* Demo: show audit trail for three events and verify integrity with recompute-hash script.

---

# Module 6 — ML Anomaly Detection (Phase 4)

**Purpose:** implement Isolation Forest pipeline, synthetic data generator, real-time scoring service and auto-revocation hook.

## Components

1. **Data generator** (`scripts/generate_logs.py`)

   * Generate labeled normal logs and injected anomalies.
   * Output CSV/SQLite table.

2. **Training pipeline**

   * `POST /train` (optional params: contamination)
   * Stores model artifact (`joblib`)

3. **Scoring API**

   * `POST /score` body `{ "features": { "hour": 23, "download_mb":500, ... } }` → `{ "score": -0.7, "is_anomaly": true }`
   * If `is_anomaly` true → call Access service `POST /revoke` and Blockchain `POST /tx`.

4. **Features to use**

   * `hour_of_day`, `download_mb`, `num_downloads_last_hour`, `failed_login_count`, `role_mismatch_flag`, `geolocation_distance_from_home`, `file_sensitivity_score`.

## Data schema (log row)

```json
{
 "timestamp":"2025-12-11T11:00:00Z",
 "user_id":"U12",
 "action":"download",
 "bytes": 123456,
 "hour": 11,
 "failed_logins": 0,
 "location":"India",
 "role":"analyst",
 "file_id":"file_1",
 "sensitivity": 3
}
```

## Tests & Acceptance

* Train on normal data (no anomalies), inject anomalies, compute classification accuracy and confusion matrix.
* Acceptance criteria (for paper demo): ML detects >80% of injected anomalies at low false positive rate (tune contamination). You may reproduce the paper’s table by choosing appropriate synthetic distributions.

## Integration

* On each logged event, call ML scoring service. If anomaly → call revoke API and write blockchain TX.

---

# Module 7 — Access Control (RBAC + ABE enforcement) (Phase 5)

**Purpose:** implement role/attribute store and enforcement API used by Data Owner and Proxy.

## Components

* RBAC store: Users, Roles, Permissions, Role assignments.
* Policy engine:

  * `POST /authorize` `{ "user":"U1","action":"download","file":"F1","context":{...} }` → `{ "allow": true/false, "reason": "..." }`
* Admin APIs to create roles and assign attributes.
* Integration: ABE wrapper will only produce keys if policy satisfied.

## Data schema (policy)

```json
{ "file_id":"F1", "required_roles": ["manager"], "min_sensitivity": 2 }
```

## Tests & Acceptance

* Create a manager role, assign user; test allow/deny scenarios, role change propagation.

---

# Module 8 — Orchestrator, UI & Demo Scripts (Phase 6)

**Purpose:** small web UI + orchestrator script to demo flows:

* Owner uploads file → encrypts with AES → wraps keys with IBE/ABE → store ciphertext in storage (local disk) → register event in blockchain
* Owner creates rekey for user → LB selects proxy → proxy re-encrypts → user downloads → ML checks behavior → blockchain logs
* Admin revokes user → rekey invalidated → blockchain logs

## UI

* Minimal React or plain HTML+JS
* Pages:

  * Dashboard (show chain, recent events)
  * Upload / Share
  * Users & Roles management
  * ML incidents list

## Demo scripts

* `demo_share_flow.sh` — automates a typical share and access.
* `demo_failover.sh` — stops one proxy and demonstrates failover.

## Acceptance

* Run `./demo_share_flow.sh` end-to-end and show logs, blockchain entries, and UI updates.

---

# Module 9 — Testing, Metrics & Verification

**Automated tests**

* Unit tests for each microservice (pytest)
* Integration tests invoking sequences across services
* ML tests: reproducible seed for data generator and deterministic model storage
* Blockchain integrity test: script that recomputes hashes and verifies chain.

**Performance metrics to record**

* Encryption/Decryption time (ms)
* Re-encryption time by proxy
* Blockchain logging latency
* ML scoring latency
* System behavior under X concurrent requests (simple load test using `locust` or `siege`)

*Note:* No time estimates — only record measured values.

---

# Module 10 — CI / DevOps (optional)

* Dockerfiles for each service
* `docker-compose.yml` to bring all services up
* CI job: lint + unit tests + build Docker images
* Optional: GitHub Actions to run integration tests on push

---

# Integration & Handoff rules (how to couple modules)

1. **APIs are the contract** — each module exposes REST endpoints listed above. The agent must produce OpenAPI (FastAPI auto-doc) for each service.
2. **Event bus = HTTP + blockchain writes** — any module that performs an important state change must call `POST /tx` on blockchain service with an event payload.
3. **Key IDs, cipher IDs, rekey IDs** are the shared identifiers across services.
4. **Model artifacts**: ML service stores `model.joblib` and the path is saved in DB for reproducible scoring.
5. **Logs**: centralized logs (JSON) optionally forwarded to a `logs/` folder or a lightweight log collector (file-based for MVI).

---

# Implementation checklist for the AI agent (stepwise tasks)

For each task, agent should:

1. Create service skeleton (FastAPI app with `/health`)
2. Implement core endpoints and data models
3. Write unit tests for each endpoint
4. Provide demo script for local manual verification
5. Add Dockerfile
6. Add integration test that calls the service from another service or from test harness

Do this **module by module** and run integration tests at the end of each phase.

---

# Example detailed build order with gating criteria (no time estimates)

* **Phase 0** — bootstrap + skeleton (gate: health checks pass)
* **Phase 1** — encryption core + single proxy + demo share (gate: encrypt/decrypt and proxy re-encrypt demo passed)
* **Phase 2** — multi-proxy + load balancer + key management (gate: LB distributes; failover works)
* **Phase 3** — blockchain audit + integration with Phase 1 events (gate: all major events are written to chain and integrity verified)
* **Phase 4** — ML pipeline + scoring + auto-revoke hook (gate: model trained, scores anomalies, triggers revoke logged in blockchain)
* **Phase 5** — RBAC & UI (gate: UI shows chain, users, and allows share/revoke flows)
* **Phase 6** — performance tests, docs, final demo scripts (gate: integration tests and demo scripts succeed)

---

# Example OpenAPI / Endpoint snippets (copy-paste friendly)

**Encryption service:**
`POST /encrypt` request:

```json
{
  "plaintext_b64": "SGVsbG8gV29ybGQ=",
  "meta": { "owner":"owner1", "file_id":"file_1" }
}
```

response:

```json
{ "cipher_id":"c1", "cipher_b64":"...", "key_id":"k1" }
```

**Proxy service:**
`POST /reencrypt`:

```json
{ "cipher_blob": "...", "rekey_id":"rk_1" }
```

response:

```json
{ "cipher_re": "..." }
```

**ML scoring service:**
`POST /score`:

```json
{ "features": {"hour":23,"download_mb":500,"failed_logins":5,"role_mismatch":1} }
```

response:

```json
{ "score": -0.84, "is_anomaly": true }
```

**Blockchain:**
`POST /tx`:

```json
{ "type":"access","user":"U1","file":"file_1","action":"download","details":{...} }
```

response:

```json
{ "block_index":4, "tx_hash":"..." }
```

---

# Synthetic data generator (detailed algorithm)

* Accept params: `n_normal`, `n_anom`, `seed`.
* For each normal user:

  * pick user_id ∈ [1..Nusers]
  * hour ∈ normal distribution around 10–17
  * download_mb ∈ log-normal small tail
  * failed_logins ∈ Poisson(0.2)
  * role_mismatch = 0
* For anomalies:

  * hour ∈ outside working hours (0–5 or 22–23)
  * download_mb ≫ normal (100–1000 MB)
  * failed_logins Poisson(5)
  * role_mismatch = occasionally 1
* Output CSV & insert into SQLite `activity_logs`.

---

# Demo scenarios to include in report & script

1. **Normal share:** Owner shares file → Proxy reencrypt → User downloads → blockchain entries show events.
2. **Anomalous access:** User downloads huge file off hours → ML flags → access revoked → blockchain shows revoke transaction.
3. **Proxy failover:** Stop proxy 2 → load balancer retries → other proxies handle re-encrypts → blockchain logs re-encrypt successes.
4. **Key revocation:** Owner revokes user → subsequent downloads denied.

---

# Deliverables the AI agent must produce

* Source repo with modules
* Unit & integration tests
* `docker-compose.yml` to bring system up
* Demo scripts for scenarios above
* README with running instructions
* Short report (2–3 pages) describing architecture, interfaces, and evaluation metrics
* Optional: PowerPoint with 8 slides for viva/demo

---

# Hints & pitfalls for the AI agent

* Keep interfaces small and well documented (OpenAPI). That allows swapping a mock with a real PQ library later.
* Make ML deterministic in tests (seed random PRNGs).
* Keep wrapping/unwrapping interfaces consistent: always use `key_id` and `wrapped_blob`.
* For blockchain: ensure append-only and provide a `validate_chain()` endpoint used in tests.
* Start with single-node implementations; only add distributed behavior (LB, multi-node blockchain) after core functionality is stable.

---

