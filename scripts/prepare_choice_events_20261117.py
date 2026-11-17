"""Normalize Choice exports and diagnose overlap with the Qingke fund universe.

All downloaded rows are retained. Identifiers refer to a source file/sheet/row,
not to a verified unique financing event. Research round flags and government
match candidates are separate outputs. No regression or ownership imputation.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import unicodedata
import warnings
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "原始数据/Choice_创投事件_20261117/raw"
OUT = ROOT / "实证结果/choice_download_20261117/prepare"
TEMPLATE = ROOT / "实证结果/fiscal_fund_design_round2_20261117/templates/financing_events.csv"
QINGKE = ROOT / "原始数据打包_20260401/清科政府引导基金投资事件截止到2024年/2015-2024投资事件_附基金级别分类注册地区_扩展匹配.csv"
AUDIT = ROOT / "实证结果/choice_download_20261117/download_audit.json"
UI_MANIFEST = ROOT / "实证结果/choice_download_20261117/ui_expected_counts.json"
SOURCE = "Choice_创投数据_投融资事件"
HEADERS = ["序号", "获投时间", "公司名称", "公司项目简介", "获投轮次", "获投金额(元)", "币种", "主题", "地区", "投资方", "相关新闻标题", "相关新闻链接", "创新属性标签", "行业一级", "行业二级", "行业三级", "行业四级"]
MISSING = {"", "--", "-", "未披露", "未透露", "不详", "暂无", "未知", "N/A", "NA"}
CURRENCY = {"人民币": "CNY", "美元": "USD", "港元": "HKD", "日元": "JPY", "英镑": "GBP", "欧元": "EUR", "澳元": "AUD", "新加坡元": "SGD", "加元": "CAD"}
RULE_VERSION = "choice_round_flags_20261117_v1"


def string(value):
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        if value.is_integer():
            return str(int(value))
    return str(value)


def norm(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", string(value)))


def present(value):
    return string(value).strip() not in MISSING


def digest(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return digest(path.read_bytes())


def parse_date(value):
    text = string(value).strip()
    if not present(text):
        return "", "missing", ""
    if re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:T00:00:00)?", text):
        try:
            dt = datetime.strptime(text[:10].replace("/", "-"), "%Y-%m-%d").date()
            return dt.isoformat(), "day", dt.year
        except ValueError:
            pass
    match = re.fullmatch(r"(\d{4})[-/](\d{1,2})", text)
    if match and 1 <= int(match[2]) <= 12:
        return f"{match[1]}-{int(match[2]):02d}", "month", int(match[1])
    if re.fullmatch(r"\d{4}", text):
        return text, "year", int(text)
    for fmt in ("%y-%b", "%b-%y"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%Y-%m"), "month", dt.year
        except ValueError:
            pass
    return "", "unparsed", ""


def round_flags(value):
    text = norm(value).upper().replace("－", "-").replace("—", "-")
    text = re.sub(r"^PRE(?=[A-Z])", "PRE-", text)
    if not present(text):
        group = "missing"
    elif text in {"种子轮", "种子", "SEED"}:
        group = "seed"
    elif text in {"天使轮", "天使", "天使+轮", "ANGEL"}:
        group = "angel"
    elif re.fullmatch(r"PRE-A(?:轮)?", text):
        group = "pre_a"
    elif re.fullmatch(r"A\+*(?:轮)?", text):
        group = "a"
    elif re.fullmatch(r"(?:PRE-)?B\+*(?:轮)?", text):
        group = "b"
    elif re.fullmatch(r"(?:PRE-)?[C-Z]\+*(?:轮)?", text):
        group = "c_or_later"
    elif text == "PRE-IPO":
        group = "pre_ipo"
    elif text in {"IPO", "新三板"}:
        group = "listing"
    elif text in {"IPO后", "新三板定增", "主板定向增发", "定向增发", "上市后融资"}:
        group = "listed_financing"
    elif text in {"被收购", "并购", "战略合并", "私有化"}:
        group = "acquisition_merger_privatization"
    elif text == "股权转让":
        group = "equity_transfer"
    elif text == "股权投资":
        group = "unspecified_equity"
    elif text == "战略投资":
        group = "strategic_investment"
    elif text == "后期阶段":
        group = "late_stage_label"
    elif text in {"债权融资", "债务融资"}:
        group = "debt"
    elif text == "众筹":
        group = "crowdfunding"
    elif text == "ICO":
        group = "ico_label"
    elif text == "扶持基金":
        group = "support_fund_label"
    else:
        group = "unmapped"
    return dict(round_rule_version=RULE_VERSION, round_normalized=text, round_group=group,
                is_seed_label=int(group == "seed"), is_angel_label=int(group == "angel"),
                is_pre_a_label=int(group == "pre_a"), is_a_label=int(group == "a"),
                is_seed_angel_pre_a_label=int(group in {"seed", "angel", "pre_a"}),
                is_explicit_venture_round_label=int(group in {"seed", "angel", "pre_a", "a", "b", "c_or_later"}),
                is_listing_or_listed_financing_label=int(group in {"listing", "listed_financing"}),
                is_mna_or_transfer_label=int(group in {"acquisition_merger_privatization", "equity_transfer"}),
                is_unspecified_equity_or_strategic_label=int(group in {"unspecified_equity", "strategic_investment"}),
                stage_evidence_kind="financing_round_label_not_firm_maturity")


def investor_tokens(value):
    """Candidate tokens only: separators inside parentheses stay in the name."""
    tokens, buf, depth = [], [], 0
    for char in string(value):
        if char in "（([【":
            depth += 1
        elif char in "）)]】":
            depth = max(depth - 1, 0)
        if char in ",，、;；\n" and depth == 0:
            if present("".join(buf)):
                tokens.append("".join(buf).strip())
            buf = []
        else:
            buf.append(char)
    if present("".join(buf)):
        tokens.append("".join(buf).strip())
    return tokens


def write_csv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(rows[0]) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        # Deterministic compression keeps unchanged source snapshots reproducible.
        with path.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8-sig", newline="") as target:
                    writer = csv.DictWriter(target, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
    else:
        with path.open("w", encoding="utf-8-sig", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


def load_qingke():
    firms, funds, rows, excluded = defaultdict(list), set(), [], []
    qhash = sha(QINGKE)
    with QINGKE.open(encoding="utf-8-sig", newline="") as source:
        for line, r in enumerate(csv.DictReader(source), 2):
            shifted_header = {"融资主体": "基金全称", "投资时间": "投资类型", "基金全称": "上级机构全称", "轮次": "投资金额(USD/M)"}
            if all(r.get(field) == text for field, text in shifted_header.items()):
                excluded.append(dict(source_file=str(QINGKE.relative_to(ROOT)), source_file_sha256=qhash,
                                     source_row=line, exclusion_reason="shifted_repeated_header",
                                     source_row_id=f"qingke:{qhash[:24]}:csv:{line}",
                                     raw_record_json=json.dumps(r, ensure_ascii=False)))
                continue
            name = norm(r["融资主体"])
            event_date, precision, year = parse_date(r["投资时间"])
            row = dict(source_row_id=f"qingke:{qhash[:24]}:csv:{line}", source_row=line,
                       firm_name_raw=r["融资主体"], firm_name_normalized=name,
                       event_date=event_date, date_precision=precision, year=year,
                       fund_name_raw=r["基金全称"], fund_level_raw=r["基金级别"],
                       fund_registration_raw=r["注册地区_基金目录"], round_raw=r["轮次"])
            rows.append(row)
            if present(name):
                firms[name].append(row)
            if present(r["基金全称"]):
                funds.add(norm(r["基金全称"]))
    return firms, funds, rows, qhash, excluded


def check_download_completeness(manifests):
    """Use registered UI query intervals, never observed event dates, for coverage."""
    issues, comparison, intervals = [], [], []
    audit_bytes = AUDIT.read_bytes() if AUDIT.exists() else b""
    ui_bytes = UI_MANIFEST.read_bytes() if UI_MANIFEST.exists() else b""
    audited = json.loads(audit_bytes) if audit_bytes else {}
    registered = json.loads(ui_bytes) if ui_bytes else {}
    audit_files = {r["file"]: r for r in audited.get("files", [])}
    actual_files = {Path(r["file"]).name for r in manifests}
    if not audit_bytes:
        issues.append("Independent download audit is missing")
    if not ui_bytes:
        issues.append("Registered UI date/count/filter manifest is missing")
    if actual_files != set(audit_files):
        issues.append("Prepared files and independent audited files differ")
    if actual_files != set(registered):
        issues.append("Prepared files and registered UI batches differ")
    if audited.get("missing_expected_files") or audited.get("available_not_yet_audited"):
        issues.append("Independent audit reports missing or not-yet-audited files")
    for filename in sorted(actual_files):
        sheets = [r for r in manifests if Path(r["file"]).name == filename]
        record, ui = audit_files.get(filename, {}), registered.get(filename, {})
        same_hash = record.get("sha256") == sheets[0]["sha256"]
        prepared_rows = sum(r["rows"] for r in sheets)
        expected_rows = record.get("actual_event_rows") if same_hash else None
        rows_match = prepared_rows == expected_rows if same_hash else None
        comparison.append(dict(file=sheets[0]["file"], same_input_hash=same_hash,
                               prepared_rows=prepared_rows, audited_rows=expected_rows, rows_match=rows_match))
        if same_hash and not rows_match:
            raise ValueError(f"Prepared/audited row count mismatch in {filename}: {prepared_rows} vs {expected_rows}")
        if not same_hash or rows_match is not True:
            issues.append(filename + ": exact input hash/row comparison is incomplete")
        if record.get("status") != "row_count_and_dates_match" or record.get("count_matches") is not True or record.get("stable_during_read") is not True:
            issues.append(filename + ": independent audit is not PASS")
        if any(record.get(k) != 0 for k in ["invalid_date_rows", "outside_query_date_range_rows"]):
            issues.append(filename + ": date validation is incomplete or failed")
        if ui.get("region_filter") != "全选" or ui.get("other_filters") != "全选":
            issues.append(filename + ": UI all-region/all-other-filter selection is unverified")
        ui_count = ui.get("expected_count")
        if not isinstance(ui_count, int) or ui_count < 0 or ui_count != prepared_rows or record.get("expected_ui_count") != ui_count:
            issues.append(filename + ": UI expected count does not match prepared/audited rows")
        if any(record.get("query_metadata", {}).get(k) != ui.get(k) for k in ["expected_count", "date_from", "date_to", "region_filter", "other_filters"]):
            issues.append(filename + ": audited query metadata does not match the current UI manifest")
        try:
            start, end = date.fromisoformat(ui["date_from"]), date.fromisoformat(ui["date_to"])
            if start > end:
                raise ValueError("reversed query dates")
            intervals.append(dict(file=filename, date_from=start.isoformat(), date_to=end.isoformat()))
        except (KeyError, ValueError, TypeError):
            issues.append(filename + ": valid registered query interval is missing")
    target_start, target_end = date(2012, 1, 1), date(2024, 12, 31)
    cursor = target_start
    gaps, overlaps = [], []
    for item in sorted(intervals, key=lambda r: (r["date_from"], r["date_to"], r["file"])):
        start, end = date.fromisoformat(item["date_from"]), date.fromisoformat(item["date_to"])
        if start > cursor:
            gaps.append(dict(date_from=cursor.isoformat(), date_to=(start-timedelta(days=1)).isoformat()))
        elif start < cursor:
            overlaps.append(dict(file=item["file"], date_from=start.isoformat(), date_to=min(end, cursor-timedelta(days=1)).isoformat()))
        if start < target_start or end > target_end:
            issues.append(item["file"] + ": registered query extends outside the target interval")
        cursor = max(cursor, end + timedelta(days=1))
    if cursor <= target_end:
        gaps.append(dict(date_from=cursor.isoformat(), date_to=target_end.isoformat()))
    if gaps:
        issues.append("Registered UI query intervals have target-period gaps")
    if overlaps:
        issues.append("Registered UI query intervals overlap")
    if len(intervals) != len(actual_files):
        issues.append("At least one input lacks a registered UI query interval")
    return dict(passed=not issues, target_date_from=target_start.isoformat(), target_date_to=target_end.isoformat(),
                boundary_basis="UI manifest query dates; observed record min/max dates do not establish coverage",
                audit_sha256=digest(audit_bytes) if audit_bytes else "", ui_manifest_sha256=digest(ui_bytes) if ui_bytes else "",
                audit_path=str(AUDIT.relative_to(ROOT)), ui_manifest_path=str(UI_MANIFEST.relative_to(ROOT)),
                prepared_files=len(actual_files), audited_files=len(audit_files), registered_files=len(registered),
                gaps=gaps, overlaps=overlaps, issues=issues, registered_intervals=intervals, file_comparison=comparison)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final-snapshot", action="store_true", help="Use only after the 2012–2024 downloads have finished; independent query-count audit remains authoritative.")
    args = parser.parse_args()
    warnings.filterwarnings("ignore", message="Workbook contains no default style", category=UserWarning)
    OUT.mkdir(parents=True, exist_ok=True)
    template_fields = next(csv.reader(TEMPLATE.open(encoding="utf-8-sig")))
    qfirms, qfunds, qrows, qhash, qexcluded = load_qingke()
    snapshot_time = datetime.now(timezone.utc).isoformat()
    files = sorted(RAW.glob("choice_events_*.xlsx"))
    ignored_workbooks = [dict(file=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                              reason="diagnostic_probe_not_formal_event_batch" if path.name.startswith("choice_probe_") else "filename_outside_choice_events_pattern")
                         for path in sorted(RAW.glob("*.xlsx")) if not path.name.startswith("choice_events_")]
    normalized, flags, token_rows, candidates = [], [], [], []
    manifests, skipped, source_notes, raw_types = [], [], [], defaultdict(Counter)
    byfirm, record_counts = defaultdict(list), Counter()
    for path in files:
        before = path.read_bytes()
        if not before or not zipfile.is_zipfile(io.BytesIO(before)):
            skipped.append(dict(file=str(path.relative_to(ROOT)), reason="empty_or_incomplete_xlsx", bytes=len(before)))
            continue
        file_hash = digest(before)
        workbook = load_workbook(io.BytesIO(before), read_only=True, data_only=True)
        file_records = []
        for sheet in workbook:
            iterator = sheet.iter_rows(values_only=True)
            header = list(next(iterator, []))
            if header != HEADERS:
                raise ValueError(f"Unexpected columns in {path.name}/{sheet.title}: {header!r}")
            n, blank_rows, metadata_rows = 0, 0, 0
            for row_number, values in enumerate(iterator, 2):
                texts = [string(v).strip() for v in values]
                if not any(texts):
                    blank_rows += 1
                    continue
                note_kind = "source_footer" if any(t.startswith("数据来源") for t in texts) else (
                    "repeated_header" if {"获投时间", "公司名称", "获投轮次", "投资方"} <= set(texts) else "")
                if note_kind:
                    metadata_rows += 1
                    source_notes.append(dict(source_file=str(path.relative_to(ROOT)), source_file_sha256=file_hash,
                                             source_batch=path.stem, source_sheet=sheet.title, source_excel_row=row_number,
                                             note_kind=note_kind, note_text=" | ".join(t for t in texts if t),
                                             raw_cells_json=json.dumps([string(v) for v in values], ensure_ascii=False)))
                    continue
                n += 1
                raw = dict(zip(header, values))
                source_id = f"choice:{path.stem}:{file_hash[:24]}:{sheet.title}:{row_number}"
                firm = norm(raw["公司名称"])
                dt, precision, year = parse_date(raw["获投时间"])
                amount = raw["获投金额(元)"]
                numeric = isinstance(amount, (int, float)) and not isinstance(amount, bool) and math.isfinite(amount)
                r = dict.fromkeys(template_fields, "")
                r.update(source=SOURCE, event_id=source_id, firm_legal_name=string(raw["公司名称"]),
                         event_date=dt, date_type="Choice获投时间_具体含义待字段说明核验", round_raw=string(raw["获投轮次"]),
                         amount_raw=string(amount), amount_value=string(amount) if numeric else "",
                         currency=CURRENCY.get(string(raw["币种"]), string(raw["币种"])),
                         amount_disclosure_status="reported_numeric" if numeric else ("missing" if not present(amount) else "reported_text"),
                         source_url=string(raw["相关新闻链接"]), extracted_at="2026-11-17")
                fingerprint = digest(json.dumps([string(raw[h]) for h in HEADERS if h != "序号"], ensure_ascii=False, separators=(",", ":")).encode())
                r.update(event_id_kind="source_file_sheet_row", vendor_event_id="", source_file=str(path.relative_to(ROOT)),
                         source_file_sha256=file_hash, source_batch=path.stem, source_sheet=sheet.title,
                         source_excel_row=row_number, source_sequence_raw=string(raw["序号"]),
                         firm_name_normalized=firm, name_normalization="NFKC_and_whitespace_only",
                         event_year=year, date_precision=precision, event_date_raw=string(raw["获投时间"]),
                         amount_cell_type=type(amount).__name__, amount_unit_raw="元", amount_conversion="none",
                         currency_raw=string(raw["币种"]), investor_list_raw=string(raw["投资方"]),
                         firm_region_raw=string(raw["地区"]), geography_precision="vendor_region_unverified",
                         firm_description_raw=string(raw["公司项目简介"]), theme_raw=string(raw["主题"]),
                         news_title_raw=string(raw["相关新闻标题"]), innovation_tags_raw=string(raw["创新属性标签"]),
                         industry_level1_raw=string(raw["行业一级"]), industry_level2_raw=string(raw["行业二级"]),
                         industry_level3_raw=string(raw["行业三级"]), industry_level4_raw=string(raw["行业四级"]),
                         attribute_valid_at="", government_status="unknown", record_fingerprint_sha256=fingerprint)
                record_counts[fingerprint] += 1
                for field in HEADERS:
                    raw_types[field][type(raw[field]).__name__] += 1
                tokens = investor_tokens(raw["投资方"])
                known_tokens = [t for t in tokens if norm(t) in qfunds]
                r["investor_token_count"] = len(tokens)
                file_records.append(r)
                byfirm[firm].append(r)
                f = dict(event_id=source_id, round_raw=string(raw["获投轮次"]), **round_flags(raw["获投轮次"]))
                flags.append(f)
                for order, token in enumerate(tokens, 1):
                    token_rows.append(dict(source=SOURCE, event_id=source_id, investor_token_order=order,
                                           investor_token_raw=token, investor_token_normalized=norm(token),
                                           investor_id="", investor_legal_name="", investor_role="", fund_id="", fund_legal_name="",
                                           government_status="unknown", source_investor_type="",
                                           token_is_qingke_known_fund_fullname=int(norm(token) in qfunds),
                                           token_rule="split_top_level_comma_semicolon_dunhao_no_entity_resolution"))
                matches = qfirms.get(firm, [])
                if matches or known_tokens:
                    same_year = [x for x in matches if year != "" and x["year"] == year]
                    same_day = [x for x in matches if precision == "day" and x["date_precision"] == "day" and x["event_date"] == dt]
                    candidates.append(dict(event_id=source_id, firm_name_raw=r["firm_legal_name"], firm_name_normalized=firm,
                                           event_date=dt, event_year=year, round_raw=r["round_raw"], investor_list_raw=r["investor_list_raw"],
                                           company_fullname_overlap=int(bool(matches)),
                                           literal_fullname_overlap=int(any(x["firm_name_raw"] == r["firm_legal_name"] for x in matches)),
                                           qingke_company_rows=len(matches), qingke_same_year_rows=len(same_year),
                                           qingke_same_day_rows=len(same_day),
                                           known_qingke_fund_fullname_tokens=json.dumps(known_tokens, ensure_ascii=False),
                                           qingke_same_year_source_row_ids=json.dumps([x["source_row_id"] for x in same_year], ensure_ascii=False),
                                           qingke_same_day_source_row_ids=json.dumps([x["source_row_id"] for x in same_day], ensure_ascii=False),
                                           government_status="unknown", candidate_basis="company_history_or_exact_fund_token_requires_event_verification"))
            manifests.append(dict(file=str(path.relative_to(ROOT)), sha256=file_hash, sheet=sheet.title, rows=n,
                                  ignored_blank_rows=blank_rows, metadata_rows=metadata_rows, bytes=len(before), columns=header))
        workbook.close()
        if sha(path) != file_hash:
            raise RuntimeError(f"Input changed while reading; rerun after download finishes: {path.name}")
        normalized.extend(file_records)
    for r in normalized:
        r["identical_content_source_rows"] = record_counts[r["record_fingerprint_sha256"]]
    assert len(normalized) == len({r["event_id"] for r in normalized})
    assert len(normalized) == sum(x["rows"] for x in manifests) == len(flags)
    assert all(r["government_status"] == "unknown" for r in normalized + token_rows)

    flag_by_id = {r["event_id"]: r for r in flags}
    overlap = []
    for firm in sorted(set(byfirm) & set(qfirms)):
        c, q = byfirm[firm], qfirms[firm]
        cy = [r["event_year"] for r in c if r["event_year"] != ""]
        vy = [r["event_year"] for r in c if r["event_year"] != "" and flag_by_id[r["event_id"]]["is_explicit_venture_round_label"]]
        qy = [r["year"] for r in q if r["year"] != ""]
        overlap.append(dict(firm_name_normalized=firm, choice_source_rows=len(c), qingke_source_rows=len(q),
                            choice_first_observed_year=min(cy) if cy else "", qingke_first_observed_year=min(qy) if qy else "",
                            choice_has_earlier_history=int(bool(cy and qy and min(cy) < min(qy))),
                            choice_first_explicit_venture_round_year=min(vy) if vy else "",
                            choice_has_earlier_explicit_venture_round_history=int(bool(vy and qy and min(vy) < min(qy))),
                            qingke_fund_fullnames=json.dumps(sorted({r["fund_name_raw"] for r in q}), ensure_ascii=False),
                            qingke_fund_levels=json.dumps(sorted({r["fund_level_raw"] for r in q}), ensure_ascii=False),
                            qingke_source_row_ids=json.dumps([r["source_row_id"] for r in q], ensure_ascii=False)))
    years = sorted({r["event_year"] for r in normalized if r["event_year"] != ""})
    if args.final_snapshot and (skipped or years != list(range(2012, 2025))):
        raise ValueError("Final snapshot requires readable files and observed records in every target year 2012–2024.")
    completeness = check_download_completeness(manifests)
    audit_comparison = completeness["file_comparison"]
    (OUT / "download_completeness_check.json").write_text(json.dumps(completeness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.final_snapshot and not completeness["passed"]:
        raise ValueError("Final snapshot failed independent audit/UI query completeness: " + "; ".join(completeness["issues"]))
    year_summary = []
    candidate_by_id = {r["event_id"]: r for r in candidates}
    for year in years:
        rows = [r for r in normalized if r["event_year"] == year]
        names = {r["firm_name_normalized"] for r in rows if present(r["firm_name_normalized"])}
        year_summary.append(dict(year=year, choice_source_rows=len(rows), choice_unique_fullnames=len(names),
                                 qingke_overlap_companies=len(names & set(qfirms)),
                                 company_overlap_rows=sum(r["firm_name_normalized"] in qfirms for r in rows),
                                 same_year_candidate_rows=sum(candidate_by_id.get(r["event_id"], {}).get("qingke_same_year_rows", 0) > 0 for r in rows),
                                 same_day_candidate_rows=sum(candidate_by_id.get(r["event_id"], {}).get("qingke_same_day_rows", 0) > 0 for r in rows),
                                 explicit_venture_round_rows=sum(flag_by_id[r["event_id"]]["is_explicit_venture_round_label"] for r in rows),
                                 listing_or_listed_financing_rows=sum(flag_by_id[r["event_id"]]["is_listing_or_listed_financing_label"] for r in rows),
                                 mna_or_transfer_rows=sum(flag_by_id[r["event_id"]]["is_mna_or_transfer_label"] for r in rows)))
    field_assessment = []
    available = {
        "event_id": "来源行ID；供应商稳定事件ID缺失", "firm_legal_name": "公司名称原文；待企业ID/曾用名核验",
        "event_date": "获投时间；日期的经济含义待字段说明", "date_type": "保留供应商字段名",
        "round_raw": "获投轮次原文", "amount_raw": "原单元格值；数值精确程度待来源说明",
        "amount_value": "仅原数值单元格；未换汇或取区间中点", "currency": "原币种明确映射", "amount_disclosure_status": "按单元格类型记录",
        "source_url": "相关新闻链接原文", "extracted_at": "本次提取日期", "source": "Choice模块名称"}
    for field in template_fields:
        count = sum(present(r[field]) for r in normalized)
        field_assessment.append(dict(template_field=field, populated_rows=count, missing_rows=len(normalized)-count,
                                    populated_share=count/len(normalized) if normalized else 0,
                                    interpretation=available.get(field, "导出表未提供；保留缺失")))
    round_counts = Counter(r["round_raw"] for r in flags)
    rule_rows = [dict(round_raw=text, source_rows=count, **round_flags(text)) for text, count in sorted(round_counts.items())]
    write_csv(OUT / "choice_events_normalized.csv.gz", normalized)
    write_csv(OUT / "choice_round_flags.csv.gz", flags)
    write_csv(OUT / "choice_investor_tokens.csv.gz", token_rows)
    write_csv(OUT / "government_event_candidates.csv.gz", candidates)
    write_csv(OUT / "company_fullname_overlap.csv", overlap)
    write_csv(OUT / "overlap_by_year.csv", year_summary)
    write_csv(OUT / "template_field_assessment.csv", field_assessment)
    write_csv(OUT / "round_classification_rules.csv", rule_rows)
    write_csv(OUT / "qingke_source_row_index.csv", qrows)
    write_csv(OUT / "qingke_excluded_source_rows.csv", qexcluded,
              ["source_file", "source_file_sha256", "source_row", "exclusion_reason", "source_row_id", "raw_record_json"])
    write_csv(OUT / "source_notes.csv", source_notes, ["source_file", "source_file_sha256", "source_batch", "source_sheet", "source_excel_row", "note_kind", "note_text", "raw_cells_json"])
    write_csv(OUT / "independent_audit_comparison.csv", audit_comparison, ["file", "same_input_hash", "prepared_rows", "audited_rows", "rows_match"])
    names = {r["firm_name_normalized"] for r in normalized if present(r["firm_name_normalized"])}
    summary = dict(snapshot_started_at_utc=snapshot_time, extraction_date="2026-11-17", download_snapshot="final_download_files" if args.final_snapshot else "current_files_not_final_coverage",
                   script_sha256=sha(Path(__file__)), template_input=dict(path=str(TEMPLATE.relative_to(ROOT)), sha256=sha(TEMPLATE)),
                   raw_directory=str(RAW.relative_to(ROOT)), files_read=len({x["file"] for x in manifests}), files_skipped=skipped,
                   ignored_non_event_workbooks=ignored_workbooks,
                   excluded_metadata_rows=len(source_notes), excluded_blank_rows=sum(r["ignored_blank_rows"] for r in manifests),
                   independent_audit_comparison=audit_comparison,
                   download_completeness=completeness,
                   source_rows=len(normalized), unique_company_fullnames=len(names), source_years=years,
                   choice_companies_overlapping_qingke=len(names & set(qfirms)), qingke_unique_companies=len(qfirms),
                   choice_company_overlap_rate=len(names & set(qfirms))/len(names) if names else None,
                   qingke_company_overlap_rate=len(names & set(qfirms))/len(qfirms) if qfirms else None,
                   company_overlap_source_rows=sum(r["firm_name_normalized"] in qfirms for r in normalized),
                   same_year_event_candidate_rows=sum(r["qingke_same_year_rows"] > 0 for r in candidates),
                   same_day_event_candidate_rows=sum(r["qingke_same_day_rows"] > 0 for r in candidates),
                   exact_known_fund_token_rows=sum(r["token_is_qingke_known_fund_fullname"] for r in token_rows),
                   investor_token_rows=len(token_rows), verified_private_events=0, government_status_unknown_events=len(normalized),
                   earlier_history_overlap_companies=sum(r["choice_has_earlier_history"] for r in overlap),
                   earlier_explicit_venture_round_overlap_companies=sum(r["choice_has_earlier_explicit_venture_round_history"] for r in overlap),
                   exact_content_duplicate_excess_rows=sum(n-1 for n in record_counts.values() if n > 1),
                   round_group_counts=dict(Counter(r["round_group"] for r in flags)),
                   amount_disclosure_counts=dict(Counter(r["amount_disclosure_status"] for r in normalized)),
                   field_gaps=dict(vendor_event_id_missing_rows=sum(not present(r["vendor_event_id"]) for r in normalized),
                                   firm_identifier_missing_rows=sum(not present(r["firm_id"]) for r in normalized),
                                   investor_list_missing_rows=sum(not present(r["investor_list_raw"]) for r in normalized),
                                   investor_list_missing_components=dict(Counter(r["investor_list_raw"] if r["investor_list_raw"].strip() else "<blank>" for r in normalized if not present(r["investor_list_raw"]))),
                                   investor_list_additional_untold_rows=sum(r["investor_list_raw"].strip() == "未透露" for r in normalized),
                                   currency_missing_rows=sum(not present(r["currency_raw"]) for r in normalized),
                                   numeric_amount_currency_missing_rows=sum(r["amount_disclosure_status"] == "reported_numeric" and not present(r["currency_raw"]) for r in normalized),
                                   news_link_missing_rows=sum(not present(r["source_url"]) for r in normalized),
                                   firm_region_missing_rows=sum(not present(r["firm_region_raw"]) for r in normalized),
                                   source_columns_not_provided=["vendor_event_id", "firm_id", "firm_uscc", "announcement_date", "transaction_status", "industry_code", "industry_code_version", "firm_city_code", "record_created_at", "record_updated_at", "fund_lp_identity", "historical_government_status", "investor_amount"]),
                   raw_cell_type_counts={k: dict(v) for k, v in raw_types.items()},
                   qingke_input=dict(path=str(QINGKE.relative_to(ROOT)), sha256=qhash, rows=len(qrows), raw_rows=len(qrows)+len(qexcluded),
                                    excluded_rows=len(qexcluded), excluded_source_rows=[r["source_row"] for r in qexcluded]), inputs=manifests,
                   validation=dict(source_rows_conserved=True, source_row_ids_unique=True, round_flags_one_per_source_row=True,
                                   government_status_unknown_preserved=True, input_files_unchanged_during_read=True),
                   rules=dict(company_match="NFKC + whitespace removal only, then full-string equality; literal equality flagged separately",
                              input_rows="Only choice_events_*.xlsx formal batches. Diagnostic choice_probe_* files remain raw and are listed as ignored. Rows below the event header exclude blanks, repeated headers and 数据来源 footers; metadata retained separately in source_notes.csv.",
                              government_candidates="Company overlap describes financing history; name+year/date and exact known fund tokens are review candidates. Ownership and government status remain unknown.",
                              qingke_header="Exclude only the explicit shifted-header signature 融资主体=基金全称, 投资时间=投资类型, 基金全称=上级机构全称, 轮次=投资金额(USD/M); preserve source record number and raw values separately.",
                              investor_tokens="Split top-level comma/Chinese comma/dunhao/semicolon/newline; parentheses preserved. No fuzzy names, role inference, legal-entity inference or investor-amount allocation.",
                              monetary_amounts="Keep original cell value and currency; numeric cells copied without conversion. No missing-to-zero or midpoint imputation.",
                              duplicate_policy="All source rows retained; content fingerprint excludes only the batch sequence. Identical-content frequency is diagnostic.",
                              round_flags="Supplier financing labels classified separately; no inference from round to government identity or firm maturity.",
                              region_and_tags="Region, industry and innovation labels retained as exported; historical effective dates are not supplied."))
    artifact_paths = sorted(p for p in OUT.iterdir() if p.suffix in {".csv", ".gz"})
    summary["outputs_sha256"] = {p.name: sha(p) for p in artifact_paths}
    (OUT / "prepare_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    groups = summary["round_group_counts"]
    rows = len(normalized)
    snapshot_sentence = "登记的全选查询区间连续覆盖2012-01-01—2024-12-31；各批次文件哈希、记录数、界面预期数与独立审计一致。" if args.final_snapshot else "下载仍在进行，年度完整性以独立下载审计为准。"
    gaps_sentence = "登记查询区间尚缺：" + "；".join(f"{g['date_from']}—{g['date_to']}" for g in completeness["gaps"]) + "。" if completeness["gaps"] else "登记查询区间已覆盖目标日期范围；各批次计数和审计状态见完整性核验。"
    nonfinal_heading = "**下载进行中。** " + gaps_sentence + "\n\n" if not args.final_snapshot else ""
    report = f"""# Choice 创投事件规范化与清科重合诊断

