## System Design Document: Gurumisha Motors Platform

### 1. Overview

The Gurumisha Motors platform is a modular, scalable, cloud-native system designed to support vehicle listing, importing, selling, spare parts management, and admin/vendor workflows. The system supports multi-role access, responsive UI/UX, real-time tracking, and integrates with cloud services for performance and reliability.

---

### 2. System Architecture

#### 2.1 High-Level Architecture

* **Frontend**: Next.js (React), TailwindCSS, Framer Motion
* **Backend API**: Node.js (Express) or Django REST Framework
* **Database**: PostgreSQL (RDS)
* **Storage**: AWS S3 for images/docs
* **Cache**: Redis for sessions, rate limiting, and caching
* **Messaging**: WebSocket/Socket.IO for real-time updates
* **CI/CD**: GitHub Actions, Docker, Kubernetes (EKS)
* **Monitoring**: Prometheus, Grafana, CloudWatch Logs

---

### 3. Modules & Subsystems

#### 3.1 User Management

* Roles: Customer, Vendor, Admin
* Features: Registration, login, JWT auth, profile management

#### 3.2 Car Listings

* CRUD operations for cars
* Search & filters: make, model, year, price, etc.
* Admin approval pipeline

#### 3.3 Import System

* Import request form
* Cost engine integration
* Real-time tracking
* Admin-controlled status updates

#### 3.4 Spare Parts System

* Vendor managed inventory (CRUD)
* Customer inquiries per part
* Inquiry tracking and vendor replies

#### 3.5 Admin Panel

* Approvals: cars, imports, vendors
* CMS: blog posts, static content
* Analytics dashboard (charts, KPIs)
* User & vendor management

#### 3.6 Messaging

* Customer-vendor chat for inquiries
* Notification system (real-time + email/WhatsApp)

#### 3.7 File Management

* Uploads: car images, documents
* AWS S3 file storage + metadata tracking

---

### 4. Database Design

#### Core Tables

* Users
* Cars
* Imports
* Vendors
* Parts
* Inquiries
* Orders
* Messages
* AuditLogs

---

### 5. API Design (RESTful)

#### Key Endpoints

* `/auth/register`, `/auth/login`, `/auth/me`
* `/cars`, `/cars/:id`, `/cars/:id/approve`
* `/imports`, `/imports/:id/status`
* `/parts`, `/inquiries`
* `/vendors`, `/vendors/:id/verify`

---

### 6. Security

* JWT Auth (access + refresh tokens)
* HTTPS enforced
* Rate limiting via Redis
* File validation for uploads
* RBAC enforcement for admin/vendor/customer roles
* Audit logging of all sensitive actions

---

### 7. Performance Optimization

* Caching: Redis for listing pages
* Lazy loading of images
* Pagination on large datasets
* Background workers for heavy jobs (e.g., image resizing)

---

### 8. Scalability & Reliability

* Auto-scaling with Kubernetes HPA
* Database read replicas
* CDN for static assets (AWS CloudFront)
* Health checks and retry logic

---

### 9. DevOps & Deployment

* Dockerized services
* GitHub Actions for CI
* EKS for deployment
* Versioned release tags
* Canary/staged rollouts

---

### 10. Monitoring & Logging

* Prometheus metrics
* Grafana dashboards
* ELK Stack for logs
* Alerting via Slack/Email

---

*This system design ensures maintainability, modularity, and scalability with security and performance best practices for Gurumisha Motors.*
