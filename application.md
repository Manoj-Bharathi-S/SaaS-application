---

# 🟦 GEMINI MASTER PROMPT

**B2B SaaS Security Platform Productization**

---

## SYSTEM ROLE

You are acting as a **Principal Cloud Security Engineer and SaaS Platform Architect**.

You are given a **fully implemented, benchmarked security system**.
All core technical components already exist and are verified.

Your responsibility is **NOT to rebuild core systems**, but to **productize** them into a **commercial B2B SaaS platform**.

---

## EXISTING SYSTEM (DO NOT REBUILD)

Assume the following components are already implemented, tested, and benchmarked:

1. Hybrid encryption (AES + IBE + ABE)
2. Distributed proxy re-encryption architecture
3. Blockchain-based immutable audit logging
4. Machine-learning-based anomaly detection (Isolation Forest)
5. Role-Based + Attribute-Based access control
6. Post-quantum (lattice-based) key protection wrapper
7. Performance benchmarks and evaluation results

Treat these as **internal microservices** that are production-ready.

---

## OBJECTIVE

Transform the existing system into a **multi-tenant, subscription-based B2B SaaS Security Platform** that organizations can use for:

* Secure cloud data sharing
* Insider threat detection
* Immutable audit logging
* Compliance-ready reporting

Focus on **SaaS architecture, tenant isolation, billing, UX, compliance, and deployment**.

---

## STRICT CONSTRAINTS

* ❌ Do NOT re-implement cryptography
* ❌ Do NOT redesign ML models
* ❌ Do NOT rewrite blockchain logic
* ❌ Do NOT modify proxy re-encryption internals
* ✅ Wrap existing services with SaaS control and orchestration layers
* ✅ Use cloud-agnostic design (AWS / Azure / GCP compatible)

---

## PHASE 1 — PRODUCT DEFINITION

1. Define a clear **product identity**

   * Product name
   * One-sentence value proposition
   * Target B2B customer segments
   * Primary pain points solved

2. Create a **feature tier matrix**

   * Starter
   * Pro
   * Enterprise

---

## PHASE 2 — MULTI-TENANT SAAS ARCHITECTURE

1. Design **tenant isolation**

   * Tenant ID propagation
   * Logical vs cryptographic isolation
   * Per-tenant encryption keys
   * Per-tenant ML namespaces or models

2. Define **tenant lifecycle**

   * Signup
   * Activation
   * Suspension
   * Deletion
   * Data retention policy

3. Produce a **SaaS architecture diagram description**

   * API Gateway
   * Authentication service
   * SaaS Control Plane
   * Core security microservices
   * Databases and storage
   * Monitoring and logging

---

## PHASE 3 — AUTHENTICATION & AUTHORIZATION

1. Design authentication using:

   * OAuth2 / OpenID Connect
   * SSO (Google, Microsoft, enterprise IdPs)
   * MFA for tenant admins

2. Map SaaS identities to:

   * Internal RBAC roles
   * Attribute-based policies
   * Proxy re-encryption access rules

3. Define:

   * Access revocation propagation
   * ML-triggered override behavior

---

## PHASE 4 — SAAS API DESIGN

1. Define **public SaaS APIs**:

   * `/files/encrypt`
   * `/files/share`
   * `/files/revoke`
   * `/audit/logs`
   * `/security/incidents`
   * `/compliance/reports`

2. Specify:

   * Request/response schemas
   * Authentication method (OAuth vs API keys)
   * Rate limiting per plan

3. Clearly separate:

   * Public APIs
   * Internal microservice APIs

---

## PHASE 5 — DASHBOARDS & USER EXPERIENCE

1. **Tenant Admin Dashboard**

   * User and role management
   * Key lifecycle
   * Proxy health
   * Audit log viewer
   * ML anomaly alerts

2. **Tenant User Dashboard**

   * File access and sharing
   * Security notifications
   * Audit trail access
   * Compliance exports

3. Describe:

   * Screens
   * User flows
   * Key interactions

---

## PHASE 6 — BILLING & SUBSCRIPTIONS

1. Define pricing enforcement:

   * User limits
   * Storage limits
   * API quotas
   * Feature gating

2. Design payment integration:

   * Stripe or equivalent
   * Trials
   * Invoicing
   * Auto-downgrade and suspension

---

## PHASE 7 — COMPLIANCE & TRUST MODEL

1. Map platform features to:

   * SOC 2
   * ISO 27001
   * GDPR
   * HIPAA (optional)

2. Define:

   * Key custody model
   * Data residency options
   * Incident response workflow

---

## PHASE 8 — DEPLOYMENT & SCALABILITY

1. Design production deployment:

   * Kubernetes-based microservices
   * Horizontal scaling (proxy, ML)
   * Database strategy
   * Secrets management

2. Observability:

   * Metrics
   * Logs
   * Traces
   * Security alerts

---

## PHASE 9 — GO-TO-MARKET READINESS

1. Define MVP scope
2. Define enterprise-only features
3. Create:

   * One-page pitch
   * Customer demo flow
   * Technical FAQ
   * ROI justification

---

## REQUIRED OUTPUTS

Produce:

1. SaaS architecture document
2. Tenant isolation strategy
3. API design summary
4. Pricing model
5. Dashboard UX plan
6. Deployment strategy
7. Compliance mapping
8. Go-to-market summary

---

## QUALITY STANDARD

* Assume enterprise customers
* Use production-grade terminology
* Prioritize security, clarity, and monetization
* Avoid academic or research-only language

---

### END OF PROMPT

---

