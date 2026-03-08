import json
from datetime import datetime
from pathlib import Path


ROLE_HOST_MATRIX = [
    {"host": "localhost:5000", "user": "(manual)", "role": "General", "scope": "Own data only"},
    {"host": "localhost:5000", "user": "(manual)", "role": "Accounting", "scope": "Tenant-wide by permission"},
    {"host": "localhost:5000", "user": "(manual)", "role": "Tenant Admin", "scope": "Admin module (current host)"},
    {"host": "lek-partners.local:5000", "user": "user@lekpartners.com", "role": "General", "scope": "Own data only"},
    {"host": "lek-partners.local:5000", "user": "admin@lekpartners.com", "role": "Accounting", "scope": "Tenant-wide by permission"},
    {"host": "lek-partners.local:5000", "user": "it@lekpartners.com", "role": "Tenant Admin", "scope": "Admin module (current host)"},
    {"host": "(operator host)", "user": "operator account", "role": "Operator", "scope": "Platform + cross-tenant"},
]


CRITICAL_CASES = [
    {
        "id": "C-01",
        "scenario": "Anonymous redirect",
        "steps": "Open /dashboard, /inbox/review, /reports, /admin without login",
        "expected": "Redirect to /login",
    },
    {
        "id": "C-02",
        "scenario": "Host isolation",
        "steps": "Change company name/logo on lek-partners.local host",
        "expected": "localhost host config/logo unchanged",
    },
    {
        "id": "C-03",
        "scenario": "Cross-tenant admin guard",
        "steps": "Tenant admin tries host switch to another tenant",
        "expected": "Forbidden/guarded",
    },
    {
        "id": "C-04",
        "scenario": "Receipt ownership scope",
        "steps": "General user A/B compare Inbox list/detail/image/audit",
        "expected": "Only own receipts visible",
    },
    {
        "id": "C-05",
        "scenario": "Admin monitor drill-down",
        "steps": "Click KPI/user/receipt links from Admin monitor",
        "expected": "Correct filter applied and Back to Admin Monitor works",
    },
    {
        "id": "C-06",
        "scenario": "Wizard step separation",
        "steps": "Check top nav and wizard pages",
        "expected": "Top nav only Dashboard/Inbox/Reports/Admin, steps only in wizard progress",
    },
    {
        "id": "C-07",
        "scenario": "Unsaved edit guard",
        "steps": "Edit Step4 row and move Step5 without save",
        "expected": "Warning shown and generate blocked",
    },
    {
        "id": "C-08",
        "scenario": "Accounting permission boundary",
        "steps": "Login as non-accounting user and open /inbox/settings",
        "expected": "No accounting edit access",
    },
]


def _build_markdown(matrix, cases):
    lines = []
    lines.append("# Manual UAT Execution Template")
    lines.append("")
    lines.append(f"Generated at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## 1) Role / Host Matrix")
    lines.append("")
    lines.append("| Host | User | Role | Expected Scope | Actual | PASS/FAIL | Evidence |")
    lines.append("|---|---|---|---|---|---|---|")
    for row in matrix:
        lines.append(f"| {row['host']} | {row['user']} | {row['role']} | {row['scope']} |  |  |  |")
    lines.append("")
    lines.append("## 2) Critical Cases")
    lines.append("")
    lines.append("| ID | Scenario | Steps | Expected | Actual | PASS/FAIL | Evidence |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in cases:
        lines.append(f"| {c['id']} | {c['scenario']} | {c['steps']} | {c['expected']} |  |  |  |")
    lines.append("")
    lines.append("## 3) Evidence Naming Rule")
    lines.append("")
    lines.append("- Screenshot: `C-xx_<host>_<user>_<short-desc>.png`")
    lines.append("- Video(optional): `C-xx_<host>_<user>.mp4`")
    lines.append("- Log: `C-xx_<host>_<user>.txt`")
    lines.append("")
    return "\n".join(lines)


def main():
    root = Path(__file__).resolve().parents[1]
    date_key = datetime.now().strftime("%Y-%m-%d")
    out_dir = root / "docs" / "ux" / "uat_evidence" / date_key
    out_dir.mkdir(parents=True, exist_ok=True)

    screenshots_dir = out_dir / "screenshots"
    logs_dir = out_dir / "logs"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / "manual_uat_template.md"
    md_path.write_text(_build_markdown(ROLE_HOST_MATRIX, CRITICAL_CASES), encoding="utf-8")

    json_path = out_dir / "manual_uat_template.json"
    json_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "matrix": ROLE_HOST_MATRIX,
        "critical_cases": CRITICAL_CASES,
        "status": "PENDING-MANUAL",
    }
    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": "PASS",
        "output_dir": str(out_dir),
        "template_markdown": str(md_path),
        "template_json": str(json_path),
        "screenshots_dir": str(screenshots_dir),
        "logs_dir": str(logs_dir),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