{nonfinal_heading}本次处理当前已完成的 {summary['files_read']} 个 Excel，保留 {rows:,} 条来源记录和 {len(names):,} 个公司全名，已覆盖下载年份为 {', '.join(map(str, years))}。{snapshot_sentence}

清科匹配底表包含 {len(qrows):,} 条真实来源记录、{len(qfirms):,} 个公司全名；{len(qexcluded)} 条错位重复表头已分流至源行诊断。公司全名经过 Unicode 统一和空白清理后，{summary['choice_companies_overlapping_qingke']:,} 家与清科政府引导基金事件表重合，占本次 Choice 公司数 {summary['choice_company_overlap_rate']:.2%}、清科公司数 {summary['qingke_company_overlap_rate']:.2%}。同公司同年候选 {summary['same_year_event_candidate_rows']:,} 条，同公司同日候选 {summary['same_day_event_candidate_rows']:,} 条；这两个层次用于核验同一融资事件。重合企业中 {summary['earlier_history_overlap_companies']:,} 家在 Choice 中出现早于清科首个观察年份的事件记录，其中 {summary['earlier_explicit_venture_round_overlap_companies']:,} 家有更早的明确种子、天使、Pre-A、A、B 或 C 及以后轮次标签。两种历史口径分别保存，后续首投核验按选定的交易范围展开。

