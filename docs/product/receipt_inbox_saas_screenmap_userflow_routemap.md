# Receipt Inbox SaaS
## Screen Map + User Flow + Route Map
Version: v1.0
Purpose: Implementation reference for Codex and development team

---

# 1. Document Purpose

This document defines the complete structural map of the Receipt Inbox SaaS application.

It includes:

1. Screen Map (all application screens)
2. User Flow (how users move through the system)
3. Route Map (recommended route structure)

This document works together with:

Receipt_Inbox_SaaS_PM_Reference_for_Codex_v1.md

This file focuses on **structure and navigation**, not UI styling.

---

# 2. Application Modules

The application is divided into four primary modules.

Dashboard
Inbox
Reports
Admin

These are the only top-level modules in the application.

All other screens must belong under one of these modules.

---

# 3. Screen Map

## 3.1 Authentication

Login

Purpose
User authentication and tenant context

Screens
Login
Forgot Password (future)

---

## 3.2 Dashboard

Purpose
System overview and quick actions

Screens
Dashboard Home

Components
Pending OCR
Needs Review
Recent Reports
Quick Upload
Create Report

---

## 3.3 Inbox Module

Purpose
Central receipt repository

Screens
Inbox List
Receipt Detail
Receipt Edit

Functions
Search
Filter
Preview
Status indicator
Duplicate detection
Assign to report

Filters
Date Range
Vendor
Category
Amount
Status
Report Status

---

## 3.4 Report Module

Purpose
Report management and generation

Screens
Report List
Report Detail
Report Preview
Create Report Wizard

---

## 3.5 Admin Module

Purpose
Organization configuration

Sections
Company Settings
Accounting
Templates
Users

---

# 4. Report Creation Wizard

Report creation is implemented as a Wizard flow.

This wizard is NOT a navigation module.

Steps

Step 1 Settings
Step 2 Upload
Step 3 OCR Processing
Step 4 Review & Edit
Step 5 Generate Report


Each step belongs to the same wizard container.

---

# 5. Wizard Screen Details

## Step 1 Settings

Fields
Employee Name
Department
Trip Title
Report Title
Report Type
Expense Period
Currency


## Step 2 Upload

Features
Drag and drop
Multiple file upload
Image preview
Upload progress


## Step 3 OCR Processing

Features
Processing queue
Status display
Retry failed OCR
Low resolution warning


## Step 4 Review & Edit

Editable fields
Receipt Date
Vendor
Amount
Currency
Category
Memo
Account Code

User actions
Edit values
View receipt image
Resolve duplicates


## Step 5 Generate Report

Features
Preview report
Receipt count
Totals
Generate PDF
Download
Submit

---

# 6. User Flow

## 6.1 Create Report Flow

Login
↓
Dashboard
↓
Create Report
↓
Select Report Type
↓
Wizard Step 1 Settings
↓
Wizard Step 2 Upload
↓
Wizard Step 3 OCR
↓
Wizard Step 4 Review
↓
Wizard Step 5 Generate
↓
Report appears in Reports

---

## 6.2 Manage Receipts Flow

Login
↓
Dashboard
↓
Inbox
↓
Search or Filter Receipts
↓
Review OCR result
↓
Assign receipts to report

---

## 6.3 Admin Accounting Flow

Login
↓
Admin
↓
Accounting
↓
Category Mapping
↓
Vendor Mapping

---

# 7. Route Map

Recommended route structure

Authentication
/login

Dashboard
/dashboard

Inbox
/inbox
/inbox/:receiptId

Reports
/reports
/reports/:reportId

Create Report Wizard
/reports/new
/reports/new/settings
/reports/new/upload
/reports/new/ocr
/reports/new/review
/reports/new/generate

Admin
/admin
/admin/company
/admin/accounting
/admin/accounting/categories
/admin/accounting/vendors
/admin/templates
/admin/users

---

# 8. Mobile Screen Map

Mobile focuses on capture-first workflow.

Screens

Mobile Home
Camera Capture
Recent Receipts
Receipt Status
Reports
Settings


---

# 9. Mobile User Flow

Open App
↓
Camera Capture
↓
Upload Receipt
↓
Automatic OCR
↓
Success / Failure Notification
↓
Stored in Inbox

---

# 10. Structural Rules

Rule 1
Wizard steps must not appear as top-level navigation.

Rule 2
Inbox is the operational receipt center.

Rule 3
Reports contain generated outputs.

Rule 4
Admin configuration must be isolated from user workflow.

Rule 5
Mobile prioritizes receipt capture.

---

# 11. Implementation Notes for Codex

Before implementing a screen:

1. Determine module (Dashboard / Inbox / Reports / Admin)
2. Determine if the screen belongs to Wizard
3. Follow the route map
4. Preserve navigation vs wizard separation

If ambiguity exists, pause implementation and request clarification.

---

# End of Document

