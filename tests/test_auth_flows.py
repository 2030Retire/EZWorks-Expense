from conftest import create_receipt_row, create_user, login_user


def test_api_requires_login(client):
    response = client.get("/api/inbox/permissions", headers={"Host": "alpha.local"})

    assert response.status_code == 401
    assert response.get_json()["error"] == "Login required."


def test_local_login_respects_host_allowed_domains(app_module, client):
    host = "alpha.local"
    cfg = app_module.load_config(host)
    cfg["auth"]["allowed_email_domains"] = ["alpha.com"]
    cfg["auth"]["local_login_password"] = "test-password"
    app_module.save_config(cfg, host)

    blocked = client.post(
        "/auth/login/local",
        json={"email": "user@other.com", "password": "test-password"},
        headers={"Host": host},
    )
    allowed = client.post(
        "/auth/login/local",
        json={"email": "user@alpha.com", "password": "test-password"},
        headers={"Host": host},
    )

    assert blocked.status_code == 403
    assert "not allowed" in blocked.get_json()["error"]
    assert allowed.status_code == 200
    assert allowed.get_json()["status"] == "ok"


def test_receipt_list_returns_only_own_rows_without_view_all(app_module, client):
    host = "alpha.local"
    user_a = create_user(app_module, "alice@alpha.com", "Alice")
    user_b = create_user(app_module, "bob@alpha.com", "Bob")
    app_module.set_user_host_permissions(
        str(app_module.USER_DB_PATH),
        int(user_a["id"]),
        host,
        ["receipt.view_own"],
    )
    create_receipt_row(app_module, host, user_a["id"], user_a["email"], "alice.jpg", 1000, "Alice Cafe")
    create_receipt_row(app_module, host, user_b["id"], user_b["email"], "bob.jpg", 2000, "Bob Cafe")

    login_user(client, host, user_a["email"], user_a["name"])
    response = client.get("/api/inbox/receipts", headers={"Host": host})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["count"] == 1
    assert payload["receipts"][0]["uploader_email"] == "alice@alpha.com"


def test_receipt_routes_are_isolated_by_host(app_module, client):
    alpha_host = "alpha.local"
    beta_host = "beta.local"
    user = create_user(app_module, "alice@alpha.com", "Alice")
    app_module.set_user_host_permissions(
        str(app_module.USER_DB_PATH),
        int(user["id"]),
        alpha_host,
        ["receipt.view_all"],
    )
    app_module.set_user_host_permissions(
        str(app_module.USER_DB_PATH),
        int(user["id"]),
        beta_host,
        ["receipt.view_all"],
    )
    alpha_row = create_receipt_row(app_module, alpha_host, user["id"], user["email"], "alpha.jpg", 1000, "Alpha Cafe")
    beta_row = create_receipt_row(app_module, beta_host, user["id"], user["email"], "beta.jpg", 2000, "Beta Cafe")

    login_user(client, alpha_host, user["email"], user["name"])

    alpha_list = client.get("/api/inbox/receipts", headers={"Host": alpha_host})
    beta_from_alpha = client.get(f"/api/inbox/receipts/{beta_row['id']}", headers={"Host": alpha_host})

    assert alpha_list.status_code == 200
    assert [row["id"] for row in alpha_list.get_json()["receipts"]] == [alpha_row["id"]]
    assert beta_from_alpha.status_code == 404
