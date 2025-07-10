Below is a **Technical Specification Document** for the Gurumisha Motors platform. It drills into architecture, data model, APIs, security, deployment and operational concerns.

---

## 1. Introduction

**Purpose:**
Provide developers and DevOps engineers with all the low‑level details needed to build, test, deploy, and maintain the Gurumisha Motors digital platform.

**Scope:**

* Detailed component architecture
* Data model (tables, keys, relationships)
* REST API specifications
* Authentication & security
* Infrastructure & deployment
* Monitoring & maintenance

---

## 2. System Architecture

```mermaid
flowchart LR
  subgraph Frontend
    A[Next.js App] -->|API calls| B[Backend API]
  end
  subgraph Backend
    B --> C[(PostgreSQL)]
    B --> D[Strapi CMS]
    B --> E[AWS S3 Storage]
    B --> F[Redis Cache]
    B --> G[Messaging Queue (RabbitMQ)]
  end
  subgraph Integrations
    B --> H[WhatsApp API]
    B --> I[SMTP Email Service]
  end
```

* **Next.js (React + Tailwind):** SSR/ISR for SEO, PWA support
* **Backend:** Node.js (Express) or Django REST Framework
* **Database:** PostgreSQL
* **Cache:** Redis for session tokens & rate‑limiting
* **Storage:** AWS S3 for images/videos
* **CMS:** Strapi (headless) for blog/content
* **Queue:** RabbitMQ for background jobs (email, import‑status updates)

---

## 3. Data Model

### 3.1 Users & Roles

| Table   | Columns                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------- |
| users   | id (PK), email (unique), password\_hash, role (enum: customer, vendor, admin), created\_at, updated\_at |
| vendors | id (PK), user\_id (FK→users), company\_name, approved (bool), created\_at                               |

### 3.2 Cars & Imports

| Table            | Columns                                                                                                          |
| ---------------- | ---------------------------------------------------------------------------------------------------------------- |
| cars             | id, owner\_id (FK→users), title, make, model, year, price, status (pending/active/sold), created\_at             |
| import\_requests | id, user\_id (FK→users), specs\_json, estimated\_cost (decimal), status (pending/shipped/delivered), created\_at |

### 3.3 Spare Parts

| Table     | Columns                                                                                              |
| --------- | ---------------------------------------------------------------------------------------------------- |
| parts     | id, vendor\_id (FK→vendors), name, sku, compatibility\_json, price, stock, created\_at               |
| inquiries | id, user\_id (FK→users), part\_id (FK→parts), quantity, message, status (new/responded), created\_at |

### 3.4 Transactions & Logs

| Table        | Columns                                                           |                                  |
| ------------ | ----------------------------------------------------------------- | -------------------------------- |
| orders       | id, user\_id, total\_amount, payment\_method, status, created\_at |                                  |
| order\_items | id, order\_id (FK→orders), item\_type (car                        | part), item\_id, price, quantity |
| audit\_logs  | id, user\_id, action, resource\_type, resource\_id, timestamp     |                                  |

---

## 4. API Specification

> **Base URL:** `https://api.gurumishamotors.com/v1`

### 4.1 Authentication

* **POST /auth/register**

  * Body: `{ email, password, role }`
  * Response: `{ user: {...}, token }`

* **POST /auth/login**

  * Body: `{ email, password }`
  * Response: `{ user: {...}, token }`

* **GET /auth/me**

  * Headers: `Authorization: Bearer <token>`
  * Response: `{ user }`

### 4.2 Cars

* **GET /cars**

  * Query: `make, model, year, minPrice, maxPrice, status, page, limit`
  * Response: `{ data: [Car], pagination }`

* **POST /cars** (Vendor or Customer selling)

  * Headers: Auth
  * Body: `{ title, make, model, year, price, images[] }`
  * Response: `{ id, status: “pending” }`

* **PUT /cars/\:id/approve** (Admin only)

  * Headers: Auth (admin)
  * Response: `{ id, status: “active” }`