原表同时收录融资轮次、上市、上市后融资、收购与股权转让。独立轮次 flags 保留种子、天使、Pre-A、A、B、C 及以后等分组，并单列其他交易：上市 {groups.get('listing', 0):,} 条，上市后融资 {groups.get('listed_financing', 0):,} 条，收购合并私有化 {groups.get('acquisition_merger_privatization', 0):,} 条，股权转让 {groups.get('equity_transfer', 0):,} 条。后续 VC 研究需要先确定交易范围和各轮次的分母。

每条来源记录以文件哈希、工作表和 Excel 行号连接原表；供应商稳定事件ID、企业ID、信用代码、政府背景和投资方金额尚未出现在导出列。投资方原文完整保留，分词另存候选表，其中 {summary['exact_known_fund_token_rows']:,} 个词元与清科基金全称精确重合。所有记录的政府背景维持 unknown；私人对照需补充事件发生时的基金及 LP 身份证据。

规范化文件保留原始金额、币种、投资方、地区、行业和新闻链接。金额未知留空，数值按来源单元格保存；未换汇。地区列保留原文，城市代码及历史有效期留空。融资时间保留原始精度和字段名，当前标签及相关新闻可能包含事后补录信息，时间有效性随数据字典核验。

金额数值可得 {summary['amount_disclosure_counts'].get('reported_numeric', 0):,} 条、金额缺失 {summary['amount_disclosure_counts'].get('missing', 0):,} 条；投资方名单缺失 {summary['field_gaps']['investor_list_missing_rows']:,} 条，其中下载验收口径下的缺项 {summary['field_gaps']['investor_list_missing_rows']-summary['field_gaps']['investor_list_additional_untold_rows']:,} 条，另有原文“未透露” {summary['field_gaps']['investor_list_additional_untold_rows']:,} 条纳入规范化缺失统计，原文均保留。新闻链接缺失 {summary['field_gaps']['news_link_missing_rows']:,} 条；数值金额对应币种缺失 {summary['field_gaps']['numeric_amount_currency_missing_rows']:,} 条。下一步身份核验优先补企业统一标识及曾用名、投资基金法律实体与历史LP、事件发生时政府出资辖区；发生日和公告日分列、地区及行业的历史有效期随后与字段字典核对。

