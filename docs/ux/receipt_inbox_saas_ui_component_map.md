# Receipt Inbox SaaS
## UI Component Map (Implementation Guide for Codex)
Version: v1.0
Purpose: Define UI component structure for each major screen so that development agents (Codex) build consistent UI without inventing layouts.

This document complements:
- Receipt_Inbox_SaaS_PM_Reference_for_Codex_v1.md
- receipt_inbox_saas_screenmap_userflow_routemap.md

This file focuses on **UI component structure**, not styling details.

---

# 1. Design Philosophy

The UI should follow a **structured SaaS layout** with clear component zones.

Primary goals:

- prevent generic "utility page" layouts
- maintain consistent card-based SaaS design
- ensure wizard steps feel guided
- keep Inbox powerful but readable

Preferred design pattern:

Header
Page Title
Primary Action
Content Cards
Tables
Secondary Panels

---

# 2. Global Layout Components

These components appear across most screens.

Top Navigation Bar

Components
Logo
Primary Navigation
User Menu
Notifications (future)

Primary Navigation
Dashboard
Inbox
Reports
Admin


Page Layout

Header Section
Page Title
Primary Action Button

Main Content
Cards or Tables

Secondary Panels
Filters
Details
Side drawers

---

# 3. Dashboard UI Components

Purpose
Provide operational overview and entry points.

Dashboard Layout

Header
Page Title: Dashboard
Primary Button: Create Report

Summary Cards
Pending OCR
Needs Review
Possible Duplicates

Activity Section
Recent Reports
Recent Uploads

Quick Actions
Upload Receipts
Create Report
Go to Inbox

Optional Future Widgets
Spending Summary
Category Breakdown

---

# 4. Inbox Screen UI Components

Purpose
Central operational interface for receipt management.

Layout

Header
Page Title: Inbox
Primary Action: Upload Receipts

Filter Panel
Date Range
Vendor
Category
Amount Range
Status
Report Assignment

Receipt Table

Columns
Thumbnail
Date
Vendor
Amount
Currency
Category
Status
Report Assignment

Row Actions
Preview
Edit
Assign to Report
Delete

Side Panel (or Modal)
Receipt Image Preview
OCR Extracted Fields
Editable Fields

Status Indicators
Processed
Needs Review
Duplicate
OCR Failed

---

# 5. Reports Screen UI Components

Purpose
Manage generated reports.

Layout

Header
Page Title: Reports
Primary Button: Create Report

Report Table

Columns
Report Title
Report Type
Employee
Period
Created Date
Status

Row Actions
Preview
Download
Edit
Delete

Report Detail View

Report Summary
Receipt List
Totals
Download Button

---

# 6. Report Creation Wizard UI Components

The wizard must feel like a guided process.

Layout

Wizard Header
Progress Step Indicator

Step Navigation
Step 1 Settings
Step 2 Upload
Step 3 OCR
Step 4 Review
Step 5 Generate

Main Wizard Container
Content changes per step

Footer
Back Button
Next Button
Cancel Button

---

# 7. Wizard Step Components

## Step 1 Settings

Components
Form Card

Fields
Employee Name
Department
Report Title
Report Type
Expense Period
Currency

Optional
Trip Purpose
Notes


## Step 2 Upload

Components
Upload Drop Zone
Upload Button
Upload Progress List

Image Preview Grid

Actions
Remove Image
Retry Upload


## Step 3 OCR Processing

Components
Processing List
Status Indicators

Statuses
Processing
Success
Failed
Low Resolution

Actions
Retry OCR
Replace Image


## Step 4 Review & Edit

Components
Editable Receipt Table

Columns
Date
Vendor
Amount
Currency
Category
Memo

Row Controls
Edit Inline
View Image
Resolve Duplicate


## Step 5 Generate Report

Components
Report Summary Card

Fields
Receipt Count
Total Amount
Category Totals

Actions
Generate PDF
Download
Submit
Save Draft

---

# 8. Admin UI Components

Admin Layout

Admin Navigation Sidebar

Sections
Company
Accounting
Templates
Users

---

# 9. Accounting Components

## Category Mapping

Components
Category Table

Columns
Category Name
Account Code
Status

Actions
Add Category
Edit Category
Delete Category
Reorder Category


## Vendor Mapping

Components
Vendor Table

Columns
Vendor Name
Suggested Category
Account Code

Actions
Edit Rule
Disable Rule

UX Rule
Vendor Mapping should be collapsible or secondary panel.

---

# 10. Mobile UI Components

Mobile design prioritizes capture.

Mobile Home

Primary Component
Camera Capture Button

Secondary Components
Recent Receipts
Pending Review
Reports Shortcut


Receipt Capture Screen

Camera View
Capture Button
Gallery Button

Upload Confirmation
OCR Status Indicator

---

# 11. Component Consistency Rules

All major screens should follow these patterns.

Use Cards for logical sections.

Use Tables for operational data.

Primary actions appear in page header.

Filters appear in a dedicated filter panel.

Details appear in modal or side panel.

Wizard always shows progress indicator.


---

# 12. Implementation Notes for Codex

Before building a screen:

1. Identify module (Dashboard / Inbox / Reports / Admin)
2. Check screen map
3. Follow component structure
4. Preserve wizard layout

Do not invent completely new layouts unless required.

If unsure, prefer the component pattern defined here.

---

# End of Document

