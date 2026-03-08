import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app as webapp
from receipt_inbox_db import init_receipt_db, create_receipt
from user_db import init_user_db, upsert_user_by_email, set_user_host_permissions


HOST = "tenant-a.local"


def _set_session(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = int(user["id"])
        sess["user_email"] = user["email"]
        sess["user_name"] = user.get("name") or ""
        sess["auth_provider"] = "local"
        sess["is_admin"] = bool(user.get("is_admin"))


def _expect(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    with tempfile.TemporaryDirectory(prefix="ezworks-smoke-", ignore_cleanup_errors=True) as tmpdir:
        tmp = Path(tmpdir)
        user_db = tmp / "users.db"
        receipt_db = tmp / "receipt.db"
        upload_root = tmp / "uploads"
        upload_root.mkdir(parents=True, exist_ok=True)

        # Isolate this smoke run from dev DB/files.
        webapp.USER_DB_PATH = user_db
        webapp.RECEIPT_DB_PATH = receipt_db

        init_user_db(str(user_db))
        init_receipt_db(str(receipt_db))

        user_a = upsert_user_by_email(str(user_db), "user.a@tenant.com", "User A", is_admin=False)
        user_b = upsert_user_by_email(str(user_db), "user.b@tenant.com", "User B", is_admin=False)
        accounting = upsert_user_by_email(str(user_db), "acct@tenant.com", "Accounting", is_admin=False)

        set_user_host_permissions(
            str(user_db),
            int(accounting["id"]),
            HOST,
            ["receipt.view_all", "report.view_all", "report.generate", "mapping.manage", "category.manage"],
        )

        f1 = upload_root / "a.jpg"
        f1.write_bytes(b"fake-a")
        f2 = upload_root / "b.jpg"
        f2.write_bytes(b"fake-b")

        row_a = create_receipt(
            db_path=str(receipt_db),
            host=HOST,
            uploader_user_id=int(user_a["id"]),
            uploader_email=user_a["email"],
            orig_filename="a.jpg",
            stored_filename="a.jpg",
            file_path=str(f1),
        )
        row_b = create_receipt(
            db_path=str(receipt_db),
            host=HOST,
            uploader_user_id=int(user_b["id"]),
            uploader_email=user_b["email"],
            orig_filename="b.jpg",
            stored_filename="b.jpg",
            file_path=str(f2),
        )

        client = webapp.app.test_client()

        tenant_headers = {"X-Forwarded-Host": HOST}

        # 1) own-scope user sees only own receipts
        _set_session(client, user_a)
        res = client.get("/api/inbox/receipts", headers=tenant_headers)
        payload = res.get_json() or {}
        ids = {int(x.get("id")) for x in payload.get("receipts") or []}
        _expect(res.status_code == 200, f"user_a receipt list failed: {res.status_code}")
        _expect(row_a["id"] in ids, "user_a must see own receipt")
        _expect(row_b["id"] not in ids, "user_a must not see user_b receipt")

        # 2) own-scope user is blocked from other user's detail/image/audit
        r_detail = client.get(f"/api/inbox/receipts/{int(row_b['id'])}", headers=tenant_headers)
        r_img = client.get(f"/api/inbox/image/{int(row_b['id'])}", headers=tenant_headers)
        r_audit = client.get(f"/api/inbox/receipts/{int(row_b['id'])}/audit", headers=tenant_headers)
        _expect(r_detail.status_code == 403, f"cross detail must be 403, got {r_detail.status_code}")
        _expect(r_img.status_code == 403, f"cross image must be 403, got {r_img.status_code}")
        _expect(r_audit.status_code == 403, f"cross audit must be 403, got {r_audit.status_code}")

        # 3) receipt.view_all user sees both and can filter by uploader email
        _set_session(client, accounting)
        res_all = client.get("/api/inbox/receipts", headers=tenant_headers)
        payload_all = res_all.get_json() or {}
        ids_all = {int(x.get("id")) for x in payload_all.get("receipts") or []}
        _expect(res_all.status_code == 200, f"accounting list failed: {res_all.status_code}")
        _expect(row_a["id"] in ids_all and row_b["id"] in ids_all, "accounting must see all tenant receipts")

        res_filter = client.get(
            f"/api/inbox/receipts?user_email={user_b['email']}",
            headers=tenant_headers,
        )
        payload_filter = res_filter.get_json() or {}
        ids_filter = [int(x.get("id")) for x in payload_filter.get("receipts") or []]
        _expect(res_filter.status_code == 200, f"accounting filtered list failed: {res_filter.status_code}")
        _expect(ids_filter == [int(row_b["id"])], f"filtered result mismatch: {ids_filter}")

        # 4) cross-tenant isolation: same user session on other host must not see HOST rows
        res_other = client.get("/api/inbox/receipts", headers={"X-Forwarded-Host": "localhost"})
        payload_other = res_other.get_json() or {}
        _expect(res_other.status_code == 200, f"other host list failed: {res_other.status_code}")
        _expect((payload_other.get("count") or 0) == 0, "other host should not expose tenant-a rows")

        result = {
            "status": "PASS",
            "host": HOST,
            "checks": [
                "own_scope_receipt_list",
                "cross_user_detail_image_audit_forbidden",
                "view_all_scope_and_user_filter",
                "host_isolation",
            ],
            "sample_receipt_ids": [int(row_a["id"]), int(row_b["id"])],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
