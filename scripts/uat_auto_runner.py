import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app as webapp
from receipt_inbox_db import create_receipt, init_receipt_db
from user_db import init_user_db, set_user_host_permissions, upsert_user_by_email


def _set_session(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = int(user["id"])
        sess["user_email"] = user["email"]
        sess["user_name"] = user.get("name") or ""
        sess["auth_provider"] = "local"
        sess["is_admin"] = bool(user.get("is_admin"))


def _case(case_id, title):
    return {"id": case_id, "title": title, "status": "PENDING", "details": "", "evidence": []}


def _pass(c, details="", evidence=None):
    c["status"] = "PASS"
    c["details"] = details
    c["evidence"] = evidence or []
    return c


def _fail(c, details="", evidence=None):
    c["status"] = "FAIL"
    c["details"] = details
    c["evidence"] = evidence or []
    return c


def run():
    cases = [
        _case("C-01", "Anonymous redirect"),
        _case("C-02", "Host isolation"),
        _case("C-03", "Cross-tenant admin guard"),
        _case("C-04", "Receipt ownership scope"),
        _case("C-05", "Admin monitor drill-down links"),
        _case("C-06", "Wizard step separation"),
        _case("C-07", "Unsaved edit guard wiring"),
        _case("C-08", "Accounting permission boundary"),
    ]
    by_id = {c["id"]: c for c in cases}

    with tempfile.TemporaryDirectory(prefix="ezworks-uat-auto-", ignore_cleanup_errors=True) as tmpdir:
        tmp = Path(tmpdir)
        user_db = tmp / "users.db"
        receipt_db = tmp / "receipt.db"
        upload_root = tmp / "uploads"
        config_dir = tmp / "configs"
        config_path = tmp / "config.json"
        upload_root.mkdir(parents=True, exist_ok=True)
        config_dir.mkdir(parents=True, exist_ok=True)

        # isolate app globals
        webapp.USER_DB_PATH = user_db
        webapp.RECEIPT_DB_PATH = receipt_db
        webapp.CONFIG_DIR = config_dir
        webapp.CONFIG_PATH = config_path

        init_user_db(str(user_db))
        init_receipt_db(str(receipt_db))
        config_path.write_text(json.dumps(webapp.DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")

        host_a = "tenant-a.local"
        host_b = "tenant-b.local"
        cfg_a = json.loads(json.dumps(webapp.DEFAULT_CONFIG))
        cfg_a["auth"]["admin_emails"] = ["tenant.admin@tenant.com"]
        cfg_b = json.loads(json.dumps(webapp.DEFAULT_CONFIG))
        cfg_b["auth"]["admin_emails"] = []
        (config_dir / f"{host_a}.json").write_text(json.dumps(cfg_a, ensure_ascii=False, indent=2), encoding="utf-8")
        (config_dir / f"{host_b}.json").write_text(json.dumps(cfg_b, ensure_ascii=False, indent=2), encoding="utf-8")

        general_a = upsert_user_by_email(str(user_db), "user.a@tenant.com", "User A", is_admin=False)
        general_b = upsert_user_by_email(str(user_db), "user.b@tenant.com", "User B", is_admin=False)
        tenant_admin = upsert_user_by_email(str(user_db), "tenant.admin@tenant.com", "Tenant Admin", is_admin=False)
        accounting = upsert_user_by_email(str(user_db), "acct@tenant.com", "Accounting", is_admin=False)
        set_user_host_permissions(
            str(user_db),
            int(accounting["id"]),
            host_a,
            ["receipt.view_all", "report.view_all", "report.generate", "mapping.manage", "category.manage"],
        )

        img_a = upload_root / "a.jpg"
        img_b = upload_root / "b.jpg"
        img_a.write_bytes(b"a")
        img_b.write_bytes(b"b")
        row_a = create_receipt(str(receipt_db), host_a, int(general_a["id"]), general_a["email"], "a.jpg", "a.jpg", str(img_a))
        row_b = create_receipt(str(receipt_db), host_a, int(general_b["id"]), general_b["email"], "b.jpg", "b.jpg", str(img_b))

        client = webapp.app.test_client()

        # C-01
        r1 = client.get("/dashboard")
        if r1.status_code in (301, 302) and "/login" in (r1.headers.get("Location") or ""):
            _pass(by_id["C-01"], "redirects to /login")
        else:
            _fail(by_id["C-01"], f"unexpected response: {r1.status_code} {r1.headers.get('Location')}")

        # C-02
        cfg_a2 = webapp.load_config(host_a)
        cfg_b2 = webapp.load_config(host_b)
        cfg_a2["company"]["name"] = "Tenant A Name"
        webapp.save_config(cfg_a2, host_a)
        cfg_b_after = webapp.load_config(host_b)
        if cfg_b_after.get("company", {}).get("name", "") == cfg_b2.get("company", {}).get("name", ""):
            _pass(by_id["C-02"], "host-specific config remained isolated")
        else:
            _fail(by_id["C-02"], "tenant-b config changed while saving tenant-a config")

        # C-03
        _set_session(client, tenant_admin)
        r3 = client.get(f"/admin/user-permissions?host={host_b}", headers={"X-Forwarded-Host": host_a})
        if r3.status_code == 403:
            _pass(by_id["C-03"], "cross-tenant admin request blocked")
        else:
            _fail(by_id["C-03"], f"expected 403, got {r3.status_code}")

        # C-04
        _set_session(client, general_a)
        r4_list = client.get("/api/inbox/receipts", headers={"X-Forwarded-Host": host_a})
        r4_detail_other = client.get(f"/api/inbox/receipts/{int(row_b['id'])}", headers={"X-Forwarded-Host": host_a})
        if r4_list.status_code == 200 and r4_detail_other.status_code == 403:
            payload = r4_list.get_json() or {}
            ids = {int(x.get("id")) for x in payload.get("receipts") or []}
            if int(row_a["id"]) in ids and int(row_b["id"]) not in ids:
                _pass(by_id["C-04"], "own-scope list/detail guard works")
            else:
                _fail(by_id["C-04"], f"unexpected list ids={sorted(ids)}")
        else:
            _fail(by_id["C-04"], f"list/detail status {r4_list.status_code}/{r4_detail_other.status_code}")

        # C-05
        admin_tpl = (ROOT_DIR / "templates" / "admin.html").read_text(encoding="utf-8")
        need_tokens = [
            "monitorLinkToInboxByUser",
            "monitorLinkToReportsByUser",
            "monitorLinkToInboxReceipt",
            'searchParams.set("aback"',
        ]
        if all(t in admin_tpl for t in need_tokens):
            _pass(by_id["C-05"], "admin monitor drill-down link helpers present")
        else:
            _fail(by_id["C-05"], "missing one or more monitor link helpers")

        # C-06
        nav_tpl = (ROOT_DIR / "templates" / "_module_nav.html").read_text(encoding="utf-8")
        wiz_tpl = (ROOT_DIR / "templates" / "_wizard_progress.html").read_text(encoding="utf-8")
        nav_ok = all(x in nav_tpl for x in ["Dashboard", "Inbox", "Reports", "Admin"])
        nav_not_wiz = all(x not in nav_tpl for x in ["1. Settings", "2. Upload", "3. OCR", "4. Review", "5. Generate"])
        wiz_ok = all(x in wiz_tpl for x in ["/reports/wizard/settings", "/reports/wizard/upload", "/reports/wizard/ocr", "/reports/wizard/review", "/reports/wizard/generate"])
        if nav_ok and nav_not_wiz and wiz_ok:
            _pass(by_id["C-06"], "module nav and wizard separation maintained")
        else:
            _fail(by_id["C-06"], "module/wizard separation contract broken")

        # C-07
        step4 = (ROOT_DIR / "templates" / "report_wizard_review.html").read_text(encoding="utf-8")
        step5 = (ROOT_DIR / "templates" / "report_wizard_generate.html").read_text(encoding="utf-8")
        dirty_ok = ("report_wizard_dirty_ids_v1" in step4) and ("report_wizard_dirty_ids_v1" in step5)
        guard_ok = ("Unsaved edits" in step5) and ("go to Step 4" in step5 or "Step 4" in step5)
        if dirty_ok and guard_ok:
            _pass(by_id["C-07"], "dirty-state + generate guard wiring detected")
        else:
            _fail(by_id["C-07"], "unsaved guard wiring not found in templates")

        # C-08
        _set_session(client, general_a)
        r8 = client.get("/inbox/settings", headers={"X-Forwarded-Host": host_a})
        loc8 = r8.headers.get("Location") or ""
        if r8.status_code in (301, 302) and "/inbox/review" in loc8:
            _pass(by_id["C-08"], "non-accounting user redirected from settings")
        else:
            _fail(by_id["C-08"], f"expected redirect to /inbox/review, got {r8.status_code} {loc8}")

    fail_count = sum(1 for c in cases if c["status"] == "FAIL")
    pending_count = sum(1 for c in cases if c["status"] == "PENDING")
    gate = "GO" if fail_count == 0 and pending_count == 0 else "NO-GO"
    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "PASS",
        "gate": gate,
        "counts": {
            "PASS": sum(1 for c in cases if c["status"] == "PASS"),
            "FAIL": fail_count,
            "PENDING": pending_count,
        },
        "cases": cases,
    }
    return result


def to_markdown(result: dict) -> str:
    lines = []
    lines.append("# Auto UAT Result (2nd Pass)")
    lines.append("")
    lines.append(f"Generated at: {result['generated_at']}")
    lines.append(f"Gate: **{result['gate']}**")
    lines.append("")
    lines.append("| ID | Scenario | Status | Details |")
    lines.append("|---|---|---|---|")
    for c in result["cases"]:
        lines.append(f"| {c['id']} | {c['title']} | {c['status']} | {c['details']} |")
    lines.append("")
    return "\n".join(lines)


def main():
    result = run()
    out_dir = ROOT_DIR / "docs" / "ux" / "uat_evidence" / datetime.now().strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "uat_auto_result_2nd_pass.json"
    out_md = out_dir / "uat_auto_result_2nd_pass.md"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(to_markdown(result), encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "gate": result["gate"],
        "json": str(out_json),
        "markdown": str(out_md),
        "counts": result["counts"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
