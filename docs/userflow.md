## Userflow Design Specification: Gurumisha Motors Platform

Each userflow below includes: primary persona, entry point, navigation steps, interactions, decision points, and exit.

---

### 1. Car Buying Flow

* **Persona:** Customer
* **Entry:** Homepage > Car Search
* **Steps:**

  1. Select filters (make/model/year/price)
  2. View results
  3. Click car to open detail page
  4. Enquire or book test drive
* **Exit:** Inquiry confirmation or booking form submitted
* **Decisions:** Unauthenticated → login/signup prompt

---

### 2. Sell a Car Flow

* **Persona:** Seller (Vendor or Customer)
* **Entry:** Homepage > "Sell Your Car"
* **Steps:**

  1. Login/Register
  2. Upload images, input specs
  3. Set valuation
  4. Review summary
  5. Submit listing
* **Exit:** Confirmation of listing (pending admin approval)
* **Decisions:** Validation error prompts inline

---

### 3. Import Request Flow

* **Persona:** Customer
* **Entry:** Homepage > "Import a Car"
* **Steps:**

  1. Fill import spec form
  2. View cost estimate
  3. Confirm request
  4. Track request in dashboard
* **Exit:** Import tracker page with real-time updates
* **Decisions:** If country unsupported, show error prompt

---

### 4. Spare Parts Order Flow

* **Persona:** Customer
* **Entry:** Homepage > Spare Parts Catalog
* **Steps:**

  1. Filter by category/compatibility
  2. View part details
  3. Fill inquiry/order form
  4. Receive vendor response
* **Exit:** Ticket confirmation page
* **Decisions:** If out of stock → notify user

---

### 5. Customer Registration/Login Flow

* **Persona:** All users
* **Entry:** Top-right nav bar > Login/Register
* **Steps:**

  1. Choose role (buyer/vendor)
  2. Fill credentials and profile info
  3. Confirm email
* **Exit:** Redirect to user dashboard
* **Decisions:** Invalid credentials → error banner

---

### 6. Vendor Onboarding Flow

* **Persona:** Vendor
* **Entry:** Registration flow > Select Vendor
* **Steps:**

  1. Complete onboarding wizard (Company → Contacts → Docs)
  2. Submit application
  3. Await admin approval
* **Exit:** Status page (pending/approved)
* **Decisions:** Incomplete forms blocked

---

### 7. Admin Approval Flow

* **Persona:** Admin
* **Entry:** Admin Dashboard
* **Steps:**

  1. Review pending listings/imports/vendors
  2. Open item modal
  3. Approve/Reject (with optional comments)
* **Exit:** Confirmation message, list refreshed
* **Decisions:** Admin may request more info

---

### 8. Order Tracking Flow

* **Persona:** Customer/Vendor
* **Entry:** Dashboard > My Orders
* **Steps:**

  1. Select order
  2. View order details
  3. Track progress bar/status updates
* **Exit:** Reorder or review feedback button
* **Decisions:** If item delayed → display estimated date

---

### 9. Messaging & Inquiry Flow

* **Persona:** All Users
* **Entry:** Dashboard > Messages
* **Steps:**

  1. Select conversation
  2. View inquiry content
  3. Type and send message
* **Exit:** Real-time update to recipient inbox
* **Decisions:** Vendor may mark inquiry as resolved

---

### 10. CMS Blog Flow (Admin)

* **Persona:** Admin
* **Entry:** CMS Section
* **Steps:**

  1. Create or edit blog post
  2. Fill rich-text content, title, meta
  3. Save draft or publish
* **Exit:** Post listed on blog page
* **Decisions:** Unsaved changes → warning modal

---

### 11. Admin Dashboard Overview Flow

* **Persona:** Admin
* **Entry:** Admin login > Dashboard
* **Steps:**

  1. View KPIs (cars listed, vendors pending, inquiries)
  2. Drill into sections (e.g., approvals, logs)
* **Exit:** Navigates to another admin module

---

### 12. Customer Feedback Submission Flow

* **Persona:** Customer
* **Entry:** Post-purchase or order delivery
* **Steps:**

  1. Click "Leave Feedback"
  2. Fill rating + comments
  3. Submit
* **Exit:** Confirmation and thank you modal

---

### 13. Vendor Inventory Update Flow

* **Persona:** Vendor
* **Entry:** Dashboard > Inventory
* **Steps:**

  1. Click "Edit Stock"
  2. Adjust quantity or pricing
  3. Save changes
* **Exit:** Success toast, updated table

---

### 14. Notification Center Flow

* **Persona:** All Users
* **Entry:** Top bar > Bell Icon
* **Steps:**

  1. View list of notifications
  2. Click item to open linked page
* **Exit:** Return to notification list or related module

---

### 15. Logout/Session Expiry Flow

* **Persona:** All Users
* **Entry:** User inactivity or click logout
* **Steps:**

  1. Session timer detects idle OR click "Logout"
  2. Prompt or auto-logout
* **Exit:** Redirect to login page with notification

---

*Each userflow ensures clear feedback, visual cues, role-appropriate navigation, and an intuitive experience tailored to the platform’s core user groups.*
## Product Requirements Document (PRD): Gurumisha Motors Platform

