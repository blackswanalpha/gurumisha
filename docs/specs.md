## Specification Design Document: Gurumisha Motors Platform

### 1. Introduction

**1.1 Purpose**
This Specification Design Document outlines detailed functional and non‑functional requirements, interface specifications, data structures, UI/UX guidelines, performance benchmarks, and deliverables for the Gurumisha Motors digital platform.

**1.2 Audience**

* Product Owners
* Development Team
* QA Engineers
* UX/UI Designers
* DevOps Engineers

**1.3 Scope**
Covers system modules for car sales, import tracking, spare parts shop, vendor/admin panels, customer-facing features, plus integration points and deployment specifics.

---

### 5. UI/UX Component Specifications

The UI design philosophy follows a clean, responsive, modern aesthetic using **Tailwind CSS** with attention-grabbing visuals and smooth animations to enhance usability and attention retention.

#### 5.1 Design Principles

* **Modern & Sleek**: Use of glassmorphism effects on modals and cards with soft shadows and large padding.
* **Interactive**: Transitions on hover/click for all interactive elements.
* **Emotionally Engaging**: Carousels, 360-degree vehicle views, and testimonial sliders.
* **Visual Hierarchy**: Color-coded CTAs (primary = green, secondary = dark blue), subtle gradients.
* **Microinteractions**: Button ripple effects, form field highlights, loader animations.

#### 5.2 Animation & Transition Patterns

* **Global Navigation Bar**: Sticky + shadow on scroll; fade-in submenus.
* **Car Cards**: Hover-scale animation with smooth easing-in (0.3s), badge reveal transitions.
* **Modal Windows**: Slide-in from bottom with spring bounce (framer-motion or Tailwind plugin).
* **Forms**: Step-by-step transitions, fade effects on error/success states.
* **Status Steppers**: Animated progress bars, vertical dots animate on completion (e.g., tracking import).

#### 5.3 Responsive Layout Guidelines

* **Breakpoints**:

  * Mobile: 1-column
  * Tablet: 2-column
  * Desktop: 3–4 column grids

* **Sticky Elements**: Filters on product pages, bottom nav bar for mobile.

#### 5.4 Color and Typography

* **Primary Color Palette**: Emerald Green (#10B981), Charcoal (#1F2937), Snow White (#F9FAFB)
* **Fonts**: Inter and DM Sans (with 600–700 weights for headlines)
* **UI Colors**: Soft yellow highlights for stock alerts, success (green), warning (orange), danger (red).

#### 5.5 High-Impact UI Sections

* **Hero Section (Homepage)**:

  * Animated car showcase carousel
  * Search bar with smooth dropdown transitions
  * Animated stats counters (cars listed, sold, imported)

* **Import Tracker**:

  * Visual vertical stepper with transitions on step change
  * Real-time WebSocket update animation with pulsing indicator

* **Admin Dashboard**:

  * Card widgets with animated KPI numbers
  * Notifications panel slides from right
  * Real-time list refresh with shimmer loading effect

---

All animations should follow performance best practices, limited to **transform** and **opacity** for GPU acceleration. Transitions use a default `ease-in-out` with a 250–400ms duration.

Interactive prototypes should be implemented using **Framer Motion** (React) or equivalent transition libraries.

---

*This design ensures a highly engaging and modern experience for all user roles while remaining performant, accessible, and brand-aligned.*
