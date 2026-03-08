import argparse
import json
from datetime import datetime
from pathlib import Path


def _normalize_status(value: str) -> str:
    v = (value or "").strip().upper()
    if v in {"PASS", "OK"}:
        return "PASS"
    if v in {"FAIL", "FAILED", "NG"}:
        return "FAIL"
    return "PENDING"


def _parse_table_rows(lines, start_idx):
    rows = []
    idx = start_idx
    while idx < len(lines):
        line = lines[idx].rstrip("\n")
        if line.startswith("## "):
            break
        if line.strip().startswith("|") and not line.strip().startswith("|---"):
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cols)
        idx += 1
    return rows, idx


def _collect_case_evidence(evidence_dir: Path, case_id: str):
    shot_dir = evidence_dir / "screenshots"
    log_dir = evidence_dir / "logs"
    files = []
    for d in (shot_dir, log_dir):
        if not d.exists():
            continue
        for f in d.glob(f"{case_id}_*"):
            if f.is_file():
                files.append(str(f))
    return sorted(files)


def _count_status(rows, status_idx):
    out = {"PASS": 0, "FAIL": 0, "PENDING": 0}
    for row in rows:
        if len(row) <= status_idx:
            out["PENDING"] += 1
            continue
        out[_normalize_status(row[status_idx])] += 1
    return out


def _build_summary_markdown(result: dict) -> str:
    lines = []
    lines.append("# UAT Result Summary")
    lines.append("")
    lines.append(f"Generated at: {result['generated_at']}")
    lines.append(f"Template: {result['template_path']}")
    lines.append("")
    lines.append("## Gate")
    lines.append("")
    lines.append(f"- Decision: **{result['gate']}**")
    lines.append(f"- Reason: {result['gate_reason']}")
    lines.append("")
    lines.append("## Matrix Status")
    lines.append("")
    m = result["matrix_counts"]
    lines.append(f"- PASS: {m['PASS']}")
    lines.append(f"- FAIL: {m['FAIL']}")
    lines.append(f"- PENDING: {m['PENDING']}")
    lines.append("")
    lines.append("## Critical Cases Status")
    lines.append("")
    c = result["case_counts"]
    lines.append(f"- PASS: {c['PASS']}")
    lines.append(f"- FAIL: {c['FAIL']}")
    lines.append(f"- PENDING: {c['PENDING']}")
    lines.append("")
    lines.append("## Critical Case Details")
    lines.append("")
    lines.append("| ID | Status | Evidence Count | Actual | Evidence Column |")
    lines.append("|---|---|---:|---|---|")
    for row in result["case_rows"]:
        lines.append(
            f"| {row['id']} | {row['status']} | {row['evidence_file_count']} | "
            f"{row['actual']} | {row['evidence_text']} |"
        )
    lines.append("")
    lines.append("## Missing Evidence (PASS but no files)")
    lines.append("")
    if result["missing_evidence_case_ids"]:
        for cid in result["missing_evidence_case_ids"]:
            lines.append(f"- {cid}")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def aggregate(evidence_dir: Path):
    template_path = evidence_dir / "manual_uat_template.md"
    if not template_path.exists():
        raise FileNotFoundError(f"manual template not found: {template_path}")

    lines = template_path.read_text(encoding="utf-8").splitlines()
    matrix_rows = []
    case_rows = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("## 1) Role / Host Matrix"):
            rows, i = _parse_table_rows(lines, i + 1)
            if rows:
                # skip header row
                for r in rows[1:]:
                    matrix_rows.append(
                        {
                            "host": r[0] if len(r) > 0 else "",
                            "user": r[1] if len(r) > 1 else "",
                            "role": r[2] if len(r) > 2 else "",
                            "expected_scope": r[3] if len(r) > 3 else "",
                            "actual": r[4] if len(r) > 4 else "",
                            "status": _normalize_status(r[5] if len(r) > 5 else ""),
                            "evidence_text": r[6] if len(r) > 6 else "",
                        }
                    )
            continue
        if line.startswith("## 2) Critical Cases"):
            rows, i = _parse_table_rows(lines, i + 1)
            if rows:
                for r in rows[1:]:
                    cid = r[0] if len(r) > 0 else ""
                    evidence_files = _collect_case_evidence(evidence_dir, cid)
                    case_rows.append(
                        {
                            "id": cid,
                            "scenario": r[1] if len(r) > 1 else "",
                            "steps": r[2] if len(r) > 2 else "",
                            "expected": r[3] if len(r) > 3 else "",
                            "actual": r[4] if len(r) > 4 else "",
                            "status": _normalize_status(r[5] if len(r) > 5 else ""),
                            "evidence_text": r[6] if len(r) > 6 else "",
                            "evidence_files": evidence_files,
                            "evidence_file_count": len(evidence_files),
                        }
                    )
            continue
        i += 1

    matrix_counts = _count_status([[x["status"]] for x in matrix_rows], 0)
    case_counts = _count_status([[x["status"]] for x in case_rows], 0)
    missing_evidence_case_ids = [
        x["id"] for x in case_rows if x["status"] == "PASS" and x["evidence_file_count"] == 0 and not x["evidence_text"]
    ]

    if case_counts["FAIL"] > 0:
        gate = "NO-GO"
        gate_reason = "One or more critical cases failed."
    elif case_counts["PENDING"] > 0 or matrix_counts["PENDING"] > 0:
        gate = "CONDITIONAL NO-GO"
        gate_reason = "Manual UAT rows are still pending."
    elif missing_evidence_case_ids:
        gate = "CONDITIONAL NO-GO"
        gate_reason = "All cases passed but evidence files are missing for some PASS rows."
    else:
        gate = "GO"
        gate_reason = "All matrix/case rows passed with evidence."

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "template_path": str(template_path),
        "evidence_dir": str(evidence_dir),
        "gate": gate,
        "gate_reason": gate_reason,
        "matrix_counts": matrix_counts,
        "case_counts": case_counts,
        "missing_evidence_case_ids": missing_evidence_case_ids,
        "matrix_rows": matrix_rows,
        "case_rows": case_rows,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Aggregate manual UAT result from template/evidence folder.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Evidence date folder (YYYY-MM-DD)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    evidence_dir = root / "docs" / "ux" / "uat_evidence" / args.date
    result = aggregate(evidence_dir)

    out_json = evidence_dir / "uat_result_summary.json"
    out_md = evidence_dir / "uat_result_summary.md"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_build_summary_markdown(result), encoding="utf-8")

    print(json.dumps({
        "status": "PASS",
        "gate": result["gate"],
        "gate_reason": result["gate_reason"],
        "summary_json": str(out_json),
        "summary_md": str(out_md),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
