"""
Tenant-scoped receipt inbox store.
"""
import sqlite3
import json
from datetime import datetime


def _utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_receipt(row):
    if not row:
        return None
    return {
        "id": int(row["id"]),
        "host": row["host"],
        "uploader_user_id": int(row["uploader_user_id"]) if row["uploader_user_id"] else None,
        "uploader_email": row["uploader_email"] or "",
        "orig_filename": row["orig_filename"] or "",
        "stored_filename": row["stored_filename"] or "",
        "file_path": row["file_path"] or "",
        "file_hash": row["file_hash"] or "",
        "date": row["date"],
        "merchant": row["merchant"] or "",
        "amount": int(row["amount"] or 0),
        "currency": row["currency"] or "USD",
        "category": row["category"] or "MISCELLANEOUS",
        "memo": row["memo"] or "",
        "confidence": row["confidence"] or "low",
        "status": row["status"] or "needs_review",
        "lifecycle_state": row["lifecycle_state"] or "UPLOADED",
        "report_status": row["report_status"] or "unassigned",
        "report_id": int(row["report_id"]) if row["report_id"] else None,
        "duplicate_of": int(row["duplicate_of"]) if row["duplicate_of"] else None,
        "ocr_error": row["ocr_error"] or "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _row_to_report(row):
    if not row:
        return None
    return {
        "id": int(row["id"]),
        "host": row["host"],
        "creator_user_id": int(row["creator_user_id"]) if row["creator_user_id"] else None,
        "creator_email": row["creator_email"] or "",
        "title": row["title"] or "",
        "mode": row["mode"] or "domestic",
        "receipt_count": int(row["receipt_count"] or 0),
        "total_amount": float(row["total_amount"] or 0),
        "currency": row["currency"] or "USD",
        "employee_name": row["employee_name"] or "",
        "department": row["department"] or "",
        "employee_id": row["employee_id"] or "",
        "manager": row["manager"] or "",
        "project": row["project"] or "",
        "period_from": row["period_from"] or "",
        "period_to": row["period_to"] or "",
        "trip_purpose": row["trip_purpose"] or "",
        "notes": row["notes"] or "",
        "output_session_id": row["output_session_id"] or "",
        "output_filename": row["output_filename"] or "",
        "created_at": row["created_at"],
    }


def init_receipt_db(db_path: str):
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT NOT NULL,
                uploader_user_id INTEGER,
                uploader_email TEXT NOT NULL DEFAULT '',
                orig_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL DEFAULT '',
                date TEXT,
                merchant TEXT NOT NULL DEFAULT '',
                amount INTEGER NOT NULL DEFAULT 0,
                currency TEXT NOT NULL DEFAULT 'USD',
                category TEXT NOT NULL DEFAULT 'MISCELLANEOUS',
                memo TEXT NOT NULL DEFAULT '',
                confidence TEXT NOT NULL DEFAULT 'low',
                status TEXT NOT NULL DEFAULT 'needs_review',
                lifecycle_state TEXT NOT NULL DEFAULT 'UPLOADED',
                report_status TEXT NOT NULL DEFAULT 'unassigned',
                report_id INTEGER,
                duplicate_of INTEGER,
                ocr_error TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT NOT NULL,
                creator_user_id INTEGER,
                creator_email TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                mode TEXT NOT NULL DEFAULT 'domestic',
                receipt_count INTEGER NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL DEFAULT 0,
                currency TEXT NOT NULL DEFAULT 'USD',
                employee_name TEXT NOT NULL DEFAULT '',
                department TEXT NOT NULL DEFAULT '',
                employee_id TEXT NOT NULL DEFAULT '',
                manager TEXT NOT NULL DEFAULT '',
                project TEXT NOT NULL DEFAULT '',
                period_from TEXT NOT NULL DEFAULT '',
                period_to TEXT NOT NULL DEFAULT '',
                trip_purpose TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                output_session_id TEXT NOT NULL DEFAULT '',
                output_filename TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        receipt_cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(receipts)").fetchall()}
        if "lifecycle_state" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN lifecycle_state TEXT NOT NULL DEFAULT 'UPLOADED'")
        if "file_hash" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN file_hash TEXT NOT NULL DEFAULT ''")
        report_cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(reports)").fetchall()}
        report_extra_cols = [
            ("employee_name", "TEXT NOT NULL DEFAULT ''"),
            ("department", "TEXT NOT NULL DEFAULT ''"),
            ("employee_id", "TEXT NOT NULL DEFAULT ''"),
            ("manager", "TEXT NOT NULL DEFAULT ''"),
            ("project", "TEXT NOT NULL DEFAULT ''"),
            ("period_from", "TEXT NOT NULL DEFAULT ''"),
            ("period_to", "TEXT NOT NULL DEFAULT ''"),
            ("trip_purpose", "TEXT NOT NULL DEFAULT ''"),
            ("notes", "TEXT NOT NULL DEFAULT ''"),
        ]
        for col_name, col_def in report_extra_cols:
            if col_name not in report_cols:
                conn.execute(f"ALTER TABLE reports ADD COLUMN {col_name} {col_def}")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS category_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT NOT NULL,
                category_id TEXT NOT NULL,
                category_label TEXT NOT NULL DEFAULT '',
                account_code TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(host, category_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vendor_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT NOT NULL,
                vendor_name TEXT NOT NULL,
                suggested_category TEXT NOT NULL DEFAULT '',
                account_code TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(host, vendor_name)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS receipt_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT NOT NULL,
                receipt_id INTEGER NOT NULL,
                actor_user_id INTEGER,
                actor_email TEXT NOT NULL DEFAULT '',
                action TEXT NOT NULL DEFAULT 'update',
                changed_fields TEXT NOT NULL DEFAULT '[]',
                before_json TEXT NOT NULL DEFAULT '{}',
                after_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_host_created ON receipts(host, created_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_host_status ON receipts(host, status, report_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_host_key_fields ON receipts(host, merchant, amount, date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_host_hash ON receipts(host, file_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_host_created ON reports(host, created_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_category_mappings_host ON category_mappings(host)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vendor_mappings_host ON vendor_mappings(host)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_receipt_audit_host_receipt ON receipt_audit_logs(host, receipt_id, created_at DESC)")
        conn.commit()


def create_receipt(
    db_path: str,
    host: str,
    uploader_user_id: int | None,
    uploader_email: str,
    orig_filename: str,
    stored_filename: str,
    file_path: str,
    file_hash: str = "",
):
    now = _utc_now()
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO receipts(
                host, uploader_user_id, uploader_email,
                orig_filename, stored_filename, file_path, file_hash,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (host, uploader_user_id, uploader_email, orig_filename, stored_filename, file_path, file_hash or "", now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM receipts WHERE id = ?", (int(cur.lastrowid),)).fetchone()
    return _row_to_receipt(row)


def get_receipt(db_path: str, host: str, receipt_id: int):
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM receipts WHERE id = ? AND host = ?",
            (receipt_id, host),
        ).fetchone()
    return _row_to_receipt(row)


def find_receipt_by_hash(
    db_path: str,
    host: str,
    file_hash: str,
    uploader_user_id: int | None = None,
    only_unassigned: bool = True,
):
    if not file_hash:
        return None
    clauses = ["host = ?", "file_hash = ?"]
    args = [host, file_hash]
    if uploader_user_id is not None:
        clauses.append("uploader_user_id = ?")
        args.append(int(uploader_user_id))
    if only_unassigned:
        clauses.append("report_status = 'unassigned'")
    sql = (
        "SELECT * FROM receipts "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY id DESC LIMIT 1"
    )
    with _connect(db_path) as conn:
        row = conn.execute(sql, tuple(args)).fetchone()
    return _row_to_receipt(row)


def delete_receipt(db_path: str, host: str, receipt_id: int):
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM receipts WHERE id = ? AND host = ?",
            (receipt_id, host),
        ).fetchone()
        if not row:
            return None
        conn.execute(
            "DELETE FROM receipt_audit_logs WHERE receipt_id = ? AND host = ?",
            (receipt_id, host),
        )
        conn.execute(
            "DELETE FROM receipts WHERE id = ? AND host = ?",
            (receipt_id, host),
        )
        conn.commit()
    return _row_to_receipt(row)


def list_receipts(
    db_path: str,
    host: str,
    status: str | None = None,
    lifecycle_state: str | None = None,
    report_status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    merchant: str | None = None,
    min_amount: int | None = None,
    max_amount: int | None = None,
    search: str | None = None,
    limit: int = 200,
):
    clauses = ["host = ?"]
    args = [host]
    if status:
        clauses.append("status = ?")
        args.append(status)
    if lifecycle_state:
        clauses.append("lifecycle_state = ?")
        args.append(lifecycle_state)
    if report_status:
        clauses.append("report_status = ?")
        args.append(report_status)
    if date_from:
        clauses.append("date >= ?")
        args.append(date_from)
    if date_to:
        clauses.append("date <= ?")
        args.append(date_to)
    if category:
        clauses.append("category = ?")
        args.append(category)
    if merchant:
        clauses.append("merchant LIKE ?")
        args.append(f"%{merchant.strip()}%")
    if min_amount is not None:
        clauses.append("amount >= ?")
        args.append(int(min_amount))
    if max_amount is not None:
        clauses.append("amount <= ?")
        args.append(int(max_amount))
    exact_id = None
    if search:
        s = search.strip()
        s_id = s[1:] if s.startswith("#") else s
        q = f"%{s}%"
        if s_id.isdigit():
            exact_id = int(s_id)
            clauses.append("(id = ? OR merchant LIKE ? OR memo LIKE ? OR orig_filename LIKE ?)")
            args.extend([exact_id, q, q, q])
        else:
            clauses.append("(merchant LIKE ? OR memo LIKE ? OR orig_filename LIKE ?)")
            args.extend([q, q, q])
    order_by = "created_at DESC, id DESC"
    if exact_id is not None:
        order_by = "CASE WHEN id = ? THEN 0 ELSE 1 END, created_at DESC, id DESC"
    sql = (
        "SELECT * FROM receipts "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY {order_by} LIMIT ?"
    )
    if exact_id is not None:
        args.append(exact_id)
    args.append(max(1, min(int(limit), 1000)))
    with _connect(db_path) as conn:
        rows = conn.execute(sql, tuple(args)).fetchall()
    return [_row_to_receipt(r) for r in rows]


def list_receipts_for_report(
    db_path: str,
    host: str,
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    merchant: str | None = None,
    min_amount: int | None = None,
    max_amount: int | None = None,
    only_unassigned: bool = False,
    status: str | None = None,
    limit: int = 1000,
):
    clauses = ["host = ?"]
    args = [host]
    if date_from:
        clauses.append("date >= ?")
        args.append(date_from)
    if date_to:
        clauses.append("date <= ?")
        args.append(date_to)
    if category:
        clauses.append("category = ?")
        args.append(category)
    if merchant:
        clauses.append("merchant LIKE ?")
        args.append(f"%{merchant.strip()}%")
    if min_amount is not None:
        clauses.append("amount >= ?")
        args.append(int(min_amount))
    if max_amount is not None:
        clauses.append("amount <= ?")
        args.append(int(max_amount))
    if only_unassigned:
        clauses.append("report_status = 'unassigned'")
    if status:
        clauses.append("status = ?")
        args.append(status)
    sql = (
        "SELECT * FROM receipts "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY date ASC, id ASC LIMIT ?"
    )
    args.append(max(1, min(int(limit), 5000)))
    with _connect(db_path) as conn:
        rows = conn.execute(sql, tuple(args)).fetchall()
    return [_row_to_receipt(r) for r in rows]


def find_duplicate_receipt(
    db_path: str,
    host: str,
    receipt_id: int,
    merchant: str | None,
    amount: int | None,
    date: str | None,
):
    merchant_norm = (merchant or "").strip().upper()
    if not merchant_norm or not date or int(amount or 0) <= 0:
        return None
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT * FROM receipts
            WHERE host = ?
              AND id != ?
              AND UPPER(TRIM(merchant)) = ?
              AND amount = ?
              AND date = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (host, receipt_id, merchant_norm, int(amount), date),
        ).fetchone()
    return _row_to_receipt(row)


def update_receipt(db_path: str, host: str, receipt_id: int, fields: dict):
    allowed = {
        "date", "merchant", "amount", "currency", "category",
        "memo", "confidence", "status", "lifecycle_state", "report_status", "report_id",
        "duplicate_of", "ocr_error",
    }
    updates = []
    values = []
    for key, value in (fields or {}).items():
        if key not in allowed:
            continue
        updates.append(f"{key} = ?")
        values.append(value)
    if not updates:
        return get_receipt(db_path, host, receipt_id)
    updates.append("updated_at = ?")
    values.append(_utc_now())
    values.extend([receipt_id, host])
    with _connect(db_path) as conn:
        cur = conn.execute(
            f"UPDATE receipts SET {', '.join(updates)} WHERE id = ? AND host = ?",
            tuple(values),
        )
        if cur.rowcount == 0:
            return None
        conn.commit()
        row = conn.execute("SELECT * FROM receipts WHERE id = ? AND host = ?", (receipt_id, host)).fetchone()
    return _row_to_receipt(row)


def create_report(
    db_path: str,
    host: str,
    creator_user_id: int | None,
    creator_email: str,
    title: str,
    mode: str,
    receipt_count: int,
    total_amount: float,
    currency: str,
    output_session_id: str,
    output_filename: str,
    employee_name: str = "",
    department: str = "",
    employee_id: str = "",
    manager: str = "",
    project: str = "",
    period_from: str = "",
    period_to: str = "",
    trip_purpose: str = "",
    notes: str = "",
):
    now = _utc_now()
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO reports(
                host, creator_user_id, creator_email, title, mode,
                receipt_count, total_amount, currency,
                employee_name, department, employee_id, manager, project, period_from, period_to, trip_purpose, notes,
                output_session_id, output_filename, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                host, creator_user_id, creator_email, title, mode,
                int(receipt_count), float(total_amount), currency,
                employee_name or "", department or "", employee_id or "", manager or "", project or "",
                period_from or "", period_to or "", trip_purpose or "", notes or "",
                output_session_id, output_filename, now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (int(cur.lastrowid),)).fetchone()
    return _row_to_report(row)


def list_reports(db_path: str, host: str, limit: int = 100):
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM reports
            WHERE host = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (host, max(1, min(int(limit), 500))),
        ).fetchall()
    return [_row_to_report(r) for r in rows]


def get_report(db_path: str, host: str, report_id: int):
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT * FROM reports
            WHERE host = ? AND id = ?
            LIMIT 1
            """,
            (host, int(report_id)),
        ).fetchone()
    return _row_to_report(row)


def list_receipts_by_report_id(db_path: str, host: str, report_id: int, limit: int = 2000):
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM receipts
            WHERE host = ? AND report_id = ?
            ORDER BY date ASC, id ASC
            LIMIT ?
            """,
            (host, int(report_id), max(1, min(int(limit), 5000))),
        ).fetchall()
    return [_row_to_receipt(r) for r in rows]


def get_report_by_output(db_path: str, host: str, output_session_id: str, output_filename: str):
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT * FROM reports
            WHERE host = ? AND output_session_id = ? AND output_filename = ?
            LIMIT 1
            """,
            (host, output_session_id, output_filename),
        ).fetchone()
    return _row_to_report(row)


def upsert_category_mapping(
    db_path: str,
    host: str,
    category_id: str,
    category_label: str,
    account_code: str,
):
    cat = (category_id or "").strip().upper()
    if not cat:
        raise ValueError("category_id is required")
    now = _utc_now()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM category_mappings WHERE host = ? AND category_id = ?",
            (host, cat),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE category_mappings
                SET category_label = ?, account_code = ?, updated_at = ?
                WHERE host = ? AND category_id = ?
                """,
                (category_label or cat, account_code or "", now, host, cat),
            )
        else:
            conn.execute(
                """
                INSERT INTO category_mappings(
                    host, category_id, category_label, account_code, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (host, cat, category_label or cat, account_code or "", now, now),
            )
        conn.commit()


def list_category_mappings(db_path: str, host: str):
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, host, category_id, category_label, account_code, created_at, updated_at
            FROM category_mappings
            WHERE host = ?
            ORDER BY category_id ASC
            """,
            (host,),
        ).fetchall()
    return [
        {
            "id": int(r["id"]),
            "host": r["host"],
            "category_id": r["category_id"],
            "category_label": r["category_label"] or "",
            "account_code": r["account_code"] or "",
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


def upsert_vendor_mapping(
    db_path: str,
    host: str,
    vendor_name: str,
    suggested_category: str = "",
    account_code: str = "",
):
    vendor = (vendor_name or "").strip().upper()
    if not vendor:
        raise ValueError("vendor_name is required")
    now = _utc_now()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM vendor_mappings WHERE host = ? AND vendor_name = ?",
            (host, vendor),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE vendor_mappings
                SET suggested_category = ?, account_code = ?, updated_at = ?
                WHERE host = ? AND vendor_name = ?
                """,
                ((suggested_category or "").strip().upper(), (account_code or "").strip(), now, host, vendor),
            )
        else:
            conn.execute(
                """
                INSERT INTO vendor_mappings(host, vendor_name, suggested_category, account_code, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (host, vendor, (suggested_category or "").strip().upper(), (account_code or "").strip(), now, now),
            )
        conn.commit()


def list_vendor_mappings(db_path: str, host: str):
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, host, vendor_name, suggested_category, account_code, created_at, updated_at
            FROM vendor_mappings
            WHERE host = ?
            ORDER BY vendor_name ASC
            """,
            (host,),
        ).fetchall()
    return [
        {
            "id": int(r["id"]),
            "host": r["host"],
            "vendor_name": r["vendor_name"] or "",
            "suggested_category": r["suggested_category"] or "",
            "account_code": r["account_code"] or "",
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


def create_receipt_audit_log(
    db_path: str,
    host: str,
    receipt_id: int,
    actor_user_id: int | None,
    actor_email: str,
    action: str,
    changed_fields: list[str],
    before_json: str,
    after_json: str,
):
    now = _utc_now()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO receipt_audit_logs(
                host, receipt_id, actor_user_id, actor_email, action,
                changed_fields, before_json, after_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                host, int(receipt_id), actor_user_id, actor_email or "", action or "update",
                json.dumps(changed_fields or [], ensure_ascii=False), before_json or "{}", after_json or "{}", now,
            ),
        )
        conn.commit()


def list_receipt_audit_logs(db_path: str, host: str, receipt_id: int, limit: int = 100):
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM receipt_audit_logs
            WHERE host = ? AND receipt_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (host, int(receipt_id), max(1, min(int(limit), 500))),
        ).fetchall()
    return [
        {
            "id": int(r["id"]),
            "host": r["host"],
            "receipt_id": int(r["receipt_id"]),
            "actor_user_id": int(r["actor_user_id"]) if r["actor_user_id"] else None,
            "actor_email": r["actor_email"] or "",
            "action": r["action"] or "update",
            "changed_fields": r["changed_fields"] or "[]",
            "before_json": r["before_json"] or "{}",
            "after_json": r["after_json"] or "{}",
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def list_receipt_audit_logs_by_host(
    db_path: str,
    host: str,
    user_email: str | None = None,
    receipt_id: int | None = None,
    limit: int = 500,
):
    clauses = ["host = ?"]
    args = [host]
    if user_email:
        clauses.append("LOWER(actor_email) = ?")
        args.append((user_email or "").strip().lower())
    if receipt_id is not None:
        clauses.append("receipt_id = ?")
        args.append(int(receipt_id))
    sql = (
        "SELECT * FROM receipt_audit_logs "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY created_at DESC, id DESC LIMIT ?"
    )
    args.append(max(1, min(int(limit), 2000)))
    with _connect(db_path) as conn:
        rows = conn.execute(sql, tuple(args)).fetchall()
    return [
        {
            "id": int(r["id"]),
            "host": r["host"],
            "receipt_id": int(r["receipt_id"]),
            "actor_user_id": int(r["actor_user_id"]) if r["actor_user_id"] else None,
            "actor_email": r["actor_email"] or "",
            "action": r["action"] or "update",
            "changed_fields": r["changed_fields"] or "[]",
            "before_json": r["before_json"] or "{}",
            "after_json": r["after_json"] or "{}",
            "created_at": r["created_at"],
        }
        for r in rows
    ]
