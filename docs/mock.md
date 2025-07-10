# Gurumisha Motors - Mock UI Pages Design Document
*Comprehensive Design Specifications for 55+ Pages*

---

## Table of Contents
1. [Design System Overview](#design-system-overview)
2. [Global Components](#global-components)
3. [Core User Pages](#core-user-pages)
4. [Vendor Management Pages](#vendor-management-pages)
5. [Administrative Pages](#administrative-pages)
6. [Specialized Features](#specialized-features)

---

## Design System Overview

### Color Tokens Implementation
```css
:root {
  /* Primary Palette */
  --midnight-black: #0A0A0A;
  --pure-white: #FFFFFF;
  --carbon-gray: #1A1A1A;
  --crimson-red: #DC2626;
  --electric-red: #EF4444;
  --deep-ocean: #1E3A8A;
  --azure-blue: #3B82F6;
  
  /* Extended Gray Scale */
  --gray-50: #F9FAFB;
  --gray-100: #F3F4F6;
  --gray-200: #E5E7EB;
  --gray-300: #D1D5DB;
  --gray-400: #9CA3AF;
  --gray-500: #6B7280;
  --gray-600: #4B5563;
  --gray-700: #374151;
  --gray-800: #1F2937;
  --gray-900: #111827;
}
```

### Typography Scale
- **Display**: 64px/48px (Desktop/Mobile) - Hero headlines
- **H1**: 48px/36px - Page titles
- **H2**: 36px/28px - Section headers
- **H3**: 28px/24px - Subsections
- **H4**: 24px/20px - Card titles
- **Body**: 16px/14px - Default text
- **Caption**: 12px/11px - Labels and metadata

---

## Global Components

### Header Navigation
**Layout**: Sticky positioned with glassmorphism backdrop
**Components**:
- **Logo Section** (Left)
  - Gurumisha Motors wordmark with automotive icon
  - Size: 180px x 40px
  - Color: Gradient from crimson-red to deep-ocean
- **Navigation Menu** (Center)
  - Items: Cars | Import | Sell | Parts | Blog | Contact
  - Font: DM Sans 16px, weight 500
  - Hover: Electric-red underline animation
- **User Actions** (Right)
  - Search icon button with expand animation
  - User avatar dropdown or Login/Register buttons
  - Shopping cart icon with item count badge

**Mobile Behavior**: Hamburger menu with slide-out drawer

### Footer Component
**Layout**: Dark background (carbon-gray) with 4-column grid
**Sections**:
1. **Company Info**: Logo, tagline, social links
2. **Quick Links**: Popular categories and pages
3. **Customer Service**: Support links and contact info
4. **Newsletter**: Email signup with gradient button

---

## Core User Pages

### Page 1: Homepage

#### Hero Section
**Layout**: Full viewport height with background video/image
**Components**:
- **Hero Overlay**: Semi-transparent gradient (midnight-black to transparent)
- **Main Headline**: "Find Your Perfect Vehicle" (Display typography)
- **Subheadline**: Premium automotive marketplace tagline
- **Search Widget**: 
  - Multi-step search form (Make → Model → Year)
  - Dropdown animations with smooth transitions
  - Primary CTA: "Search Cars" button with hover lift effect

#### Quick Action Cards
**Layout**: 3-column grid below hero
**Cards**:
1. **Import a Car**
   - Icon: Globe with car silhouette
   - Background: Gradient blue overlay
   - Hover: Scale and shadow increase
2. **Sell Your Car**
   - Icon: Dollar sign with car
   - Background: Gradient red overlay
   - Interactive elements with micro-animations
3. **Spare Parts**
   - Icon: Gear with wrench
   - Background: Gradient gray overlay
   - Subtle glow effects on hover

#### Featured Cars Section
**Layout**: Horizontal scrolling carousel
**Car Cards**:
- **Dimensions**: 320px width x 280px height
- **Image Area**: 16:9 aspect ratio with overlay gradient
- **Content Overlay**:
  - Car title (H4 typography)
  - Price with currency formatting
  - Key specs (Year, Mileage, Fuel type)
  - Status badge (Available/Featured/Sold)
- **Interactions**: 
  - Hover: Image zoom, card lift
  - Click: Smooth transition to details page

#### Testimonials Section
**Layout**: 2-column masonry grid
**Testimonial Cards**:
- **Avatar**: Circular profile image (64px)
- **Quote**: Italic text with quotation marks
- **Attribution**: Name and title
- **Rating**: 5-star display with filled/empty states
- **Animation**: Staggered fade-in on scroll

### Page 2: Car Search Results

#### Filter Sidebar (25% width)
**Layout**: Sticky positioned with accordion panels
**Filter Categories**:
1. **Make & Model**
   - Nested dropdown with search
   - Selected items as removable chips
2. **Price Range**
   - Dual-handle slider with live values
   - Quick preset buttons (Under 1M, 1-3M, 3M+)
3. **Vehicle Details**
   - Year: Range slider
   - Mileage: Input with km/miles toggle
   - Fuel Type: Checkbox grid with icons
   - Transmission: Radio buttons with descriptions
4. **Features**
   - Checkbox list with feature icons
   - "Show more" expandable section

#### Results Grid (75% width)
**Layout**: Responsive grid (3-2-1 columns for desktop-tablet-mobile)
**Car Cards Enhanced**:
- **Image Gallery**: Multiple images with dots indicator
- **Quick Actions**: Heart icon (save), compare checkbox, share button
- **Status Indicators**: Color-coded availability badges
- **Hover State**: Additional details overlay
- **Loading States**: Skeleton placeholders during search

#### Results Controls
**Top Bar**:
- Results count with loading animation
- Sort dropdown (Price, Year, Mileage, Relevance)
- View toggle (Grid/List/Map)
- Filter summary with clear-all option

**Pagination**:
- Page numbers with ellipsis for large result sets
- Previous/Next with keyboard navigation
- "Load More" infinite scroll option

### Page 3: Car Details

#### Image Gallery Section (60% width)
**Main Image**:
- **Dimensions**: 800px x 500px viewport
- **Controls**: Zoom functionality, fullscreen mode
- **Overlay**: Image counter (1/15), expand icon

**Thumbnail Strip**:
- **Layout**: Horizontal scroll with 6 visible thumbnails
- **Interactions**: Click to change main image, keyboard navigation
- **Indicator**: Active thumbnail with border highlight

#### Details Panel (40% width)
**Header Section**:
- **Title**: Car make, model, year (H1 typography)
- **Price**: Large, prominent with currency
- **Status Badge**: Colored indicator with icon

**Specifications Table**:
- **Rows**: Year, Mileage, Engine, Transmission, Fuel Type, Color
- **Styling**: Alternating row colors, clear typography
- **Icons**: Category icons for each specification type

**Features Grid**:
- **Layout**: 2-column grid of feature badges
- **Badges**: Icon + text, color-coded by category
- **Interaction**: Hover for feature descriptions

**Action Buttons**:
- **Primary**: "Enquire Now" (Full width, crimson-red)
- **Secondary**: "Book Test Drive" (Outline style)
- **Tertiary**: Save, Share, Compare icons

#### Additional Sections
**Financing Calculator**:
- **Widget**: Collapsible panel with loan calculator
- **Inputs**: Down payment, loan term, interest rate
- **Output**: Monthly payment with breakdown

**Similar Cars**:
- **Layout**: Horizontal carousel
- **Cards**: Simplified version of search result cards

### Page 4: Book Test Drive Modal

#### Modal Structure
**Backdrop**: Semi-transparent overlay with blur effect
**Container**: Centered modal with rounded corners and shadow

**Header**:
- **Title**: "Book a Test Drive" (H2 typography)
- **Close Button**: X icon with hover state
- **Car Summary**: Small car image and basic details

**Form Section**:
- **Date Picker**: Calendar widget with available dates highlighted
- **Time Slots**: Grid of available time buttons
- **Personal Info**: Pre-filled inputs (Name, Phone, Email)
- **Special Requests**: Textarea for additional notes

**Footer**:
- **Cancel Button**: Secondary style, left-aligned
- **Confirm Button**: Primary style, right-aligned
- **Loading State**: Spinner overlay during submission

### Page 5: Sell Your Car Wizard

#### Progress Stepper
**Layout**: Horizontal stepper with 4 steps
**Steps**: Images → Details → Valuation → Review
**Visual**: Connected dots with progress line, active step highlighted

#### Step 1: Images Upload
**Upload Area**:
- **Drag & Drop Zone**: Large, dashed border area
- **Instructions**: Clear typography with supported formats
- **Multiple Upload**: Support for up to 8 images

**Preview Grid**:
- **Thumbnails**: 120px x 120px with remove button overlay
- **Main Preview**: Larger preview of selected image
- **Reorder**: Drag and drop functionality

#### Step 2: Vehicle Details
**Form Layout**: Two-column grid for desktop, single column mobile

**Vehicle Information**:
- **Make/Model/Year**: Cascading dropdowns with search
- **Mileage**: Number input with km indicator
- **Condition**: Radio buttons with descriptions
- **Price**: Large number input with currency

**Description**:
- **Rich Text Editor**: Formatting toolbar, character counter
- **Template Options**: Quick-fill buttons for common descriptions

#### Step 3: Valuation
**Market Analysis**:
- **Price Suggestion**: Algorithm-based price recommendation
- **Range Slider**: Adjust price within suggested range
- **Market Data**: Comparison with similar vehicles

**Negotiation Settings**:
- **Toggle**: Accept offers vs fixed price
- **Minimum Price**: If offers enabled

#### Step 4: Review & Submit
**Summary Card**:
- **Images**: Thumbnail carousel
- **Details**: All entered information in formatted layout
- **Edit Icons**: Quick edit buttons for each section

**Terms & Conditions**:
- **Checkbox**: Agreement to terms
- **Link**: Modal or expandable terms text

### Page 6: Sell Confirmation

#### Success State
**Icon**: Large animated checkmark with success color
**Heading**: "Listing Submitted Successfully!" (H1)
**Message**: Explanation of next steps and timeline
**Actions**: 
- **Primary**: "View My Listings" button
- **Secondary**: "Add Another Car" link

#### Information Panel
**Listing Details**:
- **ID**: Generated listing reference number
- **Status**: "Under Review" with expected timeline
- **Contact**: Support information for questions

---

## Advanced Feature Pages

### Page 7-8: Import Car Process

#### Import Request Form
**Step Indicator**: 3-step process visualization

**Vehicle Specifications**:
- **Origin Country**: Interactive map or dropdown
- **Make/Model**: Searchable dropdowns with popular imports
- **Budget Range**: Slider with currency conversion
- **Special Requirements**: Checkbox list and text area

#### Cost Estimate Display
**Breakdown Table**:
- **Vehicle Cost**: Base price estimate
- **Shipping**: Ocean freight calculation
- **Import Duties**: Tax calculations by country
- **Processing Fees**: Administrative costs
- **Total**: Large, highlighted final amount

**Interactive Elements**:
- **Currency Toggle**: Switch between KES/USD
- **Sensitivity Analysis**: Sliders showing cost variations
- **Financing Options**: Available loan products

### Page 9-10: Import Tracking

#### Dashboard View
**Summary Cards**:
- **Active Imports**: Count with status breakdown
- **Pending Requests**: Items awaiting approval
- **Completed**: Delivered vehicles count

**Recent Activity**:
- **Timeline**: Chronological list of updates
- **Notifications**: Important status changes

#### Detailed Tracking
**Progress Stepper**: Vertical timeline with detailed steps
- **Request Submitted**: Timestamp and confirmation
- **Sourcing**: Finding suitable vehicles
- **Purchase**: Vehicle acquired and paperwork
- **Shipping**: Port departure and estimated arrival
- **Customs**: Clearance process and documentation
- **Delivery**: Final delivery arrangements

**Map Integration**:
- **Route Visualization**: Shipping route on world map
- **Current Location**: Real-time vessel tracking (when available)

---

## Vendor Management Section

### Page 36: Vendor Dashboard Home

#### KPI Cards (4-column grid)
1. **Total Listings**
   - **Value**: Large number with trend indicator
   - **Trend**: Up/down arrow with percentage change
   - **Timeframe**: "vs last month" comparison

2. **Active Orders**
   - **Value**: Current order count
   - **Status Breakdown**: Quick pie chart or progress rings
   - **Quick Action**: "View All Orders" link

3. **Pending Inquiries**
   - **Value**: Unread inquiry count
   - **Urgency Indicator**: Color coding for response time
   - **Quick Action**: "Respond Now" button

4. **Stock Alerts**
   - **Value**: Low stock item count
   - **Alert Level**: Critical/warning indicators
   - **Quick Action**: "Restock Items" link

#### Activity Feed
**Layout**: Vertical timeline with expandable items
**Activity Types**:
- **New Inquiries**: Customer contact with preview
- **Order Updates**: Status changes with customer info
- **Listing Performance**: View/inquiry statistics
- **System Notifications**: Policy updates, maintenance notices

### Page 37: Vendor My Listings

#### List Controls
**Top Bar**:
- **View Toggle**: Grid/List/Table view options
- **Bulk Actions**: Select all, archive, publish, delete
- **Add New**: Prominent "Add Listing" button
- **Search/Filter**: Quick search with advanced filters

#### Listing Table
**Columns**:
- **Image**: Thumbnail with hover preview
- **Title**: Car details with edit inline option
- **Status**: Badge with status and last updated
- **Performance**: Views, inquiries, favorites count
- **Actions**: Edit, duplicate, archive, delete dropdown

**Row Interactions**:
- **Hover**: Highlight with action buttons reveal
- **Click**: Navigate to listing details or edit mode
- **Drag**: Reorder listings (where applicable)

### Page 38: Vendor Inventory Management

#### Inventory Grid
**Part Cards**:
- **Image**: Part photo with category icon overlay
- **Details**: Name, SKU, compatibility info
- **Stock Level**: 
  - **Visual**: Progress bar with color coding
  - **Numbers**: Current/minimum stock levels
  - **Status**: In stock/low stock/out of stock badges

**Quick Actions**:
- **Edit Inline**: Click to edit price or stock
- **Restock**: Quick quantity adjustment
- **Duplicate**: Create similar listing

#### Stock Management
**Bulk Operations**:
- **Import/Export**: CSV upload/download functionality
- **Price Updates**: Bulk price adjustments
- **Category Management**: Organize by categories

**Alerts Panel**:
- **Low Stock**: Items below threshold
- **High Demand**: Popular items needing restock
- **Slow Moving**: Items with low turnover

---

## Administrative Interface

### Page 46: Admin User Management

#### User Table
**Layout**: Full-width data table with advanced filtering
**Columns**:
- **User Info**: Avatar, name, email with verification status
- **Role**: Badge with role color coding
- **Registration**: Date and method (email/social)
- **Activity**: Last login, activity score
- **Status**: Active/suspended/pending badges
- **Actions**: Dropdown with view/edit/deactivate options

#### User Details Modal
**Sections**:
- **Profile Information**: Editable user details
- **Activity Log**: Recent actions and login history
- **Permissions**: Role-based access control
- **Security**: Password reset, two-factor authentication

### Page 48: Admin System Logs

#### Log Viewer
**Filter Panel**:
- **Date Range**: Calendar picker with presets
- **Event Type**: Dropdown with log categories
- **Severity Level**: Error, Warning, Info, Debug
- **User Filter**: Search by user or system action

**Log Table**:
- **Timestamp**: Precise time with timezone
- **Level**: Color-coded severity indicator
- **Source**: Module or component origin
- **Message**: Expandable log details
- **User**: Associated user (if applicable)
- **Actions**: View details, export, flag for review

#### Analytics Dashboard
**Charts**:
- **Error Rate**: Time series showing system health
- **User Activity**: Login patterns and usage metrics
- **Performance**: Response times and system load

---

## Component Library Details

### Button Components

#### Primary Button
```css
.btn-primary {
  background: linear-gradient(135deg, #DC2626, #B91C1C);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
  background: linear-gradient(135deg, #EF4444, #DC2626);
}
```

#### States
- **Default**: Base styling with gradient
- **Hover**: Lift effect with increased shadow
- **Active**: Slight depression and reduced shadow
- **Loading**: Spinner overlay with disabled interaction
- **Disabled**: Reduced opacity and grayed appearance

### Form Elements

#### Input Fields
**Structure**:
- **Container**: Relative positioning for floating labels
- **Input**: Full width with consistent padding
- **Label**: Floating animation on focus/content
- **Helper Text**: Small text below for guidance
- **Error State**: Red border with error message

**Validation**:
- **Real-time**: Immediate feedback on input
- **Visual Indicators**: Color coding and icons
- **Accessibility**: ARIA labels and screen reader support

#### Select Dropdowns
**Features**:
- **Search**: Type-ahead filtering
- **Multi-select**: Checkbox options with tag display
- **Custom Styling**: Consistent with design system
- **Keyboard Navigation**: Arrow keys and enter selection

### Card Components

#### Car Listing Card
**Structure**:
- **Image Container**: Aspect ratio maintained, hover zoom
- **Content Area**: Padding and typography hierarchy
- **Action Bar**: Buttons and interactive elements
- **Status Overlay**: Availability indicators

**Interactions**:
- **Hover**: Lift animation with shadow increase
- **Image**: Zoom effect on hover
- **Actions**: Button reveals and micro-animations

#### Information Cards
**Variants**:
- **Stats Cards**: KPI display with trend indicators
- **Feature Cards**: Icon-based information presentation
- **Testimonial Cards**: Quote format with attribution

---

## Responsive Design Patterns

### Breakpoint Strategy
- **Mobile**: 320px - 639px (Single column, bottom navigation)
- **Tablet**: 640px - 1023px (2-column grid, collapsed sidebar)
- **Desktop**: 1024px+ (Full layout, persistent navigation)

### Navigation Adaptations
**Mobile**:
- **Bottom Tab Bar**: Primary navigation
- **Hamburger Menu**: Secondary options
- **Slide-out Drawer**: Full menu with search

**Tablet**:
- **Top Navigation**: Horizontal layout
- **Collapsible Sidebar**: Touch-friendly toggles
- **Modal Overlays**: Form presentations

**Desktop**:
- **Persistent Sidebar**: Always visible navigation
- **Breadcrumbs**: Hierarchical navigation aid
- **Dropdown Menus**: Hover and click interactions

### Content Reflow
**Typography**: Fluid scaling with CSS clamp()
**Images**: Responsive with art direction
**Tables**: Horizontal scroll or card transformation
**Forms**: Single column stack on mobile

---

## Animation & Interaction Patterns

### Page Transitions
**Entry Animations**:
- **Fade In**: Opacity 0 to 1 with slight upward movement
- **Stagger**: Sequential element reveals with delays
- **Slide**: Directional transitions between pages

### Micro-Interactions
**Button Feedback**:
- **Hover**: Scale and shadow changes
- **Click**: Brief scale-down and bounce back
- **Success**: Color change with checkmark animation

**Form Interactions**:
- **Focus**: Glow effect and label animation
- **Validation**: Shake for errors, slide for success
- **Submission**: Loading states with progress indicators

### Loading States
**Skeleton Screens**: Content placeholders during load
**Progressive Loading**: Images load with blur-to-sharp
**Infinite Scroll**: Smooth content addition

---

## Accessibility Considerations

### Color & Contrast
- **WCAG AAA**: 7:1 contrast ratio compliance
- **Color Independence**: Information not color-dependent
- **High Contrast Mode**: Support for OS preferences

### Keyboard Navigation
- **Tab Order**: Logical flow through interactive elements
- **Skip Links**: Direct navigation to main content
- **Keyboard Shortcuts**: Power user efficiency
- **Focus Indicators**: Clear visual feedback

### Screen Reader Support
- **Semantic HTML**: Proper heading hierarchy and landmarks
- **ARIA Labels**: Descriptive labels for complex interactions
- **Live Regions**: Dynamic content announcements
- **Alternative Text**: Meaningful descriptions for images

### Motor Accessibility
- **Touch Targets**: Minimum 44px for mobile interactions
- **Spacing**: Adequate gaps between interactive elements
- **Timing**: No auto-advancing content without controls
- **Error Recovery**: Clear error states and correction paths

---

## Performance Optimization

### Loading Strategies
- **Critical CSS**: Inline above-the-fold styles
- **Font Loading**: Preload display fonts, fallback stacks
- **Image Optimization**: WebP format, responsive sizing
- **Code Splitting**: Route-based and component-based

### Progressive Enhancement
- **Core Functionality**: Works without JavaScript
- **Enhanced Experience**: JavaScript adds interactions
- **Graceful Degradation**: Fallbacks for unsupported features

---

## Conclusion

This comprehensive mock UI design document provides detailed specifications for all 55+ pages of the Gurumisha Motors platform. Each page incorporates the design system principles while maintaining consistency across user interfaces, vendor management tools, and administrative functions.

The design emphasizes:
- **User Experience**: Intuitive navigation and clear information hierarchy
- **Visual Appeal**: Premium automotive aesthetics with modern interactions
- **Accessibility**: Inclusive design for all user capabilities
- **Performance**: Optimized loading and smooth animations
- **Scalability**: Component-based system for future expansion

Implementation should follow the progressive enhancement approach, ensuring core functionality works across all devices and browsers while providing enhanced experiences for modern platforms.