| 文件 | 用途 |
|---|---|
| choice_events_normalized.csv.gz | 全部来源记录及融资模板映射；压缩 CSV 可直接用 pandas 读取 |
| choice_round_flags.csv.gz / round_classification_rules.csv | 独立研究轮次 flags、完整原标签与规则 |
| choice_investor_tokens.csv.gz | 原投资方的分词候选；原名单仍在事件表 |
| government_event_candidates.csv.gz | 公司全名、同年、同日及基金全称的政府背景核验线索 |
| company_fullname_overlap.csv / overlap_by_year.csv | 公司重合、较早融资历史及逐年诊断 |
| template_field_assessment.csv | 标准融资字段的提供情况和实际含义 |
| qingke_source_row_index.csv | 清科原始行索引和匹配所需字段 |
| qingke_excluded_source_rows.csv | 清科错位重复表头的原逻辑行、源哈希和完整原记录 |
| source_notes.csv / independent_audit_comparison.csv | 原表来源备注与重复表头；按相同文件哈希核对独立审计有效行数 |
| prepare_summary.json | 输入输出哈希、快照范围、缺失和完整规则 |

原始 Excel 保持原样，全部融资来源记录保留。{len(source_notes)} 条页脚或重复表头另存来源备注，空白行跳过。重复内容增加标记，正式事件去重需要同时核验公司、日期、轮次、投资方和来源报道。脚本仅生成数据与诊断。

探查文件单独保留在 raw，其中 {len(ignored_workbooks)} 个非正式批次未进入规范化事件表；文件名、大小和用途记录于 prepare_summary.json 的 ignored_non_event_workbooks。
"""
    (OUT / "规范化与匹配说明.md").write_text(report, encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ["files_read", "source_rows", "source_years", "unique_company_fullnames", "choice_companies_overlapping_qingke", "same_year_event_candidate_rows", "same_day_event_candidate_rows", "earlier_history_overlap_companies", "earlier_explicit_venture_round_overlap_companies"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
