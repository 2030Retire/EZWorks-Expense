import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _expect(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    templates_dir = ROOT_DIR / "templates"
    nav_path = templates_dir / "_module_nav.html"
    wizard_progress_path = templates_dir / "_wizard_progress.html"
    app_path = ROOT_DIR / "app.py"

    nav_text = nav_path.read_text(encoding="utf-8")
    wizard_text = wizard_progress_path.read_text(encoding="utf-8")
    app_text = app_path.read_text(encoding="utf-8")

    # Top navigation contract
    for label in ["Dashboard", "Inbox", "Reports", "Admin"]:
        _expect(label in nav_text, f"top nav missing label: {label}")

    # Wizard steps must not be top-nav items
    for forbidden in ["1. Settings", "2. Upload", "3. OCR", "4. Review", "5. Generate"]:
        _expect(forbidden not in nav_text, f"wizard step leaked into top nav: {forbidden}")

    # Wizard progress contract
    for step in [
        "/reports/wizard/settings",
        "/reports/wizard/upload",
        "/reports/wizard/ocr",
        "/reports/wizard/review",
        "/reports/wizard/generate",
    ]:
        _expect(step in wizard_text, f"wizard progress missing step link: {step}")

    wizard_templates = [
        templates_dir / "report_wizard_settings.html",
        templates_dir / "report_wizard_upload.html",
        templates_dir / "report_wizard_ocr.html",
        templates_dir / "report_wizard_review.html",
        templates_dir / "report_wizard_generate.html",
    ]

    for tpl in wizard_templates:
        text = tpl.read_text(encoding="utf-8")
        _expect("_module_nav.html" in text, f"module nav include missing: {tpl.name}")
        _expect("_wizard_progress.html" in text, f"wizard progress include missing: {tpl.name}")

    # Required routes
    required_routes = [
        '/dashboard',
        '/inbox/review',
        '/reports',
        '/admin',
        '/reports/wizard/settings',
        '/reports/wizard/upload',
        '/reports/wizard/ocr',
        '/reports/wizard/review',
        '/reports/wizard/generate',
    ]
    for route in required_routes:
        pattern = re.escape(f'@app.route("{route}"')
        _expect(re.search(pattern, app_text) is not None, f"route missing in app.py: {route}")

    print(json.dumps({
        "status": "PASS",
        "checks": [
            "top_nav_module_contract",
            "wizard_steps_not_in_top_nav",
            "wizard_progress_step_links",
            "wizard_templates_include_nav_and_progress",
            "required_routes_present",
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
