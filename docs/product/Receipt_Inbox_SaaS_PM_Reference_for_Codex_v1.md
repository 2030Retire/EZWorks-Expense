# Receipt Inbox SaaS
## PM-to-Development Reference Document for Codex
Version: v1.0  
Status: Approved UX / Product Structure Baseline  
Purpose: This document is the primary reference for Codex and developers when implementing the Receipt Inbox SaaS product UI/UX structure.

Related global design baseline:
- `docs/product/ezworks_design_definition.md`

---

# 1. Document Purpose

This document defines the product structure, navigation model, screen map, user flow, UX rules, and implementation boundaries for the Receipt Inbox SaaS project.

This is not a marketing concept note.  
This is a working product reference intended for implementation.

Codex must use this document as the baseline reference when:
- designing routes and screen structure
- implementing page layout
- building report creation flow
- deciding whether a screen is a navigation page or a wizard step
- designing mobile vs PC behavior
- implementing admin/accounting settings structure

If code, UI, or route proposals conflict with this document, this document takes priority unless explicitly overridden by a newer approved version.

---

# 2. Product Positioning

The product is **not** just a trip expense report tool.

The product is defined as:

**Receipt Inbox SaaS**

Functional definition:

**Receipt Capture → OCR → Structured Receipt Inbox → Review → Report Generation**

This distinction is critical.

The center of the product is **Receipt Inbox**, not Report output.

Reports are generated from receipts that have already been accumulated, reviewed, and structured.

---

# 3. Core UX Principles

## 3.1 Primary principles

1. The product center is the Receipt Inbox.
2. Report creation is a separate guided process.
3. Navigation and Wizard must never be mixed.
4. PC and Mobile have different primary use cases.
5. AI/OCR assists the user, but final validation belongs to the user.
6. Review is not the same as History unless explicitly defined that way on a specific screen.
7. Admin/accounting configuration must be isolated from end-user report workflow.
8. Design consistency must be maintained across all screens.

## 3.2 Core user experience statement

Capture receipt → store in inbox → review when needed → generate report

---

# 4. Critical Structural Rule: Navigation vs Wizard

This is the most important rule in this document.

## 4.1 Navigation

Navigation refers to persistent application-level destinations.

Examples:
- Dashboard
- Inbox
- Reports
- Admin
- Logout

These are not steps.

They are destinations or modules.

## 4.2 Wizard

Wizard refers to the guided multi-step workflow used when creating one report.

Examples:
- Step 1: Settings
- Step 2: Upload
- Step 3: OCR Processing
- Step 4: Review & Edit
- Step 5: Generate Report

These are not application menus.

They are steps inside one report creation process.

## 4.3 Absolute implementation rule

Codex must not convert Wizard steps into top-level app navigation items.

Incorrect:
- Step 1 Upload
- Step 2 Review
- Step 3 Report

Correct:
- App navigation remains stable
- Report creation opens a wizard flow inside the app

---

# 5. Target Platform Strategy

## 5.1 PC / Web

Primary role:
- management
- review
- report creation
- admin settings
- report history
- accounting configuration

PC is the main environment for structured work.

## 5.2 Mobile

Primary role:
- quick receipt capture
- simple upload
- immediate OCR trigger
- quick status check
- minimal friction login

Mobile is not primarily for full report administration.
Mobile is capture-first.

---

# 6. High-Level Product Structure

The application should be organized at the highest level as follows:

- Dashboard
- Inbox
- Reports
- Admin

Additional functions such as login, profile, language toggle, and logout are utility functions, not primary business modules.

---

# 7. Screen Map

## 7.1 Public / Entry Screens

### 7.1.1 Login
Purpose:
- authenticate user
- determine tenant / organization context
- persist session appropriately

PC expectations:
- standard login form
- optional SSO later
- remember session support

Mobile expectations:
- persistent login preferred after first successful sign-in
- biometric unlock can be considered later
- minimize repeated login friction

---

## 7.2 Main Application Screens

### 7.2.1 Dashboard
Purpose:
- give users an immediate summary of what requires attention

Core blocks:
- receipts waiting for OCR
- receipts needing review
- possible duplicates
- recent reports
- quick upload entry
- create report entry

Recommended actions:
- Upload Receipts
- Go to Inbox
- Create Report
- View Recent Reports

Dashboard is a summary hub, not the location where the whole workflow happens.

### 7.2.2 Inbox
Purpose:
- central receipt repository
- view and manage uploaded receipts
- support search, filtering, status tracking, and pre-report review

Inbox is effectively the receipt history and operational receipt management screen.

Core components:
- receipt table / list
- image preview
- OCR result summary
- search bar
- filters
- row status
- duplicate warning
- report assignment indicator

Required filters:
- date range
- vendor
- category
- amount range
- OCR status
- report assignment status
- report type where applicable

