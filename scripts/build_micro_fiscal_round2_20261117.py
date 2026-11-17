"""Match observed fund recipients to nonlisted-company patent rows by full name.

Standard-library build. No fuzzy names, patent-row zero imputation, or allocation
of multi-city initial exposure. Writes a windowed firm-year panel and audits.
"""
from __future__ import annotations

import csv
import argparse
import hashlib
import importlib.util
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "原始数据打包_20260401"
OUT = ROOT / "实证结果/fiscal_fund_design_round2_20261117"
PANEL = ROOT / "面板数据/micro_fiscal_round2_20261117.csv"
EVENTS = RAW / "清科政府引导基金投资事件截止到2024年/2015-2024投资事件_附基金级别分类注册地区_扩展匹配.csv"
PATENTS = RAW / "CNRDS专利数据包/非上市公司专利申请与获得"
MACRO = ROOT / "面板数据/fiscal_macro_trial_20261117.csv"
SPEC = importlib.util.spec_from_file_location("fund_trial", ROOT / "scripts/build_fund_trial_20261117.py")
fund_trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fund_trial)
MISSING = {"", "--", "不披露", "未披露", "未透露", "N/A"}


def norm(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value))


def valid(value: str) -> bool:
    return value.strip() not in MISSING


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def jlist(values) -> str:
    return json.dumps(sorted(set(values)), ensure_ascii=False)


def number(value: str) -> int | None:
    text = value.strip()
    if not re.fullmatch(r"\d+(?:\.0+)?", text):
        return None
    return int(float(text))


def main() -> None:
    source = read(EVENTS)
    event_columns = [key for key in source[0] if key not in fund_trial.METADATA]
    seen = set()
    events = []
    cleaning = Counter(raw_events=len(source))
    for row in source:
        key = tuple(row[key] for key in event_columns)
        if key in seen:
            cleaning["duplicate_events_removed"] += 1
            continue
        seen.add(key)
        year = fund_trial.year_of(row["投资时间"])
        if year not in range(2015, 2025):
            cleaning["invalid_or_outside_year_removed"] += 1
            continue
        row = dict(row, event_year=year)
        events.append(row)
    by_scope = {
        "municipal": [r for r in events if r["基金级别"] == "地市级" and fund_trial.city_of(r["注册地区_基金目录"])],
        "full_known_registration": [r for r in events if fund_trial.city_of(r["注册地区_基金目录"])],
    }
    names = {norm(r["融资主体"]) for rows in by_scope.values() for r in rows if valid(r["融资主体"])}
    raw_names = {r["融资主体"] for rows in by_scope.values() for r in rows if valid(r["融资主体"])}
    firm_ids = {name: i + 1 for i, name in enumerate(sorted(names))}
    fund_names = sorted({norm(r["基金全称"]) for rows in by_scope.values() for r in rows})
    fund_ids = {name: i + 1 for i, name in enumerate(fund_names)}
    raw_first = defaultdict(list)
    for row in events:
        if valid(row["融资主体"]):
            raw_first[norm(row["融资主体"])].append(row["event_year"])

    patent_data = {}
    patent_audit = {}
    patent_years = {}
    source_hashes = {str(EVENTS.relative_to(ROOT)): hashlib.sha256(EVENTS.read_bytes()).hexdigest(),
                     str(MACRO.relative_to(ROOT)): hashlib.sha256(MACRO.read_bytes()).hexdigest()}
    for outcome, prefix, cols in [
        ("apply", "非上市公司专利申请情况", ["Invia", "Umia", "Desia", "Invja", "Umja", "Desja"]),
        ("grant", "非上市公司专利获得情况", ["Invig", "Umig", "Desig", "Invjg", "Umjg", "Desjg"]),
    ]:
        matches = {}
        counts = Counter()
        annual = Counter()
        matched_names = set()
        raw_exact_names = set()
        # Each shard is streamed once; only target-company rows are retained.
        for path in sorted(PATENTS.rglob(prefix + "_*.csv")):
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1048576), b""):
                    digest.update(block)
            source_hashes[str(path.relative_to(ROOT))] = digest.hexdigest()
            with path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    if not re.fullmatch(r"\d{4}", row["Year"]):
                        counts["header_or_invalid_year_rows"] += 1
                        continue
                    counts["all_valid_source_rows"] += 1
                    firm = norm(row["Coname"])
                    if firm not in names:
                        continue
                    year = int(row["Year"])
                    values = tuple(number(row[key]) for key in cols)
                    total = sum(values) if all(value is not None for value in values) else None
                    invention = values[0] + values[3] if values[0] is not None and values[3] is not None else None
                    value = {"total": total, "invention": invention, "source_name": row["Coname"]}
                    if (firm, year) in matches:
                        counts["duplicate_firm_year"] += 1
                        assert matches[(firm, year)] == value, (outcome, firm, year, "conflicting patent rows")
                        continue
                    matches[(firm, year)] = value
                    matched_names.add(firm)
                    if row["Coname"] in raw_names:
                        raw_exact_names.add(firm)
                    counts["matched_rows_all_years"] += 1
                    counts["matched_explicit_zero_total_rows"] += total == 0
                    counts["matched_explicit_zero_invention_rows"] += invention == 0
                    counts["matched_missing_numeric_rows"] += total is None
                    annual[year] += 1
        patent_data[outcome] = matches
        by_firm_years = defaultdict(set)
        for firm, year in matches:
            by_firm_years[firm].add(year)
        patent_years[outcome] = by_firm_years
        patent_audit[outcome] = {"counts": dict(counts), "matched_firms": len(matched_names),
                                 "raw_exact_matched_firms": len(raw_exact_names), "matched_rows_by_year": dict(sorted(annual.items()))}

    macro = {(r["city"], int(r["year"])): r for r in read(MACRO)}
    panel = []
    association_rows = []
    scope_audit = {}
    for scope, scope_events in by_scope.items():
        firms = defaultdict(list)
        for row in scope_events:
            if valid(row["融资主体"]):
                firms[norm(row["融资主体"])].append(row)
        summaries = []
        for firm, rows in sorted(firms.items()):
            first = min(r["event_year"] for r in rows)
            initial = [r for r in rows if r["event_year"] == first]
            initial_cities = sorted({fund_trial.city_of(r["注册地区_基金目录"]) for r in initial})
            initial_funds = {fund_ids[norm(r["基金全称"])] for r in initial}
            all_cities = sorted({fund_trial.city_of(r["注册地区_基金目录"]) for r in rows})
            recipient_cities = sorted({city for r in initial if (city := fund_trial.city_of(r["地区"]))})
            source_city = initial_cities[0] if len(initial_cities) == 1 else ""
            recipient_city = recipient_cities[0] if len(recipient_cities) == 1 else ""
            p_initial = macro.get((source_city, first - 1), {}).get("fiscal_gap", "") if source_city else ""
            main_cohort = 2016 <= first <= 2022
            first_any = min(raw_first[firm])
            summary = {"firm": firm, "first": first, "source_city": source_city, "p_initial": p_initial,
                       "initial_cities": len(initial_cities), "all_cities": len(all_cities), "first_any": first_any,
                       "main_cohort": main_cohort}
            for outcome in ("apply", "grant"):
                observed_years = patent_years[outcome].get(firm, set())
                summary[outcome + "_ever"] = bool(observed_years)
                for width in (1, 2, 3):
                    requested = {first - width, first + width}
                    summary[outcome + "_pair" + str(width)] = max(requested) <= 2023 and requested <= observed_years
                    contiguous = set(range(first - width, first + width + 1))
                    summary[outcome + "_continuous" + str(width)] = max(contiguous) <= 2023 and contiguous <= observed_years
            summaries.append(summary)
            for row in rows:
                association_rows.append({"scope": scope, "firm_id": firm_ids[firm], "firm_name": firm,
                    "fund_id": fund_ids[norm(row["基金全称"])], "fund_name": norm(row["基金全称"]),
                    "event_year": row["event_year"], "event_date_raw": row["投资时间"],
                    "source_city": fund_trial.city_of(row["注册地区_基金目录"]), "registration_raw": row["注册地区_基金目录"],
                    "recipient_city": fund_trial.city_of(row["地区"]) or "", "fund_level": row["基金级别"],
                    "stage": row["投资阶段"], "round": row["轮次"], "is_initial_year": int(row["event_year"] == first)})
            for year in range(first - 3, min(first + 3, 2023) + 1):
                apply = patent_data["apply"].get((firm, year))
                grant = patent_data["grant"].get((firm, year))
                lag_macro = macro.get((source_city, year - 1), {}) if source_city else {}
                panel.append({"scope": scope, "firm_id": firm_ids[firm], "firm_name": firm, "year": year,
                    "first_year": first, "first_observed_treatment_year": first, "relative_year": year - first,
                    "first_any_observed_fund_year": first_any, "earlier_other_fund_observed": int(first_any < first),
                    "source_city": source_city, "baseline_source_city": source_city,
                    "n_initial_source_cities": len(initial_cities), "initial_source_cities": jlist(initial_cities),
                    "initial_fund_ids": jlist(initial_funds), "n_all_source_cities": len(all_cities),
                    "all_source_cities": jlist(all_cities), "recipient_city_initial": recipient_city,
                    "n_initial_recipient_cities": len(recipient_cities),
                    "p_initial": p_initial, "initial_gap_year": first - 1,
                    "p_source_lag": lag_macro.get("fiscal_gap", ""),
                    "initial_ln_gdp": macro.get((source_city, first - 1), {}).get("ln_gdp", ""),
                    "initial_secondary_share": macro.get((source_city, first - 1), {}).get("secondary_share", ""),
                    "initial_debt_ratio": macro.get((source_city, first - 1), {}).get("debt_ratio", ""),
                    "main_cohort_2016_2022": int(main_cohort), "left_censored_2015": int(first == 2015),
                    "apply_total": apply["total"] if apply else "", "apply_invention": apply["invention"] if apply else "",
                    "grant_total": grant["total"] if grant else "", "grant_invention": grant["invention"] if grant else "",
                    "has_apply_row": int(apply is not None), "has_grant_row": int(grant is not None),
                    "has_patent_row": int(apply is not None or grant is not None),
                    "apply_pair1": int(summary["apply_pair1"]), "grant_pair1": int(summary["grant_pair1"]),
                    "apply_continuous3": int(summary["apply_continuous3"]), "grant_continuous3": int(summary["grant_continuous3"]),
                })
        counts = {"investment_events": len(scope_events), "events_with_known_firm": sum(len(rs) for rs in firms.values()),
                  "firms": len(firms), "initial_single_city_firms": sum(s["initial_cities"] == 1 for s in summaries),
                  "initial_multiple_city_firms": sum(s["initial_cities"] > 1 for s in summaries),
                  "ever_multiple_source_city_firms": sum(s["all_cities"] > 1 for s in summaries),
                  "earlier_other_fund_observed_firms": sum(s["first_any"] < s["first"] for s in summaries),
                  "p_initial_available_firms": sum(s["p_initial"] != "" for s in summaries),
                  "first_year_counts": dict(sorted(Counter(s["first"] for s in summaries).items()))}
        for outcome in ("apply", "grant"):
            counts[outcome + "_matched_firms"] = sum(s[outcome + "_ever"] for s in summaries)
            for subset_name, subset in [("all", summaries), ("main_cohort_unique_city_gap", [s for s in summaries if s["main_cohort"] and s["source_city"] and s["p_initial"] != ""] )]:
                counts[outcome + "_" + subset_name] = {key: sum(s[outcome + "_" + key] for s in subset) for key in ["pair1", "pair2", "pair3", "continuous1", "continuous2", "continuous3"]}
        scope_audit[scope] = counts
    write(PANEL, panel)
    write(OUT / "micro_firm_source_associations.csv", association_rows)
    audit = {"cleaning": dict(cleaning), "scope_counts": scope_audit, "patents": patent_audit,
             "definitions": {
                 "matching": "Full financing-entity names only, with Unicode NFKC and whitespace normalization; no fuzzy/abbreviated-name matching.",
                 "first_year": "Earliest observed investment year within scope in the 2015-2024 event export, not first-ever investment.",
                 "initial_source_city": "Unique registration city among every same-scope event in first observed year; blank for multiple initial cities.",
                 "p_initial": "Fiscal gap (expenditure-revenue)/expenditure at unique initial source city in first_year-1.",
                 "window": "All firm-years from first_year-3 through min(first_year+3, 2023), including unmatched patent rows as missing.",
                 "zero": "Only explicit source numeric zero is zero; missing source row and missing numeric cell remain missing.",
                 "patent_counts": "Invention count sums independent and joint invention counts; total sums six patent type/ownership cells.",
                 "has_patent_row": "At least one application or grant source row; outcome-specific flags are also saved.",
                 "pair": "Both first_year-width and first_year+width are present; no requirement for intervening years.",
                 "continuous": "Every annual source row in the entire ±width interval is present; result year <=2023.",
                 "patent_selection": "Matched nonlisted source rows have positive total patents; missing firm-years do not establish zero innovation or source coverage.",
                 "multi_city": "No fiscal-pressure averaging or arbitrary sponsor selection; all city/fund associations retained separately.",
             }, "input_sha256": source_hashes, "output_rows": len(panel),
             "output_sha256": hashlib.sha256(PANEL.read_bytes()).hexdigest()}
    (OUT / "micro_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert len({(r["scope"], r["firm_id"], r["year"]) for r in panel}) == len(panel)
    assert all(r["year"] <= 2023 for r in panel)
    print(json.dumps({"scope_counts": scope_audit, "output_rows": len(panel)}, ensure_ascii=False, indent=2))


def build_feasibility() -> None:
    """Audit smaller metadata sources without rereading the patent shards."""
    raw = read(EVENTS)
    columns = [c for c in raw[0] if c not in fund_trial.METADATA]
    seen = set()
    events = []
    for row in raw:
        key = tuple(row[c] for c in columns)
        if key in seen:
            continue
        seen.add(key)
        if fund_trial.year_of(row["投资时间"]) in range(2015, 2025):
            events.append(row)
    scopes = {"all_events": events,
              "municipal": [r for r in events if r["基金级别"] == "地市级" and fund_trial.city_of(r["注册地区_基金目录"])]}
    targets = {s: {norm(r["融资主体"]) for r in rows if valid(r["融资主体"])} for s, rows in scopes.items()}
    details = defaultdict(list)
    for path in sorted((RAW / "政府引导基金相关信息").glob("政府引导基金[123] 的副本.csv")):
        current = None
        for row in read(path):
            if valid(row["基金全称"]):
                current = norm(row["基金全称"])
            if current:
                details[current].append(dict(row, source_file=str(path.relative_to(ROOT))))
    review = []
    municipal_funds = defaultdict(list)
    for row in scopes["municipal"]:
        municipal_funds[norm(row["基金全称"])].append(row)
    fiscal_tokens = ("财政局", "财政部", "财政厅", "人民政府")
    for name, fund_events in sorted(municipal_funds.items()):
        rows = details.get(name, [])
        sponsors = {r["出资人名称"] for r in rows if valid(r["出资人名称"])}
        fiscal = {s for s in sponsors if any(token in s for token in fiscal_tokens)}
        review.append({"fund_name": name, "event_count": len(fund_events),
                       "registration_cities": jlist(fund_trial.city_of(r["注册地区_基金目录"]) for r in fund_events),
                       "catalog_matched": int(bool(rows)), "sponsor_names": jlist(sponsors),
                       "direct_fiscal_name_candidates": jlist(fiscal),
                       "establishment_dates_raw": jlist(r["成立时间"] for r in rows if valid(r["成立时间"])),
                       "source_files": jlist(r["source_file"] for r in rows),
                       "fiscal_jurisdiction_verified": 0,
                       "review_note": "原始目录名称线索；区县/开发区财政与市本级财政需分别核验；国资身份不等于财政出资"})
    write(OUT / "micro_fund_sponsor_review.csv", review)
    exit_rows = read(RAW / "退出事件数据/清科退出事件.csv")
    summary = {"fund_metadata_columns": list(next(iter(details.values()))[0]),
               "fund_metadata_notes": "Blank fund-name continuation rows inherit the preceding fund solely to attach additional investor entries. Target fund size and applicant minimum subscription percentage are not actual government subscribed/paid-in capital.",
               "scope": {}, "srdi": {}}
    for scope, rows in scopes.items():
        funds = {norm(r["基金全称"]) for r in rows}
        named_sponsors = {f for f in funds if any(valid(r["出资人名称"]) for r in details.get(f, []))}
        fiscal_named = {f for f in funds if any(any(token in r["出资人名称"] for token in fiscal_tokens) for r in details.get(f, []))}
        fund_years = defaultdict(set)
        firm_dates = defaultdict(set)
        pair_first = {}
        for row in rows:
            fund = norm(row["基金全称"])
            year = fund_trial.year_of(row["投资时间"])
            fund_years[fund].add(year)
            if valid(row["融资主体"]):
                pair = (fund, norm(row["融资主体"]))
                pair_first[pair] = min(year, pair_first.get(pair, year))
                if valid(row["轮次"]):
                    firm_dates[(norm(row["融资主体"]), row["投资时间"], row["轮次"])].add(fund)
        hits = [r for r in exit_rows if (norm(r["退出方"]), norm(r["被退出方"])) in pair_first]
        hit_pairs = {(norm(r["退出方"]), norm(r["被退出方"])) for r in hits}
        summary["scope"][scope] = {
            "events": len(rows), "funds": len(funds), "funds_observed_multiple_years": sum(len(v) > 1 for v in fund_years.values()),
            "known_firms": len(targets[scope]), "same_firm_date_round_multiple_fund_groups": sum(len(v) > 1 for v in firm_dates.values()),
            "funds_with_catalog_match": len(funds & details.keys()), "funds_with_named_sponsor": len(named_sponsors),
            "funds_with_fiscal_name_candidate": len(fiscal_named), "events_with_fiscal_name_candidate": sum(norm(r["基金全称"]) in fiscal_named for r in rows),
            "exit_exact_fund_firm_matched_rows": len(hits), "exit_exact_fund_firm_pairs": len(hit_pairs),
            "investment_events_with_exit_pair": sum((norm(r["基金全称"]), norm(r["融资主体"])) in hit_pairs for r in rows),
            "matched_exit_methods": dict(Counter(r["退出方式"] for r in hits)),
            "exit_before_first_observed_investment_year": sum(fund_trial.year_of(r["退出时间"]) is not None and fund_trial.year_of(r["退出时间"]) < pair_first[(norm(r["退出方"]), norm(r["被退出方"]))] for r in hits),
        }
    symbols = {s: defaultdict(set) for s in scopes}
    for filename in ("SRDI_EntInfo_packed.csv", "SRDI_EntIdentInfo.csv", "SRDI_EntPatentInfo_packed.csv"):
        counts = Counter()
        matches = {s: set() for s in scopes}
        hitrows = Counter()
        path = RAW / "csmar_data_export（最开始的专精特新）" / filename
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                counts["rows"] += 1
                name = norm(row["InstitutionName"])
                for scope in scopes:
                    if name in targets[scope]:
                        matches[scope].add(name)
                        hitrows[scope] += 1
                        if filename == "SRDI_EntIdentInfo.csv" and valid(row.get("Symbol", "")):
                            symbols[scope][name].add(row["Symbol"].zfill(6))
        summary["srdi"][filename] = {"rows": counts["rows"], "matches": {s: {"firms": len(matches[s]), "rows": hitrows[s]} for s in scopes}}
    listed = read(next((RAW / "CNRDS专利数据包").rglob("上市公司专利申请情况.csv")))
    for scope, mapping in symbols.items():
        unique = {name: next(iter(codes)) for name, codes in mapping.items() if len(codes) == 1}
        codes_present = {r["Scode"].zfill(6) for r in listed if r["Ftyp"] == "上市公司本身"}
        summary["scope"][scope].update({"srdi_direct_symbol_firms": len(mapping), "srdi_unique_direct_symbol_firms": len(unique),
                                        "unique_symbol_firms_in_listed_patents": sum(code in codes_present for code in unique.values())})
    summary["interpretation"] = {
        "listed_patents": "Stock-code outcomes are feasible for the exact-name SRDI subset with one direct Symbol. Use Ftyp=上市公司本身 for direct investee innovation; do not sum group totals with subsidiaries.",
        "exit": "IPO, dividends, transfers and reductions are distinct. Name-pair matches do not establish a unique investment round, final cash exit or continued holding for unmatched events.",
        "sponsor": "Fiscal-name matches are review candidates, not verified contribution amounts or authoritative jurisdiction assignments.",
    }
    (OUT / "micro_feasibility.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["scope"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    if not args.metadata_only:
        main()
    build_feasibility()
