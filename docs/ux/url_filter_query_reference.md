# URL Filter Query Reference

This document defines URL query keys used for filter state restore/share.

## Scope
- Dashboard
- Inbox
- Reports
- Admin > Inbox Monitor

## 1) Dashboard
Path: `/dashboard`

Keys:
- `dperiod`: `0|7|30|90`

Example:
- `/dashboard?dperiod=30`

## 2) Inbox
Path: `/inbox/review`

Keys:
- `iq`: search text
- `istatus`: receipt status
- `ireport_status`: `unassigned|assigned`
- `ilifecycle`: lifecycle state
- `idate_from`: `YYYY-MM-DD`
- `idate_to`: `YYYY-MM-DD`
- `iquick_days`: `all|7|30|90|custom`
- `imerchant`: merchant contains
- `icategory`: category
- `imin_amount`: minimum amount
- `imax_amount`: maximum amount
- `isort`: sort key
- `iuser`: uploader email (admin/accounting drill-down)
- `aback`: encoded admin monitor return path

Sort values (`isort`):
- `created_desc`
- `date_desc`
- `date_asc`
- `amount_desc`
- `amount_asc`
- `status_asc`

Example:
- `/inbox/review?iq=uber&istatus=processed&idate_from=2026-03-01&idate_to=2026-03-31&isort=amount_desc`
- `/inbox/review?iuser=it@lekpartners.com&istatus=needs_review`

## 3) Reports
Path: `/reports`

Keys:
- `rq`: search text
- `rmode`: `domestic|international`
- `rdate_from`: `YYYY-MM-DD`
- `rdate_to`: `YYYY-MM-DD`
- `rcreator`: creator email (effective when user can view all)
- `rsort`: sort key
- `aback`: encoded admin monitor return path

Sort values (`rsort`):
- `created_desc`
- `created_asc`
- `count_desc`
- `count_asc`
- `amount_desc`
- `amount_asc`

Example:
- `/reports?rq=sales&rmode=domestic&rdate_from=2026-03-01&rdate_to=2026-03-31&rsort=count_desc`

## 4) Admin Inbox Monitor
Path: `/admin`

Keys:
- `monitor_user_email`
- `monitor_status`
- `monitor_period_days`
- `monitor_receipt_id`
- `monitor_preset_name`

Example:
- `/admin?monitor_user_email=it@lekpartners.com&monitor_period_days=30&monitor_status=processed`

## 5) Reports Wizard (Step 4 Review)
Path: `/reports/wizard/review`

Keys:
- `ids`: preselected receipt ids (comma-separated)
- `wrisky`: risky-only filter (`1`)
- `wdirty`: dirty-only filter (`1`)
- `wdirtyfirst`: dirty-first sort override (`0` disables, default ON)

Example:
- `/reports/wizard/review?ids=101,102&wrisky=1&wdirtyfirst=0`

Step 5 (`/reports/wizard/generate`) also accepts `wrisky/wdirty/wdirtyfirst` as pass-through state for review-mode badges.

## Notes
- URL sync uses `history.replaceState` (same page, query only update).
- Empty/default values are omitted from query where applicable.
- Query values are UI-state keys, not public API contract.
- Wizard local cache TTL is configurable via Admin > Wizard settings (`cache_ttl_hours`, 1~720).