Suggested statuses:
- uploaded
- processing
- processed
- needs_review
- duplicate
- failed

Suggested report linkage states:
- assigned
- unassigned

Important note:
The Inbox screen is not the report creation wizard.
It is a reusable operational screen.

### 7.2.3 Reports
Purpose:
- manage generated reports

Core components:
- report list
- report type
- title
- created date
- period
- status
- download
- preview
- regenerate if allowed
- submission state if future workflow exists

Suggested statuses:
- draft
- generated
- submitted
- approved
- rejected
- archived

### 7.2.4 Admin
Purpose:
- organization-level settings and business rules

Admin should be clearly separated from user workflow.

Recommended sub-sections:
- Company
- Accounting
- Templates
- Users / Roles
- Preferences / Processing Rules

---

# 8. Report Creation UX

## 8.1 Entry point

Users should enter report creation from:
- Dashboard ("Create Report")
- Reports ("New Report")
- Inbox (selected receipts → create report)
- possibly a dedicated CTA in the header

Before wizard starts, user selects report type.

Examples:
- Domestic Expense Report
- International Expense Report
- Monthly Expense Report
- Trip Expense Report

The report type selection happens before or at the start of the wizard.

## 8.2 Wizard structure

### Step 1. Settings
Purpose:
- define the report context

Fields may include:
- employee name
- department
- trip title / purpose
- report title
- report type
- expense period
- currency mode
- domestic / international mode
- optional advanced settings

Notes:
- keep visual style similar to the original richer UI
- this screen should feel like a guided form, not a bare list page

### Step 2. Upload
Purpose:
- attach receipt images to this report session

Required functions:
- drag and drop
- choose files
- multi-file upload
- upload progress
- image validation
- basic duplicate pre-warning if possible

PC behavior:
- support bulk upload strongly

Mobile behavior:
- camera capture
- gallery select
- multiple capture path if practical

### Step 3. OCR Processing
Purpose:
- show OCR progress and readiness

Required functions:
- receipt-by-receipt progress
- processing queue state
- success / fail status
- retry failed OCR
- indicate low-quality image problems

Important:
If image quality is too low, user must be warned clearly and early.

Example message:
"Image quality is too low to reliably process this receipt. Please retake the photo."

This is important because users may discard physical receipts after upload.

### Step 4. Review & Edit
Purpose:
- validate extracted data before report generation

Required editable fields:
- receipt date
- vendor / merchant
- amount
- currency
- category
- memo / notes
- account code if enabled
- duplicate override decision if necessary

Required UX behavior:
- allow row-level correction
- clearly highlight failed or uncertain OCR values
- allow image preview while editing
- indicate category/vendor auto-mapping suggestions

This step is the true "review" step inside report creation.

This must not be confused with the Inbox screen.

### Step 5. Generate Report
Purpose:
- finalize report output

Required functions:
- preview summary
- selected receipt count
- totals
- category totals if needed
- template selection if multiple approved templates exist
- generate PDF
- generate downloadable output
- submit or save draft

---

# 9. Review vs History Clarification

This distinction must be preserved.

## 9.1 Inbox / History concept
This is where previously uploaded receipts are viewed and managed.

This is persistent and reusable.

## 9.2 Wizard Review concept
This is the validation step for one report being generated.

This is contextual and temporary within the report creation flow.

Implementation rule:
Codex must not rename Inbox/History to "Review" unless the screen is truly part of the wizard.

---

# 10. Admin Information Architecture

## 10.1 Admin sections

Recommended admin menu:

- Company Settings
- Accounting
- Report Templates
- Users & Roles
- Processing Preferences

## 10.2 Accounting section

Accounting is a separate admin domain, not a normal user menu.

Recommended accounting subsections:
- Category Mapping
- Vendor Mapping
- Account Code Rules
- Currency / FX behavior later if needed

### 10.2.1 Category Mapping
Required capabilities:
- add category
- edit category
- delete category
- reorder category
- mark active/inactive
- assign default account code
- optional report-type applicability

Important:
Current designs that only allow editing rows are incomplete.
Category management must include create/update/delete capabilities.

### 10.2.2 Vendor Mapping
Purpose:
- auto-suggest category and/or account code based on vendor

Required capabilities:
- search vendors
- edit rule
- deactivate rule
- merge duplicates later if needed

UX rule:
Vendor Mapping should not always appear fully expanded.
Use collapsible or secondary-detail presentation.

Recommended pattern:
- collapsed panel by default
- expand on demand
- optionally open in modal / drawer / detail panel

Important:
"Add Vendor Rule" may exist, but it should not dominate the screen.
The more important admin gap right now is robust category management.

---

# 11. Design Consistency Rules

Codex must preserve and extend the stronger original UI language shown in the richer screen designs.

