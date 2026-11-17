"""Independent, read-only validation of the final Choice download/preparation.

Does not import either production script. Re-reads all formal XLSX rows, joins
the separate output streams, and recomputes matches from the Qingke source CSV.
Only writes independent_validation.json outside the preparation directory.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import itertools
import json
import math
import re
import unicodedata
import warnings
from collections import Counter, defaultdict
from contextlib import ExitStack
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "实证结果/choice_download_20261117"
PREP = BASE / "prepare"
RAW = ROOT / "原始数据/Choice_创投事件_20261117/raw"
REPORT = BASE / "independent_validation.json"
checks, failures = Counter(), []


def check(label, condition, detail=""):
    checks[label] += 1
    if not condition:
        failures.append(dict(check=label, detail=str(detail)))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(v):
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def normal(s):
    return "".join(unicodedata.normalize("NFKC", s).split())


def qdate(s):
    if re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", s):
        y, m, d = map(int, s.split("/"))
        return date(y, m, d).isoformat(), "day", y
    if re.fullmatch(r"\d{4}", s):
        return s, "year", int(s)
    for pattern in ("%y-%b", "%b-%y", "%Y-%m", "%Y/%m"):
        try:
            d = datetime.strptime(s, pattern)
            return d.strftime("%Y-%m"), "month", d.year
        except ValueError:
            pass
    raise ValueError("Unrecognized Qingke date: " + s)


GROUPS = {
    "种子轮": "seed", "天使轮": "angel", "Pre-A轮": "pre_a",
    "A轮": "a", "A+轮": "a", "B轮": "b", "B+轮": "b", "Pre-B轮": "b",
    "C轮": "c_or_later", "C+轮": "c_or_later", "D轮": "c_or_later",
    "E轮": "c_or_later", "F轮": "c_or_later", "Pre-IPO": "pre_ipo",
    "IPO": "listing", "新三板": "listing", "IPO后": "listed_financing",
    "新三板定增": "listed_financing", "主板定向增发": "listed_financing",
    "被收购": "acquisition_merger_privatization", "私有化": "acquisition_merger_privatization",
    "战略合并": "acquisition_merger_privatization", "股权转让": "equity_transfer",
    "股权投资": "unspecified_equity", "战略投资": "strategic_investment",
    "后期阶段": "late_stage_label", "债权融资": "debt", "众筹": "crowdfunding",
    "ICO": "ico_label", "扶持基金": "support_fund_label",
}
VENTURE = {"seed", "angel", "pre_a", "a", "b", "c_or_later"}
CURRENCIES = dict(zip(
    ["人民币", "美元", "港元", "日元", "英镑", "欧元", "澳元", "新加坡元", "加元"],
    ["CNY", "USD", "HKD", "JPY", "GBP", "EUR", "AUD", "SGD", "CAD"]))


def split_investors(s):
    # Independently identify top-level separators; preserve raw tokens and order.
    boundary, depth = [-1], 0
    for i, c in enumerate(s):
        if c in "（([【":
            depth += 1
        if c in "）)]】":
            depth = max(0, depth - 1)
        if c in ",，、;；\n" and not depth:
            boundary.append(i)
    boundary.append(len(s))
    return [s[a + 1:b].strip() for a, b in zip(boundary, boundary[1:])
            if s[a + 1:b].strip() not in {"", "--", "-", "未披露", "未透露", "不详", "暂无", "未知", "N/A", "NA"}]


def main():
    summary_path = PREP / "prepare_summary.json"
    summary = json.loads(summary_path.read_text())
    audit = json.loads((BASE / "download_audit.json").read_text())
    ui = json.loads((BASE / "ui_expected_counts.json").read_text())
    audit_files = {r["file"]: r for r in audit["files"]}
    paths = sorted(RAW.glob("choice_events_*.xlsx"))
    expected_names = {p.name for p in paths}
    check("formal_file_universe", expected_names == set(ui) == set(audit_files) == {Path(r["file"]).name for r in summary["inputs"]})
    check("final_audit", audit.get("final_acceptance_passed") is True and not audit.get("incremental") and not audit.get("final_acceptance_issues"))
    check("final_preparation", summary["download_snapshot"] == "final_download_files" and summary["download_completeness"]["passed"])
    input_hashes = {p.name: sha(p) for p in paths}
    for entry in summary["inputs"]:
        name = Path(entry["file"]).name
        check("prepare_input_manifest", entry["sha256"] == input_hashes[name] and entry["rows"] == ui[name]["expected_count"] and entry["bytes"] == (ROOT / entry["file"]).stat().st_size, name)
    check("prepare_script_hash", sha(ROOT / "scripts/prepare_choice_events_20261117.py") == summary["script_sha256"])
    check("template_hash", sha(ROOT / summary["template_input"]["path"]) == summary["template_input"]["sha256"])
    check("audit_snapshot_hash", sha(BASE / "download_audit.json") == summary["download_completeness"]["audit_sha256"])
    check("ui_snapshot_hash", sha(BASE / "ui_expected_counts.json") == summary["download_completeness"]["ui_manifest_sha256"])
    output_hashes = {k: sha(PREP / k) for k in summary["outputs_sha256"]}
    for name, h in output_hashes.items():
        check("output_hash", h == summary["outputs_sha256"][name], name)
    day_coverage = Counter()
    for filename, query in ui.items():
        check("query_all_filters", query["region_filter"] == query["other_filters"] == "全选", filename)
        first, last = date.fromisoformat(query["date_from"]), date.fromisoformat(query["date_to"])
        for offset in range((last - first).days + 1):
            day_coverage[first + timedelta(days=offset)] += 1
        r = audit_files[filename]
        check("audit_batch_pass", r["status"] == "row_count_and_dates_match" and r["count_matches"] and r["stable_during_read"], filename)
        check("audit_batch_count", r["actual_event_rows"] == r["expected_ui_count"] == query["expected_count"], filename)
        check("audit_input_hash", r["sha256"] == input_hashes[filename], filename)
    first, last = date(2012, 1, 1), date(2024, 12, 31)
    target_days = {first + timedelta(days=x) for x in range((last - first).days + 1)}
    check("complete_query_day_coverage", set(day_coverage) == target_days and set(day_coverage.values()) == {1})
    ignored = {Path(r["file"]).name for r in summary["ignored_non_event_workbooks"]}
    actual_ignored = {p.name for p in RAW.glob("*.xlsx")} - expected_names
    check("probe_isolated", ignored == actual_ignored and all(x.startswith("choice_probe_") for x in ignored))

    qpath = ROOT / summary["qingke_input"]["path"]
    qhash = sha(qpath)
    check("qingke_hash", qhash == summary["qingke_input"]["sha256"])
    qcompanies, qfunds, qindex, qexcluded = defaultdict(list), set(), [], []
    with qpath.open(encoding="utf-8-sig", newline="") as h:
        for number, r in enumerate(csv.DictReader(h), 2):
            if r["融资主体"] == "基金全称" and r["投资时间"] == "投资类型" and r["基金全称"] == "上级机构全称":
                qexcluded.append(dict(source_row=number, raw=r, reason="embedded_misaligned_header"))
                continue
            d, precision, year = qdate(r["投资时间"])
            entry = dict(source_row_id=f"qingke:{qhash[:24]}:csv:{number}", source_row=str(number),
                         firm_name_raw=r["融资主体"], firm_name_normalized=normal(r["融资主体"]),
                         event_date=d, date_precision=precision, year=str(year), fund_name_raw=r["基金全称"],
                         fund_level_raw=r["基金级别"], fund_registration_raw=r["注册地区_基金目录"], round_raw=r["轮次"])
            qindex.append(entry)
            qcompanies[entry["firm_name_normalized"]].append(entry)
            qfunds.add(normal(r["基金全称"]))
    with (PREP / "qingke_source_row_index.csv").open(encoding="utf-8-sig", newline="") as h:
        check("qingke_index_recomputed", list(csv.DictReader(h)) == qindex)

    direct = {"序号": "source_sequence_raw", "公司名称": "firm_legal_name", "公司项目简介": "firm_description_raw",
              "获投轮次": "round_raw", "获投金额(元)": "amount_raw", "币种": "currency_raw", "主题": "theme_raw",
              "地区": "firm_region_raw", "投资方": "investor_list_raw", "相关新闻标题": "news_title_raw",
              "相关新闻链接": "source_url", "创新属性标签": "innovation_tags_raw", "行业一级": "industry_level1_raw",
              "行业二级": "industry_level2_raw", "行业三级": "industry_level3_raw", "行业四级": "industry_level4_raw"}
    year_rows, groups, amounts, fingerprints, investor_raw_values = Counter(), Counter(), Counter(), Counter(), Counter()
    company_counts, company_first, venture_first = Counter(), {}, {}
    seen_ids, source_notes = set(), []
    counts = Counter()
    warnings.filterwarnings("ignore", message="Workbook contains no default style", category=UserWarning)
    with ExitStack() as stack:
        def rows(filename):
            h = stack.enter_context(gzip.open(PREP / filename, "rt", encoding="utf-8-sig", newline=""))
            return iter(csv.DictReader(h))
        event_stream, flags = rows("choice_events_normalized.csv.gz"), rows("choice_round_flags.csv.gz")
        candidate_stream = rows("government_event_candidates.csv.gz")
        token_groups = iter(itertools.groupby(rows("choice_investor_tokens.csv.gz"), lambda r: r["event_id"]))
        current_token_group = next(token_groups, None)
        for path in paths:
            workbook = openpyxl.load_workbook(path, read_only=True, data_only=False)
            file_count = 0
            for sheet in workbook:
                row_iterator = sheet.iter_rows(values_only=True)
                headers = next(row_iterator)
                for number, cells in enumerate(row_iterator, 2):
                    raw = dict(zip(headers, cells))
                    if not any(text(x).strip() for x in cells):
                        counts["blank_rows"] += 1
                        continue
                    if any(text(x).startswith("数据来源") for x in cells):
                        counts["footer_rows"] += 1
                        source_notes.append((str(path.relative_to(ROOT)), sheet.title, str(number)))
                        continue
                    if raw.get("获投时间") == "获投时间":
                        counts["repeated_headers"] += 1
                        continue
                    file_count += 1
                    counts["source_rows"] += 1
                    r, f = next(event_stream), next(flags)
                    event_id = f"choice:{path.stem}:{input_hashes[path.name][:24]}:{sheet.title}:{number}"
                    check("source_row_identity", r["event_id"] == event_id and r["source_file_sha256"] == input_hashes[path.name] and r["source_file"] == str(path.relative_to(ROOT)), event_id)
                    check("source_id_unique", event_id not in seen_ids, event_id)
                    seen_ids.add(event_id)
                    check("raw_columns_preserved", all(r[target] == text(raw[source]) for source, target in direct.items()), event_id)
                    check("raw_no_formulas", not any(isinstance(v, str) and v.startswith("=") for v in cells), event_id)
                    date_raw = raw["获投时间"]
                    if isinstance(date_raw, datetime):
                        d = date_raw.date()
                    elif isinstance(date_raw, date):
                        d = date_raw
                    else:
                        d = date.fromisoformat(date_raw)
                    check("date_preservation", r["event_date"] == d.isoformat() and r["event_date_raw"] == text(date_raw) and r["event_year"] == str(d.year) and r["date_precision"] == "day", event_id)
                    check("source_date_in_query", ui[path.name]["date_from"] <= d.isoformat() <= ui[path.name]["date_to"], event_id)
                    name = normal(text(raw["公司名称"]))
                    check("fullname_normalization_only", r["firm_name_normalized"] == name and r["name_normalization"] == "NFKC_and_whitespace_only", event_id)
                    check("unresolved_identifiers_and_ownership", all(r[k] == "" for k in ["firm_id", "firm_uscc", "vendor_event_id", "firm_city_code"]) and r["government_status"] == "unknown" and r["event_id_kind"] == "source_file_sheet_row", event_id)
                    a = raw["获投金额(元)"]
                    numeric = type(a) in (int, float) and math.isfinite(a)
                    disclosure = "reported_numeric" if numeric else "missing" if a is None or text(a).strip() == "" else "reported_text"
                    check("amount_and_currency_unimputed", r["amount_value"] == (text(a) if numeric else "") and r["amount_disclosure_status"] == disclosure and r["currency"] == CURRENCIES.get(text(raw["币种"]), text(raw["币种"])) and r["amount_conversion"] == "none", event_id)
                    amounts[disclosure] += 1
                    counts["numeric_currency_missing"] += int(numeric and not r["currency"])
                    counts["raw_numeric_zero"] += int(numeric and a == 0)
                    fingerprint = hashlib.sha256(json.dumps([text(raw[h]) for h in headers if h != "序号"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
                    check("content_fingerprint", r["record_fingerprint_sha256"] == fingerprint, event_id)
                    if summary["exact_content_duplicate_excess_rows"] == 0:
                        check("zero_duplicate_marker", r["identical_content_source_rows"] == "1", event_id)
                    fingerprints[fingerprint] += 1
                    group = GROUPS.get(text(raw["获投轮次"]))
                    check("observed_round_mapped", group is not None, raw["获投轮次"])
                    expected_flags = {"is_seed_label": group == "seed", "is_angel_label": group == "angel", "is_pre_a_label": group == "pre_a", "is_a_label": group == "a",
                                      "is_seed_angel_pre_a_label": group in {"seed", "angel", "pre_a"}, "is_explicit_venture_round_label": group in VENTURE,
                                      "is_listing_or_listed_financing_label": group in {"listing", "listed_financing"},
                                      "is_mna_or_transfer_label": group in {"acquisition_merger_privatization", "equity_transfer"},
                                      "is_unspecified_equity_or_strategic_label": group in {"unspecified_equity", "strategic_investment"}}
                    check("independent_round_flags", f["event_id"] == event_id and f["round_raw"] == r["round_raw"] and f["round_group"] == group and all(f[k] == str(int(v)) for k, v in expected_flags.items()), event_id)
                    groups[group] += 1
                    year_rows[d.year] += 1
                    company_counts[name] += 1
                    company_first[name] = min(company_first.get(name, d.year), d.year)
                    if group in VENTURE:
                        venture_first[name] = min(venture_first.get(name, d.year), d.year)
                    tokens = split_investors(r["investor_list_raw"])
                    investor_raw_values[r["investor_list_raw"]] += 1
                    known = [t for t in tokens if normal(t) in qfunds]
                    if tokens:
                        check("token_event_link", current_token_group is not None and current_token_group[0] == event_id, event_id)
                        token_records = list(current_token_group[1])
                        check("token_raw_order", [x["investor_token_raw"] for x in token_records] == tokens, event_id)
                        for order, token in enumerate(token_records, 1):
                            check("token_identity_unresolved", token["government_status"] == "unknown" and not token["investor_id"] and not token["fund_id"] and not token["investor_legal_name"] and not token["fund_legal_name"], event_id)
                            check("token_exact_fund_candidate", token["token_is_qingke_known_fund_fullname"] == str(int(normal(token["investor_token_raw"]) in qfunds)) and token["investor_token_order"] == str(order), event_id)
                        counts["investor_token_rows"] += len(tokens)
                        counts["known_fund_tokens"] += len(known)
                        current_token_group = next(token_groups, None)
                    q = qcompanies.get(name, [])
                    if q or known:
                        candidate = next(candidate_stream)
                        same_year = [x["source_row_id"] for x in q if int(x["year"]) == d.year]
                        same_day = [x["source_row_id"] for x in q if x["date_precision"] == "day" and x["event_date"] == d.isoformat()]
                        check("candidate_event_identity", candidate["event_id"] == event_id and candidate["government_status"] == "unknown" and candidate["company_fullname_overlap"] == str(int(bool(q))), event_id)
                        check("candidate_strict_fullname_date", json.loads(candidate["qingke_same_year_source_row_ids"]) == same_year and json.loads(candidate["qingke_same_day_source_row_ids"]) == same_day and int(candidate["qingke_company_rows"]) == len(q) and int(candidate["qingke_same_year_rows"]) == len(same_year) and int(candidate["qingke_same_day_rows"]) == len(same_day), event_id)
                        check("candidate_literal_and_fund_tokens", candidate["literal_fullname_overlap"] == str(int(any(x["firm_name_raw"] == r["firm_legal_name"] for x in q))) and json.loads(candidate["known_qingke_fund_fullname_tokens"]) == known, event_id)
                        counts["same_year_candidates"] += bool(same_year)
                        counts["same_day_candidates"] += bool(same_day)
                        counts["company_overlap_source_rows"] += bool(q)
            workbook.close()
            check("raw_file_count", file_count == ui[path.name]["expected_count"], path.name)
            check("input_unchanged_during_validation", sha(path) == input_hashes[path.name], path.name)
            print(json.dumps({"file": path.name, "rows_verified": file_count}, ensure_ascii=False), flush=True)
        check("no_extra_output_rows", next(event_stream, None) is None and next(flags, None) is None and next(candidate_stream, None) is None and current_token_group is None)

    matched_names = set(company_counts) & set(qcompanies)
    earlier, earlier_v = 0, 0
    with (PREP / "company_fullname_overlap.csv").open(encoding="utf-8-sig", newline="") as h:
        overlaps = list(csv.DictReader(h))
    check("overlap_company_set", {r["firm_name_normalized"] for r in overlaps} == matched_names and len(overlaps) == len(matched_names))
    for r in overlaps:
        name = r["firm_name_normalized"]
        qfirst = min(int(x["year"]) for x in qcompanies[name])
        any_before = company_first[name] < qfirst
        venture_before = name in venture_first and venture_first[name] < qfirst
        check("earlier_history_recalculated", int(r["choice_first_observed_year"]) == company_first[name] and int(r["qingke_first_observed_year"]) == qfirst and r["choice_has_earlier_history"] == str(int(any_before)) and r["choice_first_explicit_venture_round_year"] == (str(venture_first[name]) if name in venture_first else "") and r["choice_has_earlier_explicit_venture_round_history"] == str(int(venture_before)), name)
        earlier += any_before
        earlier_v += venture_before
    recalc = dict(source_rows=counts["source_rows"], files_read=len(paths), unique_company_fullnames=len(company_counts),
                  choice_companies_overlapping_qingke=len(matched_names), qingke_unique_companies=len(qcompanies),
                  company_overlap_source_rows=counts["company_overlap_source_rows"], same_year_event_candidate_rows=counts["same_year_candidates"],
                  same_day_event_candidate_rows=counts["same_day_candidates"], exact_known_fund_token_rows=counts["known_fund_tokens"],
                  investor_token_rows=counts["investor_token_rows"], earlier_history_overlap_companies=earlier,
                  earlier_explicit_venture_round_overlap_companies=earlier_v,
                  exact_content_duplicate_excess_rows=sum(v - 1 for v in fingerprints.values()),
                  excluded_metadata_rows=counts["footer_rows"] + counts["repeated_headers"], excluded_blank_rows=counts["blank_rows"])
    for key, value in recalc.items():
        check("summary_recalculated", summary[key] == value, key)
    check("round_summary_recalculated", summary["round_group_counts"] == dict(groups))
    check("amount_summary_recalculated", summary["amount_disclosure_counts"] == dict(amounts))
    missing_labels = {k: investor_raw_values[k] for k in ["", "未披露", "未透露", "暂无"]}
    audit_investor_missing = sum(r["investor_missing"] for r in audit["files"])
    audit_missing_expected = missing_labels[""] + missing_labels["未披露"] + missing_labels["暂无"]
    prepare_missing_expected = audit_missing_expected + missing_labels["未透露"]
    check("investor_missing_audit_definition", audit_investor_missing == audit_missing_expected)
    check("investor_missing_prepare_definition", summary["field_gaps"]["investor_list_missing_rows"] == prepare_missing_expected)
    with (PREP / "source_notes.csv").open(encoding="utf-8-sig", newline="") as h:
        notes = list(csv.DictReader(h))
    check("footer_traceability", [(r["source_file"], r["source_sheet"], r["source_excel_row"]) for r in notes] == source_notes)
    with (PREP / "overlap_by_year.csv").open(encoding="utf-8-sig", newline="") as h:
        yearly = list(csv.DictReader(h))
    check("annual_counts_recalculated", {int(r["year"]): int(r["choice_source_rows"]) for r in yearly} == dict(year_rows))
    for name, h in output_hashes.items():
        check("outputs_unchanged_during_validation", sha(PREP / name) == h, name)
    check("production_script_unchanged_during_validation", sha(ROOT / "scripts/prepare_choice_events_20261117.py") == summary["script_sha256"])
    report = dict(status="PASS" if not failures else "FAIL", validated_at_utc=datetime.now(timezone.utc).isoformat(),
                  validation_script=str(Path(__file__).relative_to(ROOT)), validation_script_sha256=sha(Path(__file__)),
                  preparation_summary_sha256=sha(summary_path), production_script_sha256=summary["script_sha256"],
                  audit_sha256=sha(BASE / "download_audit.json"), ui_manifest_sha256=sha(BASE / "ui_expected_counts.json"),
                  method="Independent all-row XLSX reread plus streamed output joins; no production-script imports. Full-string NFKC/whitespace matching and manual observed-round mapping recomputed from sources.",
                  total_checks=sum(checks.values()), checks_by_type=dict(checks), failures=failures,
                  recomputed=recalc, covered_days=len(day_coverage), target_interval=[first.isoformat(), last.isoformat()],
                  formal_input_sha256=input_hashes, checked_output_sha256=output_hashes, ignored_workbooks=sorted(ignored),
                  annual_rows=dict(year_rows), round_groups=dict(groups), amount_disclosure=dict(amounts),
                  qingke_excluded_metadata=qexcluded,
                  investor_missing_labels=missing_labels,
                  investor_missing_reconciliation=dict(audit=audit_investor_missing, prepared=prepare_missing_expected,
                      difference=prepare_missing_expected-audit_investor_missing,
                      explanation="The preparation definition additionally recognizes the 28 raw 未透露 labels as unavailable. All original labels are retained."),
                  raw_numeric_zero_rows=counts["raw_numeric_zero"], numeric_amount_currency_missing_rows=counts["numeric_currency_missing"],
                  scope="Validates registered-query export completeness and normalization, not undisclosed-market coverage or legal-entity identity. Same-name/date matches remain candidates and all ownership statuses remain unknown.")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "total_checks": report["total_checks"], "failures": len(failures), "report": str(REPORT)}, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