* **DELETE /cars/\:id**

  * Headers: Auth (owner or admin)
  * Response: `204 No Content`

### 4.3 Import Requests

* **POST /imports**

  * Headers: Auth
  * Body: `{ specs: { make, model, year, budget, originCountry } }`
  * Response: `{ id, estimated_cost, status: “pending” }`

* **GET /imports/\:id**

  * Headers: Auth
  * Response: `{ ...import_request }`

* **PUT /imports/\:id/status** (Vendor/Admin)

  * Body: `{ status }`
  * Response: `{ ...updated_request }`

### 4.4 Spare Parts

* **GET /parts**

  * Query: `vendorId, name, compatibility, page, limit`
  * Response: `{ data: [Part], pagination }`

* **POST /parts** (Vendor)

  * Body: `{ name, sku, compatibility: [...], price, stock }`
  * Response: `{ id }`

* **POST /inquiries**

  * Body: `{ partId, quantity, message }`
  * Response: `{ id, status: “new” }`

* **PUT /inquiries/\:id/respond** (Vendor/Admin)

  * Body: `{ responseMessage, status: “responded” }`
  * Response: `{ ...inquiry }`

---

## 5. Security & Compliance

* **Authentication:** JWT with refresh tokens stored as HTTP‑only cookies
* **Authorization:** RBAC (roles checked on each protected endpoint)
* **Input Validation:** Joi or Django serializers to prevent injection
* **Rate‑Limiting:** 100 req/min per IP via Redis
* **Data Protection:**

  * HTTPS/TLS everywhere
  * Passwords hashed with bcrypt (cost ≥ 12)
* **Vulnerability Scanning:** Periodic Snyk and Dependabot alerts

---

## 6. Infrastructure & Deployment

| Environment | Frontend                | Backend                | DB  | Cache       | Storage      | CI/CD                    |
| ----------- | ----------------------- | ---------------------- | --- | ----------- | ------------ | ------------------------ |
| Staging     | Vercel Preview          | Docker on DigitalOcean | RDS | Elasticache | S3 (staging) | GitHub Actions (staging) |
| Production  | Vercel (canary rollout) | EKS on AWS             | RDS | Elasticache | S3 (prod)    | GitHub Actions (prod)    |

* **Containers:** Docker images pushed to ECR
* **Orchestration:** Kubernetes (EKS) with Helm charts
* **CI/CD:**

  * Lint, tests, build → push to registry
  * Automated deployments to staging → manual approval for prod

---

## 7. Monitoring & Logging

* **Application Logs:** Winston/Logback → ELK Stack (Elasticsearch + Kibana)
* **Metrics:** Prometheus + Grafana dashboards (API latency, error rates)
* **Alerts:**

  * > 5xx errors spike → Slack alert
  * CPU/RAM > 80% → PagerDuty
* **Uptime:** Health checks on `/healthz` endpoint (returns 200 OK)

---

## 8. Testing Strategy

* **Unit Tests:** Mocha/Jest or PyTest (≥ 90% coverage)
* **Integration Tests:** Supertest or Django’s test client (API flows)
* **E2E Tests:** Cypress for critical user journeys (buy car, sell car, import)
* **Load Testing:** k6 scripts simulating 1,000 concurrent users

---

## 9. Roadmap & Future Enhancements

1. **Online Payments:** M‑Pesa integration + card checkout (Stripe)
2. **Mobile Apps:** React Native wrappers of web views
3. **AI Search Assistant:** Natural‑language car/part search
4. **Recommendation Engine:** Collaborative filtering for parts & cars
5. **ERP Integration:** Sync orders/inventory with accounting systems

---

> Next steps:
>
> 1. Review and sign off the API contract.
> 2. Begin database schema migration scripts.
> 3. Spin up staging infra and deploy minimal “Hello World” services.
> 4. Sprint plan for frontend & backend feature development.

Let me know if you’d like any section expanded (e.g. detailed sequence diagrams, full ERD image file, or CI/CD pipeline YAML templates).