The following must be preserved:
- clear card sections
- strong report-type selector
- visually grouped step blocks
- modern spacing
- consistent visual hierarchy
- admin accessibility in top navigation where appropriate
- brand-aware layout

Codex must avoid replacing structured designed screens with plain, generic, utility-looking pages unless intentionally approved.

The simplified "raw page with links" style is not acceptable as the default final UX direction.

---

# 12. PC User Flows

## 12.1 Core PC flow: create new report
1. User logs in
2. User lands on Dashboard
3. User selects Create Report
4. User selects report type
5. Wizard opens
6. Step 1 Settings completed
7. Step 2 Upload receipts
8. Step 3 OCR processes
9. Step 4 User reviews and edits
10. Step 5 Generate report
11. User downloads or submits report
12. Generated report appears in Reports

## 12.2 Core PC flow: manage existing receipts
1. User logs in
2. User goes to Inbox
3. User searches / filters uploaded receipts
4. User reviews status or OCR quality
5. User optionally selects receipts
6. User starts report creation or edits receipt details

## 12.3 Core PC flow: accounting admin
1. Admin logs in
2. Admin goes to Admin
3. Admin enters Accounting
4. Admin manages categories
5. Admin reviews vendor mapping rules
6. Admin saves changes
7. Future OCR/review flows consume these rules

---

# 13. Mobile User Flows

## 13.1 Core mobile flow: fast receipt upload
1. User opens app
2. User remains signed in whenever possible
3. User lands on capture-focused home
4. User taps camera
5. User captures receipt
6. Receipt uploads immediately
7. OCR runs immediately by default
8. User sees quick success / failure result
9. If image quality is low, user is prompted to retake immediately

## 13.2 Mobile flow: check pending items
1. User opens app
2. User sees pending review count
3. User opens recent receipts
4. User checks OCR results
5. User optionally fixes simple fields
6. User leaves deeper report creation for PC unless mobile UX becomes richer later

## 13.3 Mobile settings concept
Later settings may include:
- immediate OCR on upload (default: on)
- batch OCR option
- receipt retention preferences
- notifications
- biometric unlock

Immediate OCR should be the default.
Batch OCR may be optional.

---

# 14. Route / Module Guidance for Codex

The exact route names may vary, but the module boundaries should resemble:

- /login
- /dashboard
- /inbox
- /reports
- /reports/new or /create-report
- /admin
- /admin/accounting
- /admin/templates
- /admin/users

Wizard-related routes may be nested under:
- /reports/new/step-1
- /reports/new/step-2
- /reports/new/step-3
- /reports/new/step-4
- /reports/new/step-5

or handled in a single wizard container with internal state.

Either approach is acceptable if:
- wizard integrity is preserved
- navigation integrity is preserved
- back/forward behavior is handled clearly

---

# 15. Data / UX Terminology Standards

Codex should use consistent terminology.

Preferred terms:
- Inbox
- Receipt
- Report
- OCR Processing
- Review & Edit
- Category Mapping
- Vendor Mapping

Avoid using the following ambiguously:
- Review (for a history screen)
- Step (for top-level navigation)
- Upload page as a standalone product center

---

# 16. Implementation Boundaries

This document defines product structure and UX requirements.
It does not lock down:
- final database schema
- detailed API contracts
- exact component library
- exact CSS framework decisions
- exact OCR engine implementation

However, implementation must respect the UX structure in this document.

---

# 17. Explicit Do / Do Not List for Codex

## 17.1 Do
- keep top-level navigation stable
- keep report creation as a wizard
- preserve richer visual design direction
- treat Inbox as the operational receipt center
- separate Admin/Accounting from user workflow
- support category CRUD in admin
- keep vendor mapping secondary/collapsible
- design PC and mobile differently

## 17.2 Do Not
- do not replace the wizard with plain menu pages
- do not rename history/inbox screens as review unless they are wizard review steps
- do not flatten the UI into generic utility screens
- do not force admin/accounting settings into end-user workflow
- do not assume mobile and PC should behave identically
- do not leave category management as edit-only

---

# 18. Recommended Next Deliverables

After this document, Codex / development should ideally produce:

1. Screen-by-screen UI specification
2. Clickable navigation structure
3. Wizard interaction details
4. Inbox table behavior specification
5. Admin accounting specification
6. Mobile capture screen specification
7. Route map
8. component breakdown

---

# 19. Final Instruction to Codex

Use this document as the primary UX and navigation reference.

Before implementing or restructuring screens, verify:
1. Is this a top-level navigation destination?
2. Or is this a step within one report creation wizard?
3. Is this screen Inbox/history?
4. Or is this the review step inside the report creation workflow?
5. Is this an admin/configuration screen that should be isolated?

If there is ambiguity, preserve the separation rules defined in this document.

This project must maintain:
- Inbox-centered product logic
- wizard-based report creation
- consistent visual design
- PC/mobile role separation
- clear admin isolation

End of document.
