# Receipt Inbox SaaS UAT Checklist (Multi-tenant / Auth / Security)

Date: 2026-03-08
Scope: Tenant isolation, role permissions, module routing, URL filter restore.

## 1. Test Matrix

Host:
- `localhost:5000` (root)
- `lek-partners.local:5000` (tenant)

Identity / Role:
- Anonymous
- General user
- Accounting user
- Tenant admin (`user.manage`)
- Operator

Module / Route:
- `/dashboard`
- `/inbox/review`
- `/reports`
- `/reports/wizard/settings|upload|ocr|review|generate`
- `/admin`
- `/platform` (operator only)

## 2. Critical Smoke (Go/No-go)

1) Anonymous redirect
- Step: open `/dashboard`, `/inbox/review`, `/reports`, `/admin` without login
- Expect: redirect to `/login`

2) Host isolation
- Step: login on `lek-partners.local`; edit company/policy/logo in admin
- Expect: `localhost` config/logo unchanged

3) Cross-tenant guard
- Step: tenant admin on `lek-partners.local` tries cross-tenant management
- Expect: denied (operator-only)

4) Operator boundary
- Step: operator opens `/platform`, manages tenant/admin mapping
- Expect: allowed
- Step: non-operator opens `/platform`
- Expect: blocked/redirected

5) Receipt ownership isolation
- Step: general user A uploads receipts; general user B opens Inbox/Reports
- Expect: B cannot see A's receipts/reports in user module

6) Admin monitor visibility
- Step: tenant admin opens `/admin` > Inbox Monitor
- Expect: can view tenant-wide data with user filter; pagination works

7) Admin drill-down roundtrip
- Step: in Admin Monitor click user link to Inbox/Reports
- Expect: target page opens with user scope filter and `Back to Admin Monitor` button
- Expect: click back returns with original `monitor_*` filter state
- Step: in Admin Monitor click receipt ID
- Expect: Inbox opens with `iq=<receipt_id>` prefilled for quick lookup

## 3. Permission UAT

General user:
- Can: upload receipt, own history, submit/view own report
- Cannot: admin pages, shared preset lock/edit without permission

Accounting user:
- Can: category/vendor mapping, account-related setup
- Confirm: report/receipt view scope follows granted permission set

Tenant admin:
- Can: company/template/user/policy within current host only
- Cannot: platform-level or other host admin operations

Operator:
- Can: platform tenant operations + cross-tenant management

## 4. Wizard UX UAT

1) Navigation rule
- Top nav must remain: `Dashboard / Inbox / Reports / Admin`
- Wizard steps are not top nav items

2) Step routing
- Step links: `/reports/wizard/settings -> upload -> ocr -> review -> generate`
- Back/next flow works; return to Step 1 possible

3) Risk handling
- Step 4 risky rows require confirmation before Step 5 generate
- Personal/Tenant priority mode and DnD order persist as designed

4) Progress summary consistency
- Step 2/3/4/5 all show lifecycle summary text
- After upload/OCR/edit, summary refreshes and values remain consistent

5) Unsaved edit guard
- Step 4 edit one selected row and navigate to Step 5 without save (direct URL / edge case)
- Expect: Step 5 warning banner shown and generate blocked until Step 4 save
- Expect: banner provides Step 4 return link with dirty receipt IDs pre-selected
- Expect: Step 4 row shows `Unsaved` badge immediately after edit
- Expect: `Show Dirty Only` filter lists only unsaved rows
- Expect: `Dirty First` ON/OFF toggle changes row ordering accordingly
- Expect: filter-state badges correctly reflect `Risky only / Dirty only / Dirty first`
- Expect: active button style matches current filter mode (`Risky only`, `Dirty only`, `Show all`, `Dirty first`)
- Expect: Step 5 shows the same review-mode badges passed from Step 4
- Expect: Step 4/5 badges are clickable for quick filter toggle or review return

## 5. URL Filter Restore UAT

Verify refresh/share restore for:
- Dashboard: `dperiod`
- Inbox: `iq, istatus, ireport_status, ilifecycle, idate_from, idate_to, iquick_days, imerchant, icategory, imin_amount, imax_amount, isort`
- Inbox: additional `iuser, aback` (admin drill-down)
- Reports: `rq, rmode, rdate_from, rdate_to, rcreator, rsort, aback`
- Admin monitor: `monitor_user_email, monitor_status, monitor_period_days, monitor_receipt_id, monitor_preset_name`

Search behavior check:
- Inbox `iq` value is numeric (e.g. `123`) -> exact receipt ID match should appear first
- Inbox `iq` value is hash numeric (e.g. `#123`) -> exact receipt ID match should appear first

## 6. Regression Checks

- Local login policy per host (`local_login_enabled`, password)
- Allowed email domain policy per host
- MS365 callback host handling and non-HTTPS local limitations
- Logo filename isolation (`company_logo_<host>.*`)
- Shared preset lock/audit logs behavior
- Wizard local cache TTL: stale local state auto-expires (settings/selection/dirty/risk-confirm)
- TTL expiry notice banner appears on Step 1/4/5 when local wizard state is reset
- Expiry notice includes expired key labels (e.g., settings, selection, dirty, risk-confirm)
- Expiry notice text follows browser locale (ko/en)
- Expiry notice includes `Reset to Step 1` action

## 7. Evidence Capture Template

For each failed case capture:
- Host / user email / role
- Route
- Request payload or URL
- Expected
- Actual
- Screenshot timestamp

## 8. Release Gate

Go:
- All section 2 pass
- No P0/P1 security issue in tenant isolation/permission boundaries

No-go:
- Any cross-tenant data exposure
- Any unauthorized admin/platform action success