### 1. Overview

**Product Name:** Gurumisha Motors Platform
**Prepared By:** Product Management Team
**Document Date:** 30 June 2025

**Objective:**
To design and deliver a modern, responsive, and AI-enhanced digital platform for customers to buy, sell, import cars and shop for spare parts, with advanced admin/vendor workflows for content moderation, inventory, analytics, and support.

---

### 2. Goals & Success Metrics

**2.1 Product Goals:**

* Enable customers to search, buy, and enquire about vehicles easily
* Allow sellers and vendors to post listings, manage inventory, and communicate with customers
* Simplify the car import request and tracking process
* Streamline admin oversight and approval workflows
* Enhance platform experience through responsive design and visual engagement

**2.2 Success Metrics:**

* > 5,000 monthly active users by Q4 2025
* 10% conversion rate from visitors to inquiries
* <2s average page load time
* > 90% satisfaction score from vendor and admin surveys
* 99.9% platform uptime

---

### 3. Features & Requirements

#### 3.1 Customer Features

* Browse cars with filtering (make, model, year, price, etc.)
* Detailed car view with specs, gallery, and contact/enquire CTA
* Book test drives
* Submit car import request and track status
* View spare parts catalog and send inquiries
* Register/login, manage profile, view orders/messages

#### 3.2 Vendor Features

* Register as a vendor with document verification
* Manage car listings (CRUD)
* Manage spare part inventory
* View and respond to inquiries/orders
* Access vendor dashboard with analytics

#### 3.3 Admin Features

* View/approve/reject car listings
* Approve vendor applications
* Monitor import requests and update statuses
* Access audit logs, user management, content CMS
* View platform analytics (users, traffic, listings)

#### 3.4 Shared Features

* Notification system (WhatsApp/email)
* Messaging center (chat-style)
* Secure authentication (JWT)
* Responsive UI (mobile/tablet/desktop)
* Accessibility and localization support

---

### 4. Technical Requirements

* **Frontend:** Next.js, Tailwind CSS, Framer Motion
* **Backend:** Node.js (Express) or Django REST API
* **Database:** PostgreSQL (hosted on AWS RDS)
* **Storage:** AWS S3 (media assets)
* **CI/CD:** GitHub Actions, Docker, Kubernetes (EKS)
* **Hosting:** Vercel (frontend), AWS EC2/EKS (backend)
* **Cache:** Redis (sessions, rate limit)
* **Monitoring:** Prometheus + Grafana, ELK Stack

---

### 5. User Stories & Acceptance Criteria

**As a Customer, I want to:**

* Search for cars so I can find a vehicle that fits my needs
* Enquire about a car so I can connect with the seller
* Track my car import status so I know when it will arrive

**Acceptance Criteria:**

* Car cards display filterable metadata
* Inquiry form sends email & stores in DB
* Tracker updates via WebSocket or polling

**As a Vendor, I want to:**

* List new inventory so customers can view my products
* Respond to part inquiries efficiently

**As an Admin, I want to:**

* Review listings before they go live to maintain quality
* Track user activity and approve vendor documents

---

### 6. Design Guidelines

* Follow UI Style & Animation System (see linked doc)
* Support black/white/red/dark blue color palette
* Modular component design with accessible markup
* Smooth transitions and microinteractions on forms/cards

---

### 7. Milestones & Timeline

| Phase                    | Timeline      | Deliverables                              |
| ------------------------ | ------------- | ----------------------------------------- |
| Discovery & Planning     | Jul 1–Jul 5   | Feature breakdown, tech stack, wireframes |
| Sprint 1 (Setup & Auth)  | Jul 6–Jul 19  | Login/signup, homepage, DB setup          |
| Sprint 2 (Cars)          | Jul 20–Aug 2  | Car browsing, search, filter, details     |
| Sprint 3 (Sell & Import) | Aug 3–Aug 16  | Sell car wizard, import request system    |
| Sprint 4 (Spare Parts)   | Aug 17–Aug 30 | Parts catalog, inquiry, vendor system     |
| Sprint 5 (Admin Panel)   | Sep 1–Sep 14  | Admin tools, analytics, approvals         |
| Final QA & Launch        | Sep 15–Sep 22 | Testing, performance, deployment          |

---

### 8. Assumptions & Constraints

* Users have access to mobile or desktop web browsers
* M-Pesa integration is scheduled for post-launch release
* Image-heavy listings require optimized CDN delivery

---

### 9. Out of Scope (MVP)

* Mobile apps (native)
* AI-powered recommendations
* Multi-language support beyond English

---

### 10. Risks & Mitigation

| Risk                               | Mitigation Strategy                              |
| ---------------------------------- | ------------------------------------------------ |
| Delays in vendor verification flow | Enable staged onboarding, allow partial access   |
| High image traffic affecting load  | Use CloudFront + compression                     |
| Poor adoption from vendors         | Run demo sessions, provide vendor onboarding kit |

---

*This PRD will be updated regularly as development progresses, with all changes communicated across product and engineering teams.*
