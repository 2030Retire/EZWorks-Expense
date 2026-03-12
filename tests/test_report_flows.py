from conftest import create_receipt_row, create_report_row, create_user, login_user


def test_report_permissions_split_own_and_all(app_module, client):
    host = "alpha.local"
    user_a = create_user(app_module, "alice@alpha.com", "Alice")
    user_b = create_user(app_module, "bob@alpha.com", "Bob")
    app_module.set_user_host_permissions(
        str(app_module.USER_DB_PATH),
        int(user_a["id"]),
        host,
        ["report.view_own"],
    )
    app_module.set_user_host_permissions(
        str(app_module.USER_DB_PATH),
        int(user_b["id"]),
        host,
        ["report.view_all"],
    )
    report_a = app_module.create_report(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        creator_user_id=user_a["id"],
        creator_email=user_a["email"],
        title="Alice Report",
        mode="domestic",
        receipt_count=1,
        total_amount=10.0,
        currency="USD",
        output_session_id="sess-a",
        output_filename="alice.xlsx",
    )
    report_b = app_module.create_report(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        creator_user_id=user_b["id"],
        creator_email=user_b["email"],
        title="Bob Report",
        mode="domestic",
        receipt_count=1,
        total_amount=20.0,
        currency="USD",
        output_session_id="sess-b",
        output_filename="bob.xlsx",
    )

    login_user(client, host, user_a["email"], user_a["name"])
    own_list = client.get("/api/inbox/reports", headers={"Host": host})
    forbidden_detail = client.get(f"/api/inbox/reports/{report_b['id']}", headers={"Host": host})

    assert own_list.status_code == 200
    assert [row["id"] for row in own_list.get_json()["reports"]] == [report_a["id"]]
    assert forbidden_detail.status_code == 403

    client.post("/auth/logout", headers={"Host": host})
    login_user(client, host, user_b["email"], user_b["name"])
    all_list = client.get("/api/inbox/reports", headers={"Host": host})

    assert all_list.status_code == 200
    assert {row["id"] for row in all_list.get_json()["reports"]} == {report_a["id"], report_b["id"]}


def test_report_generate_assigns_receipts_and_creates_output_record(app_module, client, monkeypatch):
    host = "alpha.local"
    user = create_user(app_module, "alice@alpha.com", "Alice")
    app_module.set_user_host_permissions(
        str(app_module.USER_DB_PATH),
        int(user["id"]),
        host,
        ["report.submit", "receipt.view_own"],
    )
    receipt = create_receipt_row(app_module, host, user["id"], user["email"], "alice.jpg", 1200, "Alice Cafe")

    template_path = app_module.DEFAULT_TEMPLATE_DIR / "template_domestic.xlsx"
    template_path.write_bytes(b"template")

    # 리포트 생성 테스트는 Excel 포맷 자체보다 권한/상태 전이에 집중한다.
    def fake_fill_expense_report(template_path, receipts, output_path, **kwargs):
        with open(output_path, "wb") as handle:
            handle.write(b"generated")

    monkeypatch.setattr(app_module, "fill_expense_report", fake_fill_expense_report)

    login_user(client, host, user["email"], user["name"])
    response = client.post(
        "/api/inbox/reports/generate",
        json={
            "receipt_ids": [receipt["id"]],
            "mode": "domestic",
            "title": "March Expense",
            "employee_name": "Alice",
            "currency": "USD",
        },
        headers={"Host": host},
    )
    payload = response.get_json()
    updated_receipt = app_module.get_receipt(str(app_module.RECEIPT_DB_PATH), host, int(receipt["id"]))
    report_row = app_module.get_report(str(app_module.RECEIPT_DB_PATH), host, int(payload["report"]["id"]))

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert report_row is not None
    assert updated_receipt["report_status"] == "assigned"
    assert updated_receipt["status"] == "processed"
    assert updated_receipt["lifecycle_state"] == "ASSIGNED_TO_REPORT"
    assert updated_receipt["report_id"] == report_row["id"]


def test_ocr_marks_low_confidence_and_duplicate_can_be_ignored(app_module, client, monkeypatch):
    host = "alpha.local"
    user = create_user(app_module, "alice@alpha.com", "Alice")
    app_module.set_user_host_permissions(
        str(app_module.USER_DB_PATH),
        int(user["id"]),
        host,
        ["receipt.view_own", "duplicate.resolve"],
    )
    original = create_receipt_row(app_module, host, user["id"], user["email"], "base.jpg", 1200, "Alpha Cafe")
    candidate = create_receipt_row(app_module, host, user["id"], user["email"], "candidate.jpg", 100, "Temp Merchant")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def fake_ocr(_path, _api_key):
        return {
            "date": "2026-03-10",
            "merchant": "Alpha Cafe",
            "amount": 1200,
            "currency": "USD",
            "category": "LUNCH",
            "memo": "ocr result",
            "confidence": "low",
            "error": "low confidence",
        }

    monkeypatch.setattr(app_module, "process_receipt_image", fake_ocr)

    login_user(client, host, user["email"], user["name"])
    ocr_response = client.post(f"/api/inbox/ocr/{candidate['id']}", headers={"Host": host})
    duplicate_row = app_module.get_receipt(str(app_module.RECEIPT_DB_PATH), host, int(candidate["id"]))
    ignore_response = client.post(
        f"/api/inbox/receipts/{candidate['id']}/ignore-duplicate",
        headers={"Host": host},
    )
    ignored_row = app_module.get_receipt(str(app_module.RECEIPT_DB_PATH), host, int(candidate["id"]))

    assert ocr_response.status_code == 200
    assert duplicate_row["status"] == "duplicate"
    assert duplicate_row["duplicate_of"] == original["id"]
    assert duplicate_row["lifecycle_state"] == "NEEDS_REVIEW"
    assert ignore_response.status_code == 200
    assert ignored_row["status"] == "processed"
    assert ignored_row["duplicate_of"] is None
    assert ignored_row["lifecycle_state"] == "LOW_CONFIDENCE"


def test_report_line_item_exports_include_receipt_data(app_module, client):
    host = "alpha.local"
    user = create_user(app_module, "alice@alpha.com", "Alice")
    app_module.set_user_host_permissions(
        str(app_module.USER_DB_PATH),
        int(user["id"]),
        host,
        ["report.view_own"],
    )
    report = create_report_row(app_module, host, user["id"], user["email"], title="Alice Report", output_filename="alice.xlsx")
    receipt = create_receipt_row(app_module, host, user["id"], user["email"], "line.jpg", 1300, "Line Cafe")
    app_module.update_receipt(
        db_path=str(app_module.RECEIPT_DB_PATH),
        host=host,
        receipt_id=int(receipt["id"]),
        fields={"report_id": report["id"], "report_status": "assigned", "status": "processed", "lifecycle_state": "ASSIGNED_TO_REPORT"},
    )

    login_user(client, host, user["email"], user["name"])
    csv_response = client.get(f"/api/inbox/reports/{report['id']}/line-items.csv", headers={"Host": host})
    xlsx_response = client.get(f"/api/inbox/reports/{report['id']}/line-items.xlsx", headers={"Host": host})

    csv_text = csv_response.get_data(as_text=True)
    assert csv_response.status_code == 200
    assert "Line Cafe" in csv_text
    assert "receipt_id,file,date,merchant,amount" in csv_text
    assert xlsx_response.status_code == 200
    assert xlsx_response.headers["Content-Type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
