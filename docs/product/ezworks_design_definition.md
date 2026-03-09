# EZWorks Design Definition (Global)
Version: v1.0  
Updated: 2026-03-08

This document defines shared UX and visual rules for EZWorks products.
For EZWorks-Expense, this document is applied together with:

- `docs/product/Receipt_Inbox_SaaS_PM_Reference_for_Codex_v1.md`
- `docs/product/ezworks_expense_ai_design.md`
- `docs/ux/receipt_inbox_saas_screenmap_userflow_routemap.md`
- `docs/ux/receipt_inbox_saas_ui_component_map.md`
- `docs/ux/receipt_data_workflow.md`

If this document conflicts with module-specific workflow architecture, module workflow architecture wins.

## 1. Global Layout Rules
- Use the same shell structure across modules:
  - Brand header (logo + company info + host chip)
  - Module navigation: Dashboard / Inbox / Reports / Admin
  - Content area with consistent card/table style
- Use responsive width that avoids unnecessary narrow desktop rendering:
  - Desktop content container target: wide (up to ~1500px class)
  - Mobile/tablet collapses naturally
- Keep module pages visually consistent; avoid isolated one-off themes per page.

## 2. Branding Rules
- Header logo priority:
  1. tenant company logo
  2. EZWorks mark fallback (never generic `COMPANY` text block)
- Company name/address/phone shown when configured.
- Brand fallback must remain professional and product-grade.

## 3. Navigation Rules
- Top navigation is fixed and global:
  - Dashboard
  - Inbox
  - Reports
  - Admin
- Wizard steps are not top-level navigation items.
- Wizard stays inside the report creation flow only.

## 4. Admin Information Architecture
- Admin is tenant-scoped by default.
- Platform (operator) console is separate and is the only cross-tenant management location.
- Admin page should use grouped tabs for long forms, for example:
  - Company
  - Accounting
  - Users
  - Templates
  - Monitor

## 5. Tenant Security Rules
- Non-operator admin users cannot view or manage other tenant data.
- Even operator users should use Platform for cross-tenant actions.
- User lists, permissions, templates, and policy operations must remain host-scoped in tenant Admin.

## 6. Template Rules
- Template architecture is split:
  - Shared default templates (solution-level baseline)
  - Tenant custom templates (host-scoped overrides)
- Tenant custom templates must be isolated per host.
- Template UI should be simple:
  - generate base template from current settings
  - upload tenant custom template
  - preview current template
- Avoid overcomplicated “AI-only template generation” messaging in admin UX.

## 7. Quality Standard
- Keep edits user-authoritative (AI suggestions editable).
- Preserve module boundaries and data ownership boundaries.
- Prefer predictable, maintainable UI behavior over hidden automation.

## 8. Numeric Formatting Rule
- All monetary values must be right-aligned across web tables and forms.
- Use tabular numeric rendering where possible for scanability.
- Date display standard for US-facing UI/export is `mm/dd/yyyy` unless a tenant explicitly overrides.
