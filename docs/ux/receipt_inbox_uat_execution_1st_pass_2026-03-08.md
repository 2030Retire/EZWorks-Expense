# Receipt Inbox SaaS UAT Execution (1st Pass)

Date: 2026-03-08  
Environment: local dev (`localhost:5000`, `lek-partners.local:5000`)  
Build/Commit: workspace current (not git-managed in this path)  
Tester: Codex (automated/static checks) + Manual UAT Pending

## A. Role / Host Matrix (Prepared)

| Host | User | Role | Expected Scope | Result |
|---|---|---|---|---|
| localhost:5000 | (manual) | General | Own data only | PENDING-MANUAL |
| localhost:5000 | (manual) | Accounting | Tenant-wide by permission | PENDING-MANUAL |
| localhost:5000 | (manual) | Tenant Admin | Admin module (current host) | PENDING-MANUAL |
| lek-partners.local:5000 | user@lekpartners.com | General | Own data only | PENDING-MANUAL |
| lek-partners.local:5000 | admin@lekpartners.com | Accounting | Tenant-wide by permission | PENDING-MANUAL |
| lek-partners.local:5000 | it@lekpartners.com | Tenant Admin | Admin module (current host) | PENDING-MANUAL |
| (operator host) | operator account | Operator | Platform + cross-tenant | PENDING-MANUAL |

## B. Critical Cases (1st Pass)

| ID | Scenario | Steps | Expected | Actual | PASS/FAIL | Evidence |
|---|---|---|---|---|---|---|
| C-01 | Anonymous redirect | open protected routes | redirect to /login | Requires browser run | PENDING-MANUAL | - |
| C-02 | Host isolation | edit tenant config/logo | other host unchanged | Tenant config files separated by host key | PASS (static) | `configs/<host>.json`, logo naming rule |
| C-03 | Cross-tenant guard | tenant admin tries cross-tenant | denied | Guard exists in backend (`_ensure_tenant_admin_allowed`) | PASS (static) | [app.py](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/app.py) |
| C-04 | Receipt ownership | user A/B compare Inbox | no cross-user exposure | Permission-scope logic implemented (`receipt.view_all` vs own) | PASS (static) | [app.py](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/app.py) |
| C-05 | Admin monitor drill-down | click KPI/receipt ID links | correct filters + back | Link/query wiring implemented (`iuser/iq/aback`) | PASS (static) | [admin.html](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/templates/admin.html) |
| C-06 | Wizard risk guard | Step4 risky without confirm | Step5 blocked | Guard logic implemented | PASS (static) | [report_wizard_review.html](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/templates/report_wizard_review.html) |
| C-07 | Unsaved guard | edit row unsaved -> Step5 | warning + blocked | Dirty-state + banner + block logic implemented | PASS (static) | [report_wizard_generate.html](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/templates/report_wizard_generate.html) |
| C-08 | URL restore | refresh/share URLs | filters restored | Query sync/restore implemented for modules/wizard | PASS (static) | [url_filter_query_reference.md](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/docs/ux/url_filter_query_reference.md) |

## C. Automated Checks

| Check | Result | Evidence |
|---|---|---|
| Python syntax compile | PASS | `python -m py_compile app.py user_db.py receipt_inbox_db.py` |
| Wizard TTL config support | PASS | `wizard.cache_ttl_hours` in backend + admin UI + wizard consumers |
| Expiry notice enhancements | PASS | key-label display + locale + reset action in Step1/4/5 |
| Security scope smoke | PASS | `python scripts/security_scope_smoke.py` |
| UI contract smoke | PASS | `python scripts/ui_contract_smoke.py` |

### C-Detail. Security Scope Smoke Result

```json
{
  "status": "PASS",
  "host": "tenant-a.local",
  "checks": [
    "own_scope_receipt_list",
    "cross_user_detail_image_audit_forbidden",
    "view_all_scope_and_user_filter",
    "host_isolation"
  ],
  "sample_receipt_ids": [
    1,
    2
  ]
}
```

## D. Known Manual-UAT Queue

1. Browser validation for all critical cases with real sessions/cookies.
2. Role permission behavior confirmation with actual user permission assignments.
3. Host-isolation verification by changing tenant settings/logo and cross-checking root host.
4. Admin monitor drill-down roundtrip (including tooltip behavior ko/en).
5. Wizard state restore/TTL expiry real-time scenario (with forced old timestamp).

### Manual Execution Pack (Generated)

- Template generator: `python scripts/uat_manual_runner.py`
- Result aggregator: `python scripts/uat_result_aggregator.py --date 2026-03-08`
- Output folder: [docs/ux/uat_evidence/2026-03-08](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/docs/ux/uat_evidence/2026-03-08)
- Markdown template: [manual_uat_template.md](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/docs/ux/uat_evidence/2026-03-08/manual_uat_template.md)
- JSON template: [manual_uat_template.json](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/docs/ux/uat_evidence/2026-03-08/manual_uat_template.json)
- Aggregated summary: [uat_result_summary.md](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/docs/ux/uat_evidence/2026-03-08/uat_result_summary.md)
- Aggregated json: [uat_result_summary.json](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/docs/ux/uat_evidence/2026-03-08/uat_result_summary.json)

## E. Data Snapshot Used

- Tenant config observed: `configs/lek-partners.local.json`
- Noted values:
  - `auth.allowed_email_domains = ["lekpartners.com"]`
  - `auth.admin_emails = ["it@lekpartners.com"]`
  - `auth.local_login_enabled = true`
  - `auth.local_login_password = "lek1234!"`

## F. Interim Gate

- Security/permission implementation status: **Automated smoke PASS + manual verification pending**
- Release decision: **CONDITIONAL NO-GO (manual browser UAT evidence not yet completed)**
- Next immediate action: execute manual matrix and update PASS/FAIL + screenshots

## G. Auto UAT Closure (2nd Pass)

- Runner: `python scripts/uat_auto_runner.py`
- Result: **GO** (`PASS=8, FAIL=0, PENDING=0`)
- Auto report: [uat_auto_result_2nd_pass.md](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/docs/ux/uat_evidence/2026-03-08/uat_auto_result_2nd_pass.md)
- Auto json: [uat_auto_result_2nd_pass.json](/C:/Users/John/OneDrive%20-%20LIT/LIT/시스템개발/GPT/expense-processor/docs/ux/uat_evidence/2026-03-08/uat_auto_result_2nd_pass.json)

## H. Current Gate (Updated)

- Engineering gate (automated): **GO**
- Business/UAT gate (human acceptance): **CONDITIONAL NO-GO** until manual sign-off is filled in template.
