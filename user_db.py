"""
Local user/identity store for SSO integration.
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


def init_user_db(db_path: str):
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT DEFAULT '',
                tenant_id TEXT DEFAULT '',
                org_name TEXT DEFAULT '',
                is_admin INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                provider_user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(provider, provider_user_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_identities_user_id ON identities(user_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_host_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                host TEXT NOT NULL,
                permissions_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, host),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_host_permissions_host ON user_host_permissions(host)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inbox_filter_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                host TEXT NOT NULL,
                preset_name TEXT NOT NULL,
                filters_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, host, preset_name),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_inbox_filter_presets_user_host ON inbox_filter_presets(user_id, host)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inbox_shared_filter_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT NOT NULL,
                preset_name TEXT NOT NULL,
                filters_json TEXT NOT NULL DEFAULT '{}',
                created_by_user_id INTEGER,
                created_by_email TEXT NOT NULL DEFAULT '',
                is_locked INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(host, preset_name)
            )
            """
        )
        cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(inbox_shared_filter_presets)").fetchall()}
        if "is_locked" not in cols:
            conn.execute("ALTER TABLE inbox_shared_filter_presets ADD COLUMN is_locked INTEGER NOT NULL DEFAULT 0")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_inbox_shared_filter_presets_host ON inbox_shared_filter_presets(host)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_wizard_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                host TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'default',
                risk_priority_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, host),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_wizard_preferences_user_host ON user_wizard_preferences(user_id, host)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inbox_shared_filter_preset_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT NOT NULL,
                preset_name TEXT NOT NULL,
                actor_user_id INTEGER,
                actor_email TEXT NOT NULL DEFAULT '',
                action TEXT NOT NULL DEFAULT 'update',
                before_json TEXT NOT NULL DEFAULT '{}',
                after_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_shared_preset_audit_host_name ON inbox_shared_filter_preset_audit_logs(host, preset_name, created_at DESC)"
        )
        conn.commit()


def _row_to_user(row):
    if not row:
        return None
    return {
        "id": int(row["id"]),
        "email": row["email"],
        "name": row["name"] or "",
        "tenant_id": row["tenant_id"] or "",
        "org_name": row["org_name"] or "",
        "is_admin": bool(row["is_admin"]),
        "is_active": bool(row["is_active"]),
    }


def get_user_by_id(db_path: str, user_id: int):
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_user(row)


