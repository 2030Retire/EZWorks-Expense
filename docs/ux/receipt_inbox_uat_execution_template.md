# Receipt Inbox SaaS UAT Execution Template

Date:
Environment:
Build/Commit:
Tester:

## A. Role / Host Matrix

| Host | User | Role | Expected Scope | Result |
|---|---|---|---|---|
| localhost:5000 |  | General | Own data only |  |
| localhost:5000 |  | Accounting | Tenant-wide by permission |  |
| localhost:5000 |  | Tenant Admin | Admin module (current host) |  |
| lek-partners.local:5000 |  | General | Own data only |  |
| lek-partners.local:5000 |  | Accounting | Tenant-wide by permission |  |
| lek-partners.local:5000 |  | Tenant Admin | Admin module (current host) |  |
|  |  | Operator | Platform + cross-tenant |  |

## B. Critical Cases (PASS/FAIL)

| ID | Scenario | Steps | Expected | Actual | PASS/FAIL | Evidence |
|---|---|---|---|---|---|---|
| C-01 | Anonymous redirect | open protected routes | redirect to /login |  |  |  |
| C-02 | Host isolation | edit tenant config/logo | other host unchanged |  |  |  |
| C-03 | Cross-tenant guard | tenant admin tries cross-tenant | denied |  |  |  |
| C-04 | Receipt ownership | user A/B compare Inbox | no cross-user exposure |  |  |  |
| C-05 | Admin monitor drill-down | click KPI/receipt ID links | correct filters + back |  |  |  |
| C-06 | Wizard risk guard | Step4 risky without confirm | Step5 blocked |  |  |  |
| C-07 | Unsaved guard | edit row unsaved -> Step5 | warning + blocked |  |  |  |
| C-08 | URL restore | refresh/share URLs | filters restored |  |  |  |

## C. Wizard UX Checks

| Check | Result | Notes |
|---|---|---|
| Step1~5 routing/back/next |  |  |
| Step2~5 progress summary consistency |  |  |
| Step4 filter badges (`Risky/Dirty/Dirty first`) |  |  |
| Step4 button active states |  |  |
| Step5 review-state badges match Step4 |  |  |

## D. Search / Filter Checks

| Check | Input | Expected | Result |
|---|---|---|---|
| Numeric ID priority | `iq=123` | exact ID row first |  |
| Hash ID priority | `iq=#123` | exact ID row first |  |
| Dirty only | Step4 dirty rows exist | only dirty rows shown |  |

## E. Defects

| Severity | Title | Repro | Impact | Owner | Status |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## F. Final Gate

- Go / No-go:
- Blocking issues:
- Follow-up tasks:
