import importlib
from pathlib import Path

import pytest


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    # 단일 모듈 앱에서도 테스트마다 DB/설정 경로를 분리해 테넌트/권한 케이스가 서로 오염되지 않게 한다.
    app_module = importlib.import_module("app")

    work_dir = tmp_path / "sandbox"
    upload_dir = work_dir / "uploads"
    inbox_upload_dir = upload_dir / "inbox"
    output_dir = work_dir / "outputs"
    default_template_dir = work_dir / "default_template"
    tenant_template_root = work_dir / "tenant_templates"
    logo_dir = work_dir / "static" / "logos"
    login_bg_dir = work_dir / "static" / "login_bg"
    config_dir = work_dir / "configs"

    for folder in [
        upload_dir,
        inbox_upload_dir,
        output_dir,
        default_template_dir,
        tenant_template_root,
        logo_dir,
        login_bg_dir,
        config_dir,
    ]:
        folder.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(app_module, "BASE_DIR", work_dir)
    monkeypatch.setattr(app_module, "UPLOAD_FOLDER", upload_dir)
    monkeypatch.setattr(app_module, "INBOX_UPLOAD_FOLDER", inbox_upload_dir)
    monkeypatch.setattr(app_module, "OUTPUT_FOLDER", output_dir)
    monkeypatch.setattr(app_module, "DEFAULT_TEMPLATE_DIR", default_template_dir)
    monkeypatch.setattr(app_module, "TENANT_TEMPLATE_ROOT", tenant_template_root)
    monkeypatch.setattr(app_module, "LOGO_FOLDER", logo_dir)
    monkeypatch.setattr(app_module, "LOGIN_BG_FOLDER", login_bg_dir)
    monkeypatch.setattr(app_module, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(app_module, "CONFIG_PATH", work_dir / "config.json")
    monkeypatch.setattr(app_module, "TENANT_REGISTRY_PATH", work_dir / "tenants.json")
    monkeypatch.setattr(app_module, "USER_DB_PATH", work_dir / "users.db")
    monkeypatch.setattr(app_module, "RECEIPT_DB_PATH", work_dir / "receipt_inbox.db")
    monkeypatch.setattr(app_module, "LOCAL_LOGIN_PASSWORD", "test-password")
    monkeypatch.setattr(app_module, "LOCAL_LOGIN_ENABLED", True)
    monkeypatch.setattr(app_module, "ADMIN_PASSWORD", "test-password")
    monkeypatch.setattr(app_module, "EFFECTIVE_ADMIN_EMAILS", set())
    monkeypatch.setattr(app_module, "OPERATOR_EMAILS", {"operator@ezworks.co"})
    monkeypatch.setattr(app_module, "OPERATOR_DOMAINS", {"ezworks.co"})

    app_module.init_user_db(str(app_module.USER_DB_PATH))
    app_module.init_receipt_db(str(app_module.RECEIPT_DB_PATH))
    app_module.app.config.update(TESTING=True, SECRET_KEY="test-secret")

    return app_module


@pytest.fixture()
def client(app_module):
    return app_module.app.test_client()


def login_user(client, host, email, name="", password="test-password"):
    response = client.post(
        "/auth/login/local",
        json={"email": email, "name": name, "password": password},
        headers={"Host": host},
    )
    assert response.status_code == 200, response.get_json()
    return response


def create_user(app_module, email, name="", is_admin=False):
    return app_module.upsert_user_by_email(
        db_path=str(app_module.USER_DB_PATH),
        email=email,
        name=name,
        is_admin=is_admin,
    )


def grant_tenant_admin(app_module, host, email):
    cfg = app_module.load_config(host)
    admins = set(cfg["auth"].get("admin_emails") or [])
    admins.add(email)
    cfg["auth"]["admin_emails"] = sorted(admins)
    app_module.save_config(cfg, host)


def create_receipt_row(app_module, host, uploader_user_id, uploader_email, filename, amount, merchant):
    host_key = app_module._host_to_config_key(host)
    host_dir = Path(app_module.INBOX_UPLOAD_FOLDER) / host_key
    host_dir.mkdir(parents=True, exist_ok=True)
    file_path = host_dir / filename
    file_path.write_bytes(b"test-image")
    row = app_module.create_receipt(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        uploader_user_id=uploader_user_id,
        uploader_email=uploader_email,
        orig_filename=filename,
        stored_filename=filename,
        file_path=str(file_path),
        file_hash=f"hash-{filename}",
    )
    return app_module.update_receipt(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        receipt_id=int(row["id"]),
        fields={
            "date": "2026-03-10",
            "amount": amount,
            "merchant": merchant,
            "currency": "USD",
            "category": "LUNCH",
            "status": "needs_review",
            "report_status": "unassigned",
            "lifecycle_state": "READY",
        },
    )


def create_report_row(app_module, host, creator_user_id, creator_email, title="Report", output_filename="report.xlsx"):
    return app_module.create_report(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        creator_user_id=creator_user_id,
        creator_email=creator_email,
        title=title,
        mode="domestic",
        receipt_count=1,
        total_amount=10.0,
        currency="USD",
        output_session_id="sess-test",
        output_filename=output_filename,
    )