def list_users(db_path: str):
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, email, name, tenant_id, org_name, is_admin, is_active, created_at, updated_at
            FROM users
            ORDER BY is_admin DESC, updated_at DESC, id DESC
            """
        ).fetchall()
    result = []
    for row in rows:
        item = _row_to_user(row)
        item["created_at"] = row["created_at"]
        item["updated_at"] = row["updated_at"]
        result.append(item)
    return result


def update_user_flags(db_path: str, user_id: int, is_admin=None, is_active=None):
    updates = []
    values = []
    if is_admin is not None:
        updates.append("is_admin = ?")
        values.append(int(bool(is_admin)))
    if is_active is not None:
        updates.append("is_active = ?")
        values.append(int(bool(is_active)))
    if not updates:
        raise ValueError("no updates requested")

    now = _utc_now()
    updates.append("updated_at = ?")
    values.append(now)
    values.append(user_id)

    with _connect(db_path) as conn:
        cur = conn.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            tuple(values),
        )
        if cur.rowcount == 0:
            raise ValueError("user not found")
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_user(row)


def upsert_user_by_email(db_path: str, email: str, name: str = "", is_admin: bool = False):
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("email is required")
    now = _utc_now()
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            conn.execute(
                "UPDATE users SET name = ?, is_admin = ?, updated_at = ? WHERE id = ?",
                (name or row["name"] or "", int(bool(is_admin)), now, int(row["id"])),
            )
            conn.commit()
            updated = conn.execute("SELECT * FROM users WHERE id = ?", (int(row["id"]),)).fetchone()
            return _row_to_user(updated)
        cur = conn.execute(
            """
            INSERT INTO users(email, name, tenant_id, org_name, is_admin, is_active, created_at, updated_at)
            VALUES (?, ?, '', '', ?, 1, ?, ?)
            """,
            (email, name or "", int(bool(is_admin)), now, now),
        )
        conn.commit()
        created = conn.execute("SELECT * FROM users WHERE id = ?", (int(cur.lastrowid),)).fetchone()
    return _row_to_user(created)


def upsert_user_from_oidc(
    db_path: str,
    provider: str,
    provider_user_id: str,
    email: str,
    name: str = "",
    tenant_id: str = "",
    org_name: str = "",
    admin_emails=None,
):
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("email is required")
    provider = (provider or "").strip().lower()
    if not provider:
        raise ValueError("provider is required")
    provider_user_id = (provider_user_id or "").strip()
    if not provider_user_id:
        raise ValueError("provider_user_id is required")

    admin_emails = {x.strip().lower() for x in (admin_emails or set()) if x}
    now = _utc_now()

    with _connect(db_path) as conn:
        ident = conn.execute(
            "SELECT * FROM identities WHERE provider = ? AND provider_user_id = ?",
            (provider, provider_user_id),
        ).fetchone()

        if ident:
            user_id = int(ident["user_id"])
            user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user_row:
                raise RuntimeError("identity exists but linked user was not found")

            is_admin = bool(user_row["is_admin"]) or (email in admin_emails)
            conn.execute(
                """
                UPDATE users
                SET email = ?, name = ?, tenant_id = ?, org_name = ?, is_admin = ?, updated_at = ?
                WHERE id = ?
                """,
                (email, name or "", tenant_id or "", org_name or "", int(is_admin), now, user_id),
            )
            conn.execute(
                "UPDATE identities SET email = ?, updated_at = ? WHERE id = ?",
                (email, now, int(ident["id"])),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _row_to_user(row)

        user_row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user_row:
            user_id = int(user_row["id"])
            is_admin = bool(user_row["is_admin"]) or (email in admin_emails)
            conn.execute(
                """
                UPDATE users
                SET name = ?, tenant_id = ?, org_name = ?, is_admin = ?, updated_at = ?
                WHERE id = ?
                """,
                (name or "", tenant_id or "", org_name or "", int(is_admin), now, user_id),
            )
        else:
            is_admin = email in admin_emails
            cur = conn.execute(
                """
                INSERT INTO users(email, name, tenant_id, org_name, is_admin, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (email, name or "", tenant_id or "", org_name or "", int(is_admin), now, now),
            )
            user_id = int(cur.lastrowid)

        conn.execute(
            """
            INSERT INTO identities(user_id, provider, provider_user_id, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, provider, provider_user_id, email, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_user(row)


def get_user_host_permissions(db_path: str, user_id: int, host: str):
    host = (host or "").strip().lower()
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT permissions_json
            FROM user_host_permissions
            WHERE user_id = ? AND host = ?
            """,
            (int(user_id), host),
        ).fetchone()
    if not row:
        return set()
    try:
        raw = json.loads(row["permissions_json"] or "[]")
    except Exception:
        raw = []
    return {str(x).strip() for x in raw if str(x).strip()}


def set_user_host_permissions(db_path: str, user_id: int, host: str, permissions):
    host = (host or "").strip().lower()
    if not host:
        raise ValueError("host is required")
    user_id = int(user_id)
    normalized = sorted({str(x).strip() for x in (permissions or []) if str(x).strip()})
    payload = json.dumps(normalized, ensure_ascii=False)
    now = _utc_now()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM user_host_permissions WHERE user_id = ? AND host = ?",
            (user_id, host),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE user_host_permissions
                SET permissions_json = ?, updated_at = ?
                WHERE user_id = ? AND host = ?
                """,
                (payload, now, user_id, host),
            )
        else:
            conn.execute(
                """
                INSERT INTO user_host_permissions(user_id, host, permissions_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, host, payload, now, now),
            )
        conn.commit()
    return normalized


def list_user_host_permissions(db_path: str, host: str):
    host = (host or "").strip().lower()
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT uhp.user_id, uhp.host, uhp.permissions_json, uhp.updated_at,
                   u.email, u.name, u.is_admin, u.is_active
            FROM user_host_permissions uhp
            JOIN users u ON u.id = uhp.user_id
            WHERE uhp.host = ?
            ORDER BY u.email ASC
            """,
            (host,),
        ).fetchall()
    result = []
    for row in rows:
        try:
            perms = json.loads(row["permissions_json"] or "[]")
        except Exception:
            perms = []
        result.append(
            {
                "user_id": int(row["user_id"]),
                "host": row["host"],
                "email": row["email"] or "",
                "name": row["name"] or "",
                "is_admin": bool(row["is_admin"]),
                "is_active": bool(row["is_active"]),
                "permissions": sorted({str(x).strip() for x in perms if str(x).strip()}),
                "updated_at": row["updated_at"],
            }
        )
    return result


def list_inbox_filter_presets(db_path: str, user_id: int, host: str):
    host = (host or "").strip().lower()
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT preset_name, filters_json, updated_at
            FROM inbox_filter_presets
            WHERE user_id = ? AND host = ?
            ORDER BY preset_name ASC
            """,
            (int(user_id), host),
        ).fetchall()
    items = []
    for r in rows:
        try:
            filters = json.loads(r["filters_json"] or "{}")
        except Exception:
            filters = {}
        items.append(
            {
                "preset_name": r["preset_name"] or "",
                "filters": filters if isinstance(filters, dict) else {},
                "updated_at": r["updated_at"],
            }
        )
    return items


