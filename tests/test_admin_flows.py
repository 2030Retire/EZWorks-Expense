from io import BytesIO

from conftest import create_receipt_row, create_user, grant_tenant_admin, login_user


def test_shared_filter_preset_lock_blocks_non_admin_updates(app_module, client):
    host = "alpha.local"
    owner = create_user(app_module, "owner@alpha.com", "Owner")
    admin = create_user(app_module, "admin@alpha.com", "Admin")
    member = create_user(app_module, "member@alpha.com", "Member")
    grant_tenant_admin(app_module, host, admin["email"])

    login_user(client, host, admin["email"], admin["name"])
    create_locked = client.post(
        "/api/inbox/filter-presets",
        json={
            "preset_name": "Team View",
            "scope": "shared",
            "filters": {"status": "needs_review"},
            "is_locked": True,
        },
        headers={"Host": host},
    )
    client.post("/auth/logout", headers={"Host": host})

    login_user(client, host, owner["email"], owner["name"])
    owner_update = client.post(
        "/api/inbox/filter-presets",
        json={
            "preset_name": "Team View",
            "scope": "shared",
            "filters": {"status": "processed"},
        },
        headers={"Host": host},
    )
    client.post("/auth/logout", headers={"Host": host})

    login_user(client, host, member["email"], member["name"])
    member_delete = client.delete(
        "/api/inbox/filter-presets/Team View?scope=shared",
        headers={"Host": host},
    )
    client.post("/auth/logout", headers={"Host": host})

    login_user(client, host, admin["email"], admin["name"])
    admin_unlock = client.patch(
        "/api/inbox/filter-presets/Team View/lock",
        json={"is_locked": False},
        headers={"Host": host},
    )

    assert create_locked.status_code == 200
    assert owner_update.status_code == 403
    assert "Locked shared preset" in owner_update.get_json()["error"]
    assert member_delete.status_code == 403
    assert "Locked shared preset" in member_delete.get_json()["error"]
    assert admin_unlock.status_code == 200
    assert admin_unlock.get_json()["preset"]["is_locked"] is False


def test_tenant_admin_cannot_manage_other_host_config_but_operator_can(app_module, client):
    alpha_host = "alpha.local"
    beta_host = "beta.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Tenant Admin")
    operator = create_user(app_module, "operator@ezworks.co", "Operator")
    grant_tenant_admin(app_module, alpha_host, tenant_admin["email"])

    login_user(client, alpha_host, tenant_admin["email"], tenant_admin["name"])
    denied = client.get(f"/admin/config?host={beta_host}", headers={"Host": alpha_host})
    client.post("/auth/logout", headers={"Host": alpha_host})

    login_user(client, alpha_host, operator["email"], operator["name"])
    allowed = client.get(f"/admin/config?host={beta_host}", headers={"Host": alpha_host})

    assert denied.status_code == 403
    assert "Cross-tenant admin management" in denied.get_json()["error"]
    assert allowed.status_code == 200
    assert allowed.get_json()["_config_host"] == beta_host


