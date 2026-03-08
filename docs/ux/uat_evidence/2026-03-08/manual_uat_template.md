# Manual UAT Execution Template

Generated at: 2026-03-08T22:15:33

## 1) Role / Host Matrix

| Host | User | Role | Expected Scope | Actual | PASS/FAIL | Evidence |
|---|---|---|---|---|---|---|
| localhost:5000 | (manual) | General | Own data only |  |  |  |
| localhost:5000 | (manual) | Accounting | Tenant-wide by permission |  |  |  |
| localhost:5000 | (manual) | Tenant Admin | Admin module (current host) |  |  |  |
| lek-partners.local:5000 | user@lekpartners.com | General | Own data only |  |  |  |
| lek-partners.local:5000 | admin@lekpartners.com | Accounting | Tenant-wide by permission |  |  |  |
| lek-partners.local:5000 | it@lekpartners.com | Tenant Admin | Admin module (current host) |  |  |  |
| (operator host) | operator account | Operator | Platform + cross-tenant |  |  |  |

## 2) Critical Cases

| ID | Scenario | Steps | Expected | Actual | PASS/FAIL | Evidence |
|---|---|---|---|---|---|---|
| C-01 | Anonymous redirect | Open /dashboard, /inbox/review, /reports, /admin without login | Redirect to /login |  |  |  |
| C-02 | Host isolation | Change company name/logo on lek-partners.local host | localhost host config/logo unchanged |  |  |  |
| C-03 | Cross-tenant admin guard | Tenant admin tries host switch to another tenant | Forbidden/guarded |  |  |  |
| C-04 | Receipt ownership scope | General user A/B compare Inbox list/detail/image/audit | Only own receipts visible |  |  |  |
| C-05 | Admin monitor drill-down | Click KPI/user/receipt links from Admin monitor | Correct filter applied and Back to Admin Monitor works |  |  |  |
| C-06 | Wizard step separation | Check top nav and wizard pages | Top nav only Dashboard/Inbox/Reports/Admin, steps only in wizard progress |  |  |  |
| C-07 | Unsaved edit guard | Edit Step4 row and move Step5 without save | Warning shown and generate blocked |  |  |  |
| C-08 | Accounting permission boundary | Login as non-accounting user and open /inbox/settings | No accounting edit access |  |  |  |

## 3) Evidence Naming Rule

- Screenshot: `C-xx_<host>_<user>_<short-desc>.png`
- Video(optional): `C-xx_<host>_<user>.mp4`
- Log: `C-xx_<host>_<user>.txt`