def upsert_inbox_filter_preset(db_path: str, user_id: int, host: str, preset_name: str, filters: dict):
    host = (host or "").strip().lower()
    name = (preset_name or "").strip()
    if not name:
        raise ValueError("preset_name is required")
    payload = json.dumps(filters or {}, ensure_ascii=False)
    now = _utc_now()
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id
            FROM inbox_filter_presets
            WHERE user_id = ? AND host = ? AND preset_name = ?
            """,
            (int(user_id), host, name),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE inbox_filter_presets
                SET filters_json = ?, updated_at = ?
                WHERE user_id = ? AND host = ? AND preset_name = ?
                """,
                (payload, now, int(user_id), host, name),
            )
        else:
            conn.execute(
                """
                INSERT INTO inbox_filter_presets(user_id, host, preset_name, filters_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (int(user_id), host, name, payload, now, now),
            )
        conn.commit()
    return {"preset_name": name, "filters": filters or {}, "updated_at": now}


def delete_inbox_filter_preset(db_path: str, user_id: int, host: str, preset_name: str):
    host = (host or "").strip().lower()
    name = (preset_name or "").strip()
    if not name:
        raise ValueError("preset_name is required")
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            DELETE FROM inbox_filter_presets
            WHERE user_id = ? AND host = ? AND preset_name = ?
            """,
            (int(user_id), host, name),
        )
        conn.commit()
    return cur.rowcount > 0