def test_admin_user_permissions_can_list_and_update_explicit_permissions(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    member = create_user(app_module, "member@alpha.com", "Member")
    grant_tenant_admin(app_module, host, tenant_admin["email"])

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    update_response = client.patch(
        f"/admin/user-permissions/{member['id']}",
        json={"permissions": ["receipt.view_all", "report.generate", "invalid.permission"]},
        headers={"Host": host},
    )
    list_response = client.get("/admin/user-permissions", headers={"Host": host})
    users = {row["email"]: row for row in list_response.get_json()["users"]}

    assert update_response.status_code == 200
    assert set(update_response.get_json()["permissions"]) == {"receipt.view_all", "report.generate"}
    assert list_response.status_code == 200
    assert users["member@alpha.com"]["explicit_permissions"] == ["receipt.view_all", "report.generate"]
    assert "receipt.view_all" in users["member@alpha.com"]["effective_permissions"]
    assert users["admin@alpha.com"]["is_tenant_admin"] is True


def test_admin_template_info_reports_base_and_document_template_scope(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    grant_tenant_admin(app_module, host, tenant_admin["email"])

    cfg = app_module.load_config(host)
    cfg["document_types"] = [{"id": "travel", "label": "Travel", "enabled": True}]
    app_module.save_config(cfg, host)

    shared_base = app_module.DEFAULT_TEMPLATE_DIR / "template_domestic.xlsx"
    shared_base.write_bytes(b"shared-base")
    tenant_doc = app_module._tenant_template_dir(host) / "template_domestic__travel.xlsx"
    tenant_doc.parent.mkdir(parents=True, exist_ok=True)
    tenant_doc.write_bytes(b"tenant-doc")

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    response = client.get("/admin/template-info", headers={"Host": host})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["base"]["domestic"]["exists"] is True
    assert payload["base"]["domestic"]["scope"] == "shared_default"
    assert payload["document_templates"]["travel"]["domestic"]["exists"] is True
    assert payload["document_templates"]["travel"]["domestic"]["scope"] == "tenant"


def test_admin_audit_log_endpoints_return_json_and_csv(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    member = create_user(app_module, "member@alpha.com", "Member")
    grant_tenant_admin(app_module, host, tenant_admin["email"])
    receipt = create_receipt_row(app_module, host, member["id"], member["email"], "audit.jpg", 900, "Audit Cafe")
    app_module.create_receipt_audit_log(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        receipt_id=int(receipt["id"]),
        actor_user_id=tenant_admin["id"],
        actor_email=tenant_admin["email"],
        action="update",
        changed_fields=["merchant"],
        before_json='{"merchant":"Old Cafe"}',
        after_json='{"merchant":"Audit Cafe"}',
    )

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    logs_response = client.get("/admin/inbox/audit-logs", headers={"Host": host})
    csv_response = client.get("/admin/inbox/audit-logs.csv", headers={"Host": host})

    assert logs_response.status_code == 200
    assert logs_response.get_json()["count"] == 1
    assert logs_response.get_json()["logs"][0]["actor_email"] == "admin@alpha.com"
    assert csv_response.status_code == 200
    assert "merchant: Old Cafe -> Audit Cafe" in csv_response.get_data(as_text=True)


def test_admin_inbox_receipts_and_reports_filter_by_user(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    member_a = create_user(app_module, "a@alpha.com", "Member A")
    member_b = create_user(app_module, "b@alpha.com", "Member B")
    grant_tenant_admin(app_module, host, tenant_admin["email"])

    create_receipt_row(app_module, host, member_a["id"], member_a["email"], "a.jpg", 1000, "Alpha")
    create_receipt_row(app_module, host, member_b["id"], member_b["email"], "b.jpg", 2000, "Beta")
    app_module.create_report(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        creator_user_id=member_a["id"],
        creator_email=member_a["email"],
        title="A Report",
        mode="domestic",
        receipt_count=1,
        total_amount=10.0,
        currency="USD",
        output_session_id="sess-a",
        output_filename="a.xlsx",
    )
    app_module.create_report(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        creator_user_id=member_b["id"],
        creator_email=member_b["email"],
        title="B Report",
        mode="domestic",
        receipt_count=1,
        total_amount=20.0,
        currency="USD",
        output_session_id="sess-b",
        output_filename="b.xlsx",
    )

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    receipts_response = client.get(f"/admin/inbox/receipts?user_email={member_a['email']}", headers={"Host": host})
    reports_response = client.get(f"/admin/inbox/reports?user_email={member_b['email']}", headers={"Host": host})

    assert receipts_response.status_code == 200
    assert receipts_response.get_json()["count"] == 1
    assert receipts_response.get_json()["receipts"][0]["uploader_email"] == member_a["email"]
    assert reports_response.status_code == 200
    assert reports_response.get_json()["count"] == 1
    assert reports_response.get_json()["reports"][0]["creator_email"] == member_b["email"]


def test_admin_shared_preset_audit_log_endpoints_return_json_and_csv(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    grant_tenant_admin(app_module, host, tenant_admin["email"])

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    client.post(
        "/api/inbox/filter-presets",
        json={
            "preset_name": "Finance View",
            "scope": "shared",
            "filters": {"status": "needs_review"},
            "is_locked": True,
        },
        headers={"Host": host},
    )
    logs_response = client.get("/admin/inbox/shared-preset-audit-logs?preset_name=Finance View", headers={"Host": host})
    csv_response = client.get("/admin/inbox/shared-preset-audit-logs.csv?preset_name=Finance View", headers={"Host": host})

    assert logs_response.status_code == 200
    assert logs_response.get_json()["count"] >= 1
    assert logs_response.get_json()["logs"][0]["preset_name"] == "Finance View"
    assert csv_response.status_code == 200
    assert "Finance View" in csv_response.get_data(as_text=True)


def test_admin_generate_templates_creates_requested_files(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    grant_tenant_admin(app_module, host, tenant_admin["email"])

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    response = client.post(
        "/admin/generate-templates",
        json={"modes": ["domestic", "international"]},
        headers={"Host": host},
    )

    domestic = app_module._tenant_template_dir(host) / "template_domestic.xlsx"
    international = app_module._tenant_template_dir(host) / "template_international.xlsx"

    assert response.status_code == 200
    assert set(response.get_json()["created"]) == {"template_domestic.xlsx", "template_international.xlsx"}
    assert domestic.exists()
    assert international.exists()


def test_admin_upload_template_stores_document_override_in_tenant_scope(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    grant_tenant_admin(app_module, host, tenant_admin["email"])

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    response = client.post(
        "/admin/upload-template",
        data={
            "mode": "domestic",
            "document_type": "travel",
            "template": (BytesIO(b"fake-xlsx"), "travel.xlsx"),
        },
        content_type="multipart/form-data",
        headers={"Host": host},
    )

    saved_path = app_module._tenant_template_dir(host) / "template_domestic__travel.xlsx"

    assert response.status_code == 200
    assert response.get_json()["filename"] == "template_domestic__travel.xlsx"
    assert saved_path.exists()


def test_admin_users_create_list_and_update_user_flags(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    grant_tenant_admin(app_module, host, tenant_admin["email"])

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    create_response = client.post(
        "/admin/users",
        json={"email": "newuser@alpha.com", "name": "New User", "is_admin": True},
        headers={"Host": host},
    )
    created_user_id = int(create_response.get_json()["user"]["id"])
    update_response = client.patch(
        f"/admin/users/{created_user_id}",
        json={"is_admin": False, "is_active": False},
        headers={"Host": host},
    )
    list_response = client.get("/admin/users", headers={"Host": host})
    users = {row["email"]: row for row in list_response.get_json()["users"]}

    assert create_response.status_code == 200
    assert create_response.get_json()["user"]["is_admin"] is True
    assert update_response.status_code == 200
    assert update_response.get_json()["user"]["is_admin"] is False
    assert update_response.get_json()["user"]["is_active"] is False
    assert list_response.status_code == 200
    assert users["newuser@alpha.com"]["is_active"] is False


def test_admin_kpi_by_user_aggregates_receipts_and_reports(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    member = create_user(app_module, "member@alpha.com", "Member")
    grant_tenant_admin(app_module, host, tenant_admin["email"])
    receipt_a = create_receipt_row(app_module, host, member["id"], member["email"], "one.jpg", 1000, "One Cafe")
    receipt_b = create_receipt_row(app_module, host, member["id"], member["email"], "two.jpg", 2000, "Two Cafe")
    app_module.update_receipt(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        receipt_id=int(receipt_b["id"]),
        fields={"status": "duplicate", "lifecycle_state": "NEEDS_REVIEW"},
    )
    report = app_module.create_report(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        creator_user_id=member["id"],
        creator_email=member["email"],
        title="Member Report",
        mode="domestic",
        receipt_count=1,
        total_amount=10.0,
        currency="USD",
        output_session_id="sess-kpi",
        output_filename="member.xlsx",
    )
    app_module.update_receipt(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        receipt_id=int(receipt_a["id"]),
        fields={"report_id": report["id"], "report_status": "assigned", "status": "processed", "lifecycle_state": "ASSIGNED_TO_REPORT"},
    )

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    response = client.get("/admin/inbox/kpi-by-user", headers={"Host": host})
    rows = {row["email"]: row for row in response.get_json()["users"]}

    assert response.status_code == 200
    assert rows["member@alpha.com"]["receipts"] == 2
    assert rows["member@alpha.com"]["duplicate"] == 1
    assert rows["member@alpha.com"]["assigned"] == 1
    assert rows["member@alpha.com"]["reports"] == 1


def test_admin_login_slides_upload_list_and_delete(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    grant_tenant_admin(app_module, host, tenant_admin["email"])

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    upload_response = client.post(
        "/admin/login-slides",
        data={
            "caption": "Welcome",
            "image": (BytesIO(b"fake-image"), "slide.png"),
        },
        content_type="multipart/form-data",
        headers={"Host": host},
    )
    filename = upload_response.get_json()["slide"]["filename"]
    list_response = client.get("/admin/login-slides", headers={"Host": host})
    delete_response = client.delete(f"/admin/login-slides/{filename}", headers={"Host": host})
    after_delete = client.get("/admin/login-slides", headers={"Host": host})

    assert upload_response.status_code == 200
    assert any(slide["filename"] == filename for slide in list_response.get_json()["slides"])
    assert delete_response.status_code == 200
    assert all(slide["filename"] != filename for slide in after_delete.get_json()["slides"])


def test_admin_upload_logo_updates_company_logo_filename(app_module, client):
    host = "alpha.local"
    tenant_admin = create_user(app_module, "admin@alpha.com", "Admin")
    grant_tenant_admin(app_module, host, tenant_admin["email"])

    login_user(client, host, tenant_admin["email"], tenant_admin["name"])
    response = client.post(
        "/admin/upload-logo",
        data={"logo": (BytesIO(b"fake-logo"), "logo.png")},
        content_type="multipart/form-data",
        headers={"Host": host},
    )

    cfg = app_module.load_config(host)
    expected_name = f"company_logo_{app_module._host_to_config_key(host)}.png"

    assert response.status_code == 200
    assert response.get_json()["filename"] == expected_name
    assert cfg["company"]["logo_filename"] == expected_name
    assert (app_module.LOGO_FOLDER / expected_name).exists()
