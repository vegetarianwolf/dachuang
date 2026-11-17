"""Read-only acceptance audit for Choice financing-event XLSX downloads.

Run with the bundled Python. XLSX inputs are opened read-only and never saved.
Example: python3 scripts/audit_choice_download_20261117.py \
    --expect choice_events_2012.xlsx=6654
UI expectations persist in the audit directory. No expectation is inferred from
the downloaded row count. Re-running scans formal choice_events_*.xlsx batches.
Test exports named choice_probe_*.xlsx are retained separately and ignored.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
import re
import sys
import warnings
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "原始数据/Choice_创投事件_20261117/raw"
OUT = ROOT / "实证结果/choice_download_20261117"
REQUIRED = {"获投时间", "公司名称", "获投轮次", "投资方"}
MISSING_MARKERS = {"--", "—", "未披露", "未公开", "不详", "未知", "暂无", "N/A", "NA", "null"}
PROVINCE_LABELS = set("北京 天津 上海 重庆 河北 山西 辽宁 吉林 黑龙江 江苏 浙江 安徽 福建 江西 山东 河南 湖北 湖南 广东 海南 四川 贵州 云南 陕西 甘肃 青海 内蒙古 广西 西藏 宁夏 新疆 香港 澳门 台湾".split())
LATER_OR_TRANSACTION = {"被收购", "股权转让", "IPO", "新三板", "主板定向增发", "新三板定增", "IPO后", "战略合并"}


def value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def blank(value) -> bool:
    return value is None or isinstance(value, str) and not value.strip()


def unavailable(value) -> bool:
    return blank(value) or isinstance(value, str) and value.strip() in MISSING_MARKERS


def iso_date(value) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        text = value.strip()
        for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, pattern).date().isoformat()
            except ValueError:
                pass
    return None


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def query_interval_audit(expectations: dict) -> dict:
    """Check registered query dates, independently of observed event dates."""
    start, end = date(2012, 1, 1), date(2024, 12, 31)
    days = {start + timedelta(days=i): [] for i in range((end - start).days + 1)}
    invalid = []
    outside = []
    for filename, expectation in expectations.items():
        try:
            lower = date.fromisoformat(expectation["date_from"])
            upper = date.fromisoformat(expectation["date_to"])
            if lower > upper:
                raise ValueError("date_from is later than date_to")
        except (KeyError, TypeError, ValueError) as error:
            invalid.append({"file": filename, "error": str(error)})
            continue
        if lower < start or upper > end:
            outside.append({"file": filename, "date_from": lower.isoformat(), "date_to": upper.isoformat()})
        current = max(lower, start)
        while current <= min(upper, end):
            days[current].append(filename)
            current += timedelta(days=1)
    def segments(predicate):
        output = []
        for current, names in days.items():
            if not predicate(names):
                continue
            signature = tuple(sorted(names))
            if output and output[-1]["files"] == list(signature) and date.fromisoformat(output[-1]["date_to"]) + timedelta(days=1) == current:
                output[-1]["date_to"] = current.isoformat()
                output[-1]["days"] += 1
            else:
                output.append({"date_from": current.isoformat(), "date_to": current.isoformat(), "days": 1, "files": list(signature)})
        return output
    gaps = segments(lambda names: not names)
    overlaps = segments(lambda names: len(names) > 1)
    return {"target_date_from": start.isoformat(), "target_date_to": end.isoformat(),
            "target_days": len(days), "covered_days": sum(bool(names) for names in days.values()),
            "gap_intervals": gaps, "overlap_intervals": overlaps,
            "invalid_interval_records": invalid, "outside_target_intervals": outside,
            "complete_without_overlap": not (gaps or overlaps or invalid or outside)}


def audit_file(path: Path, expectation: int | dict | None, shared_rows: dict) -> tuple[dict, list[dict], list[dict]]:
    before = path.stat()
    match = re.search(r"choice_events_(20\d{2})(?:\D|$)", path.name)
    expected_year = int(match.group(1)) if match else None
    expected = expectation.get("expected_count") if isinstance(expectation, dict) else expectation
    date_from = f"{expected_year}-01-01" if expected_year else None
    date_to = f"{expected_year}-12-31" if expected_year else None
    quarter = re.search(r"choice_events_(20\d{2})Q([1-4])", path.name)
    if quarter:
        start_month = 3 * int(quarter.group(2)) - 2
        end_month = start_month + 2
        date_from = f"{expected_year}-{start_month:02d}-01"
        date_to = f"{expected_year}-{end_month:02d}-{calendar.monthrange(expected_year, end_month)[1]}"
    month = re.search(r"choice_events_(20\d{2})M(0[1-9]|1[0-2])(?:_M(0[1-9]|1[0-2]))?", path.name)
    if month:
        start_month = int(month.group(2))
        end_month = int(month.group(3) or month.group(2))
        if end_month < start_month:
            raise ValueError("Within-year month ranges must have end_month >= start_month")
        date_from = f"{expected_year}-{start_month:02d}-01"
        date_to = f"{expected_year}-{end_month:02d}-{calendar.monthrange(expected_year, end_month)[1]}"
    if isinstance(expectation, dict):
        date_from = expectation.get("date_from", date_from)
        date_to = expectation.get("date_to", date_to)
    profiles = []
    flagged = []
    sheets = []
    all_rows = []
    source_notes = []
    warning_messages = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=False)
        for sheet in workbook:
            headers = None
            header_row = None
            records = []
            ignored_blank = 0
            for excel_row, cells in enumerate(sheet.iter_rows(values_only=True), 1):
                texts = [str(v).strip() if v is not None else "" for v in cells]
                if headers is None:
                    if REQUIRED <= set(texts):
                        headers = texts
                        header_row = excel_row
                    elif any(texts):
                        source_notes.append({"sheet": sheet.title, "row": excel_row, "text": " | ".join(t for t in texts if t)})
                    continue
                if not any(texts):
                    ignored_blank += 1
                    continue
                if any(t.startswith("数据来源") for t in texts):
                    source_notes.append({"sheet": sheet.title, "row": excel_row, "text": " | ".join(t for t in texts if t)})
                    continue
                row = {name: value(cells[i]) for i, name in enumerate(headers) if name}
                if REQUIRED <= set(texts):
                    flagged.append({"file": path.name, "sheet": sheet.title, "excel_row": excel_row,
                                    "issue": "repeated_header", "company": "", "field": "", "value": ""})
                    continue
                row["_sheet"] = sheet.title
                row["_excel_row"] = excel_row
                parsed = iso_date(cells[headers.index("获投时间")])
                row["_date"] = parsed
                records.append(row)
                for field in ("公司名称", "投资方"):
                    text = str(row.get(field) or "")
                    if "…" in text or "..." in text or re.search(r"等(?:投资|机构|公司)?[。.]*$", text):
                        flagged.append({"file": path.name, "sheet": sheet.title, "excel_row": excel_row,
                                        "issue": "possible_abbreviation_or_truncation", "company": row.get("公司名称", ""),
                                        "field": field, "value": text})
                if parsed is None or date_from and parsed < date_from or date_to and parsed > date_to:
                    flagged.append({"file": path.name, "sheet": sheet.title, "excel_row": excel_row,
                                    "issue": "invalid_or_outside_query_date_range", "company": row.get("公司名称", ""),
                                    "field": "获投时间", "value": row.get("获投时间", "")})
                signature = tuple((name, row.get(name)) for name in headers if name and name != "序号")
                shared_rows[signature].append({"file": path.name, "sheet": sheet.title, "excel_row": excel_row,
                                               "company": row.get("公司名称"), "date": row.get("获投时间"), "round": row.get("获投轮次")})
            if headers is None:
                sheets.append({"sheet": sheet.title, "status": "no_event_header", "max_row": sheet.max_row, "max_column": sheet.max_column})
                continue
            for field in headers:
                if not field:
                    continue
                vals = [r.get(field) for r in records]
                profiles.append({"file": path.name, "sheet": sheet.title, "column": field,
                                 "rows": len(vals), "blank_count": sum(blank(v) for v in vals),
                                 "missing_marker_count": sum(not blank(v) and unavailable(v) for v in vals),
                                 "numeric_zero_count": sum(isinstance(v, (int, float)) and v == 0 for v in vals),
                                 "unique_nonblank": len({str(v) for v in vals if not blank(v)}),
                                 "value_types": json.dumps(dict(Counter(type(v).__name__ for v in vals)), ensure_ascii=False),
                                 "max_text_length": max((len(v) for v in vals if isinstance(v, str)), default=0)})
            sheets.append({"sheet": sheet.title, "status": "event_table", "header_row": header_row,
                           "columns": headers, "actual_event_rows": len(records), "ignored_blank_rows": ignored_blank,
                           "max_row": sheet.max_row, "max_column": sheet.max_column})
            all_rows.extend(records)
        workbook.close()
        warning_messages = sorted({str(item.message) for item in caught})
    after = path.stat()
    stable = before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns
    dates = [r["_date"] for r in all_rows if r["_date"]]
    amount_col = next((h for s in sheets for h in s.get("columns", []) if "获投金额" in h), None)
    missing_amount = sum(unavailable(r.get(amount_col)) for r in all_rows) if amount_col else len(all_rows)
    serials = [int(r["序号"]) for r in all_rows if isinstance(r.get("序号"), (int, float)) and float(r["序号"]).is_integer()]
    rounds = Counter(str(r.get("获投轮次") or "") for r in all_rows)
    regions = Counter(str(r.get("地区") or "") for r in all_rows)
    companies = {str(r["公司名称"]) for r in all_rows if not unavailable(r.get("公司名称"))}
    within_signatures = Counter(tuple((k, r.get(k)) for k in sorted(r) if not k.startswith("_") and k != "序号") for r in all_rows)
    event_keys = Counter((r.get("公司名称"), r.get("获投时间"), r.get("获投轮次")) for r in all_rows)
    all_columns = {h for s in sheets for h in s.get("columns", [])}
    count_matches = expected is not None and len(all_rows) == expected
    invalid_dates = len(all_rows) - len(dates)
    out_of_year = sum(not d.startswith(str(expected_year)) for d in dates) if expected_year else 0
    out_of_range = sum(bool(date_from and d < date_from or date_to and d > date_to) for d in dates)
    if not stable:
        status = "file_changed_during_read"
    elif not all_rows:
        status = "no_event_rows"
    elif invalid_dates or out_of_range:
        status = "date_check_failed"
    elif expected is not None and not count_matches:
        status = "row_count_mismatch"
    elif expected is None:
        status = "ui_count_not_supplied"
    else:
        status = "row_count_and_dates_match"
    result = {
        "file": path.name, "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "bytes": after.st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "stable_during_read": stable,
        "expected_ui_count": expected, "actual_event_rows": len(all_rows), "count_matches": count_matches if expected is not None else None,
        "status": status, "filename_year": expected_year, "date_min": min(dates) if dates else None, "date_max": max(dates) if dates else None,
        "query_date_from": date_from, "query_date_to": date_to,
        "query_metadata": expectation if isinstance(expectation, dict) else {"expected_count": expected, "date_source": "filename"},
        "invalid_date_rows": invalid_dates, "outside_filename_year_rows": out_of_year, "outside_query_date_range_rows": out_of_range,
        "serial_1_through_n": len(serials) == len(all_rows) and sorted(serials) == list(range(1, len(all_rows) + 1)),
        "unique_company_names": len(companies), "company_missing": sum(unavailable(r.get("公司名称")) for r in all_rows),
        "company_names_with_legal_entity_hint": sum(bool(re.search(r"公司|合伙|集团|事务所", str(r.get("公司名称") or ""))) for r in all_rows),
        "investor_missing": sum(unavailable(r.get("投资方")) for r in all_rows),
        "investor_multiple_list_rows": sum(bool(re.search(r"[，,；;、\n]", str(r.get("投资方") or ""))) for r in all_rows),
        "investor_possible_truncation_rows": sum(f["field"] == "投资方" and f["issue"] == "possible_abbreviation_or_truncation" for f in flagged),
        "max_investor_text_length": max((len(str(r.get("投资方") or "")) for r in all_rows), default=0),
        "amount_column": amount_col, "amount_missing": missing_amount,
        "amount_numeric_zero": sum(isinstance(r.get(amount_col), (int, float)) and r[amount_col] == 0 for r in all_rows) if amount_col else 0,
        "amount_numeric_negative": sum(isinstance(r.get(amount_col), (int, float)) and r[amount_col] < 0 for r in all_rows) if amount_col else 0,
        "amount_available_currency_missing": sum(not unavailable(r.get(amount_col)) and unavailable(r.get("币种")) for r in all_rows) if amount_col else 0,
        "amount_types": dict(Counter(type(r.get(amount_col)).__name__ for r in all_rows)),
        "currency_distribution": dict(Counter(str(r.get("币种") or "缺失") for r in all_rows)),
        "region_missing": sum(unavailable(r.get("地区")) for r in all_rows), "region_distribution": dict(regions),
        "region_province_label_rows": sum(regions[label] for label in PROVINCE_LABELS),
        "hong_kong_macao_taiwan_rows": sum(regions[label] for label in ("香港", "澳门", "台湾")),
        "round_distribution": dict(rounds), "later_or_transaction_round_rows": sum(rounds[label] for label in LATER_OR_TRANSACTION),
        "news_link_missing": sum(unavailable(r.get("相关新闻链接")) for r in all_rows),
        "exact_content_duplicate_excess": sum(v - 1 for v in within_signatures.values()),
        "same_company_date_round_multiple_rows": sum(v > 1 for v in event_keys.values()),
        "supplier_event_id_present": any(re.search(r"事件.*(?:ID|代码|编号)", h, re.I) for h in all_columns),
        "supplier_firm_id_or_uscc_present": any(re.search(r"(?:公司|企业).*(?:ID|代码|编号)|信用代码", h, re.I) for h in all_columns),
        "formula_cells": sum(isinstance(v, str) and v.startswith("=") for r in all_rows for k, v in r.items() if not k.startswith("_")),
        "sheets": sheets, "source_notes": source_notes, "read_warnings": warning_messages,
    }
    return result, profiles, flagged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--expect", action="append", default=[], metavar="FILENAME=COUNT")
    parser.add_argument("--file", action="append", default=[], metavar="FILENAME", help="Read only named batches and retain earlier audit results")
    parser.add_argument("--final-check", action="store_true", help="Require complete 2012-2024 registered query dates and verify all batches and prior hashes")
    args = parser.parse_args()
    if args.final_check and args.file:
        parser.error("--final-check requires a full scan; omit --file")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    expectation_path = args.out_dir / "ui_expected_counts.json"
    expectations = json.loads(expectation_path.read_text(encoding="utf-8")) if expectation_path.exists() else {"choice_events_2012.xlsx": 6654}
    for item in args.expect:
        filename, count = item.rsplit("=", 1)
        if int(count) < 0 or Path(filename).name != filename:
            raise ValueError("--expect requires a plain filename and nonnegative count")
        if isinstance(expectations.get(filename), dict):
            expectations[filename]["expected_count"] = int(count)
        else:
            expectations[filename] = int(count)
    expectation_path.write_text(json.dumps(expectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit_path = args.out_dir / "download_audit.json"
    previous = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else {}
    previous_hashes = {r["file"]: r.get("sha256") for r in previous.get("files", []) if r.get("sha256")}
    results, profiles, flagged = [], [], []
    shared_rows = defaultdict(list)
    available_paths = sorted(args.raw_dir.glob("choice_events_*.xlsx"))
    ignored_xlsx = sorted(p.name for p in args.raw_dir.glob("*.xlsx")
                          if p not in available_paths and not p.name.startswith("~$"))
    selected = set(args.file)
    if any(Path(name).name != name for name in selected):
        raise ValueError("--file requires plain filenames")
    paths = [p for p in available_paths if not selected or p.name in selected]
    missing_selected = selected - {p.name for p in available_paths}
    if missing_selected:
        raise FileNotFoundError(f"Selected batches not found: {sorted(missing_selected)}")
    for path in paths:
        try:
            result, cols, flags = audit_file(path, expectations.get(path.name), shared_rows)
            profiles.extend(cols)
            flagged.extend(flags)
        except Exception as error:
            result = {"file": path.name, "status": "read_error", "error": f"{type(error).__name__}: {error}",
                      "expected_ui_count": expectations.get(path.name), "actual_event_rows": None}
        results.append(result)
        print(json.dumps({key: result.get(key) for key in ("file", "status", "expected_ui_count", "actual_event_rows", "date_min", "date_max", "investor_missing", "amount_missing")}, ensure_ascii=False), flush=True)
    duplicate_rows = []
    for records in shared_rows.values():
        if len(records) > 1:
            group_id = len(duplicate_rows) + 1
            for record in records:
                duplicate_rows.append({"group_id": group_id, **record})
    current_results = list(results)
    hash_checks = [{"file": r["file"], "previous_sha256": previous_hashes.get(r["file"]),
                    "current_sha256": r.get("sha256"),
                    "matches_previous_audit": r.get("sha256") == previous_hashes[r["file"]]}
                   for r in current_results if r["file"] in previous_hashes]
    if selected:
        available_names = {p.name for p in available_paths}
        retained = [r for r in previous.get("files", []) if r["file"] not in selected and r["file"] in available_names]
        results = sorted(retained + results, key=lambda r: r["file"])
        def retained_csv(name):
            path = args.out_dir / name
            if not path.exists():
                return []
            with path.open(encoding="utf-8-sig", newline="") as handle:
                return [r for r in csv.DictReader(handle) if r["file"] not in selected and r["file"] in available_names]
        profiles = retained_csv("column_profile.csv") + profiles
        flagged = retained_csv("flagged_rows.csv") + flagged
        prior_duplicates = retained_csv("exact_duplicate_rows.csv")
        group_sizes = Counter(r["group_id"] for r in prior_duplicates)
        prior_duplicates = [r for r in prior_duplicates if group_sizes[r["group_id"]] >= 2]
        offset = max((int(r["group_id"]) for r in prior_duplicates), default=0)
        for row in duplicate_rows:
            row["group_id"] = int(row["group_id"]) + offset
        duplicate_rows = prior_duplicates + duplicate_rows
    summary_fields = ["file", "status", "expected_ui_count", "actual_event_rows", "query_date_from", "query_date_to", "date_min", "date_max", "unique_company_names",
                      "investor_missing", "investor_possible_truncation_rows", "amount_missing", "amount_numeric_zero", "amount_available_currency_missing",
                      "region_province_label_rows", "hong_kong_macao_taiwan_rows", "exact_content_duplicate_excess", "bytes", "sha256"]
    write_csv(args.out_dir / "batch_summary.csv", [{k: row.get(k) for k in summary_fields} for row in results], summary_fields)
    write_csv(args.out_dir / "column_profile.csv", profiles,
              ["file", "sheet", "column", "rows", "blank_count", "missing_marker_count", "numeric_zero_count", "unique_nonblank", "value_types", "max_text_length"])
    write_csv(args.out_dir / "flagged_rows.csv", flagged, ["file", "sheet", "excel_row", "issue", "company", "field", "value"])
    write_csv(args.out_dir / "exact_duplicate_rows.csv", duplicate_rows, ["group_id", "file", "sheet", "excel_row", "company", "date", "round"])
    audit = {"files": results, "files_scanned_this_run": len(paths), "files_audited": len(results),
             "files_read_this_run": [p.name for p in paths], "incremental": bool(selected),
             "total_event_rows": sum(r.get("actual_event_rows") or 0 for r in results),
             "missing_expected_files": sorted(set(expectations) - {p.name for p in available_paths}),
             "available_not_yet_audited": sorted({p.name for p in available_paths} - {r["file"] for r in results}),
             "ignored_probe_files": [name for name in ignored_xlsx if name.startswith("choice_probe_")],
             "ignored_other_xlsx": [name for name in ignored_xlsx if not name.startswith("choice_probe_")],
             "registered_query_intervals": query_interval_audit(expectations),
             "expectation_manifest_sha256": hashlib.sha256(expectation_path.read_bytes()).hexdigest(),
             "prior_hash_checks_this_run": hash_checks,
             "final_check_requested": args.final_check,
             "rules": {
                 "read_only": "Inputs opened read_only=True, data_only=False; original XLSX files are never saved or changed.",
                 "formal_batches": "Only choice_events_*.xlsx are formal batches. choice_probe_*.xlsx test exports remain in raw and are listed as ignored; they do not enter counts, date coverage or duplicate checks.",
                 "data_rows": "Rows after financing-event headers, excluding empty rows, repeated headers and 数据来源 footer.",
                 "missing_amount": "Blank/explicit missing markers remain missing; numeric zero is recorded separately. No monetary aggregation or currency conversion.",
                 "row_count": "Compared only with supplied UI counts. Matching a UI count establishes export completeness for that query, not market coverage.",
                 "expectation_manifest": "ui_expected_counts.json accepts filename: count, or filename: {expected_count,date_from,date_to,region_filter,notes}. Counts are recorded from the UI, never replaced by file counts.",
                 "names": "Legal-entity words are only name-format hints; investor lists may mix brands, people and legal funds. Flagged 等/ellipsis rows require detail review.",
                 "geography": "Preserve original region labels. Province labels do not establish a prefecture-city match; Hong Kong/Macao/Taiwan are counted separately.",
                 "scope": "All raw rounds retained; IPO/listing, acquisitions and transfers remain separate source categories. No government/private classification inferred from labels alone.",
                 "duplicates": "Exact content excludes export row number. Candidate duplicates are reported, not deleted.",
                 "incremental": "--file reads only selected XLSX batches, retains earlier audits, and compares duplicates within this run. Run once without --file for a final all-file duplicate check.",
                 "query_intervals": "Registered UI query dates are checked against every calendar day from 2012-01-01 through 2024-12-31. Gaps during download are reported; --final-check requires complete, disjoint coverage.",
                 "hashes": "Re-read batches are compared with SHA-256 recorded in the preceding audit. Final check reads all raw batches and requires matching prior hashes, UI counts, explicit intervals and stable inputs.",
             }}
    final_issues = []
    if not audit["registered_query_intervals"]["complete_without_overlap"]:
        final_issues.append("registered_query_dates_not_complete_and_disjoint")
    if audit["missing_expected_files"] or audit["available_not_yet_audited"] or {p.name for p in available_paths} - set(expectations):
        final_issues.append("raw_files_manifest_and_audit_not_one_to_one")
    if any(r.get("status") != "row_count_and_dates_match" or not r.get("stable_during_read") for r in results):
        final_issues.append("not_all_batches_pass_count_dates_and_stability")
    if any(not r["matches_previous_audit"] for r in hash_checks):
        final_issues.append("raw_file_sha256_changed_since_previous_audit")
    if args.final_check and len(hash_checks) != len(results):
        final_issues.append("not_all_batches_have_prior_hash_comparison")
    audit["final_acceptance_issues"] = final_issues
    audit["final_acceptance_passed"] = args.final_check and not final_issues
    (args.out_dir / "download_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = any(r["status"] not in ("row_count_and_dates_match", "ui_count_not_supplied") for r in current_results) or args.final_check and bool(final_issues)
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