def list_shared_inbox_filter_presets(db_path: str, host: str):
    host = (host or "").strip().lower()
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT preset_name, filters_json, created_by_user_id, created_by_email, is_locked, created_at, updated_at
            FROM inbox_shared_filter_presets
            WHERE host = ?
            ORDER BY preset_name ASC
            """,
            (host,),
        ).fetchall()
    items = []
    for r in rows:
        try:
            filters = json.loads(r["filters_json"] or "{}")
        except Exception:
            filters = {}
        items.append(
            {
                "preset_name": r["preset_name"] or "",
                "filters": filters if isinstance(filters, dict) else {},
                "created_by_user_id": int(r["created_by_user_id"]) if r["created_by_user_id"] else None,
                "created_by_email": r["created_by_email"] or "",
                "is_locked": bool(r["is_locked"]),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
        )
    return items


def get_shared_inbox_filter_preset(db_path: str, host: str, preset_name: str):
    host = (host or "").strip().lower()
    name = (preset_name or "").strip()
    if not name:
        return None
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT preset_name, filters_json, created_by_user_id, created_by_email, is_locked, created_at, updated_at
            FROM inbox_shared_filter_presets
            WHERE host = ? AND preset_name = ?
            LIMIT 1
            """,
            (host, name),
        ).fetchone()
    if not row:
        return None
    try:
        filters = json.loads(row["filters_json"] or "{}")
    except Exception:
        filters = {}
    return {
        "preset_name": row["preset_name"] or "",
        "filters": filters if isinstance(filters, dict) else {},
        "created_by_user_id": int(row["created_by_user_id"]) if row["created_by_user_id"] else None,
        "created_by_email": row["created_by_email"] or "",
        "is_locked": bool(row["is_locked"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def upsert_shared_inbox_filter_preset(
    db_path: str,
    host: str,
    preset_name: str,
    filters: dict,
    created_by_user_id: int | None,
    created_by_email: str,
    is_locked: bool | None = None,
):
    host = (host or "").strip().lower()
    name = (preset_name or "").strip()
    if not name:
        raise ValueError("preset_name is required")
    payload = json.dumps(filters or {}, ensure_ascii=False)
    now = _utc_now()
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id
            FROM inbox_shared_filter_presets
            WHERE host = ? AND preset_name = ?
            """,
            (host, name),
        ).fetchone()
        if row:
            locked_value = int(bool(is_locked))
            if is_locked is None:
                lock_row = conn.execute(
                    "SELECT is_locked FROM inbox_shared_filter_presets WHERE host = ? AND preset_name = ? LIMIT 1",
                    (host, name),
                ).fetchone()
                locked_value = int(lock_row["is_locked"]) if lock_row else 0
            conn.execute(
                """
                UPDATE inbox_shared_filter_presets
                SET filters_json = ?, created_by_user_id = ?, created_by_email = ?, is_locked = ?, updated_at = ?
                WHERE host = ? AND preset_name = ?
                """,
                (payload, created_by_user_id, created_by_email or "", locked_value, now, host, name),
            )
        else:
            conn.execute(
                """
                INSERT INTO inbox_shared_filter_presets(
                    host, preset_name, filters_json, created_by_user_id, created_by_email, is_locked, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (host, name, payload, created_by_user_id, created_by_email or "", int(bool(is_locked)), now, now),
            )
        conn.commit()
    return {
        "preset_name": name,
        "filters": filters or {},
        "created_by_user_id": created_by_user_id,
        "created_by_email": created_by_email or "",
        "is_locked": bool(is_locked),
        "updated_at": now,
    }


def delete_shared_inbox_filter_preset(db_path: str, host: str, preset_name: str):
    host = (host or "").strip().lower()
    name = (preset_name or "").strip()
    if not name:
        raise ValueError("preset_name is required")
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            DELETE FROM inbox_shared_filter_presets
            WHERE host = ? AND preset_name = ?
            """,
            (host, name),
        )
        conn.commit()
    return cur.rowcount > 0


def create_shared_inbox_filter_preset_audit_log(
    db_path: str,
    host: str,
    preset_name: str,
    actor_user_id: int | None,
    actor_email: str,
    action: str,
    before_json: str,
    after_json: str,
):
    now = _utc_now()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO inbox_shared_filter_preset_audit_logs(
                host, preset_name, actor_user_id, actor_email, action, before_json, after_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (host or "").strip().lower(),
                (preset_name or "").strip(),
                actor_user_id,
                actor_email or "",
                action or "update",
                before_json or "{}",
                after_json or "{}",
                now,
            ),
        )
        conn.commit()


def list_shared_inbox_filter_preset_audit_logs(
    db_path: str,
    host: str,
    preset_name: str | None = None,
    limit: int = 300,
):
    host = (host or "").strip().lower()
    clauses = ["host = ?"]
    args = [host]
    if preset_name:
        clauses.append("preset_name = ?")
        args.append((preset_name or "").strip())
    sql = (
        "SELECT * FROM inbox_shared_filter_preset_audit_logs "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY created_at DESC, id DESC LIMIT ?"
    )
    args.append(max(1, min(int(limit), 1000)))
    with _connect(db_path) as conn:
        rows = conn.execute(sql, tuple(args)).fetchall()
    return [
        {
            "id": int(r["id"]),
            "host": r["host"],
            "preset_name": r["preset_name"] or "",
            "actor_user_id": int(r["actor_user_id"]) if r["actor_user_id"] else None,
            "actor_email": r["actor_email"] or "",
            "action": r["action"] or "update",
            "before_json": r["before_json"] or "{}",
            "after_json": r["after_json"] or "{}",
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def get_user_wizard_preference(db_path: str, user_id: int, host: str):
    host = (host or "").strip().lower()
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT mode, risk_priority_json, updated_at
            FROM user_wizard_preferences
            WHERE user_id = ? AND host = ?
            LIMIT 1
            """,
            (int(user_id), host),
        ).fetchone()
    if not row:
        return {"mode": "default", "risk_priority": [], "updated_at": None}
    try:
        risk_priority = json.loads(row["risk_priority_json"] or "[]")
    except Exception:
        risk_priority = []
    return {
        "mode": (row["mode"] or "default"),
        "risk_priority": risk_priority if isinstance(risk_priority, list) else [],
        "updated_at": row["updated_at"],
    }


def upsert_user_wizard_preference(db_path: str, user_id: int, host: str, mode: str, risk_priority: list[str]):
    host = (host or "").strip().lower()
    mode = (mode or "default").strip().lower()
    if mode not in {"default", "personal"}:
        mode = "default"
    payload = json.dumps(risk_priority or [], ensure_ascii=False)
    now = _utc_now()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM user_wizard_preferences WHERE user_id = ? AND host = ?",
            (int(user_id), host),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE user_wizard_preferences
                SET mode = ?, risk_priority_json = ?, updated_at = ?
                WHERE user_id = ? AND host = ?
                """,
                (mode, payload, now, int(user_id), host),
            )
        else:
            conn.execute(
                """
                INSERT INTO user_wizard_preferences(user_id, host, mode, risk_priority_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (int(user_id), host, mode, payload, now, now),
            )
        conn.commit()
    return {"mode": mode, "risk_priority": risk_priority or [], "updated_at": now}
