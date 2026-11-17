"""Rebuild observed fund city-years for the fiscal-constraint trial.

Only complete economic-event duplicates are removed. Fund registration and
recipient geography remain distinct; missing city-years are never filled with
zero. Run from any directory with Python 3.10+ (standard library only).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


SOURCE_REL = Path(
    "原始数据打包_20260401/清科政府引导基金投资事件截止到2024年/"
    "2015-2024投资事件_附基金级别分类注册地区_扩展匹配.csv"
)
METADATA = {
    "投资事件来源", "基金级别", "基金分类", "注册地区_基金目录",
    "标注匹配方式", "标注来源表", "命中别名",
}
EARLY = {"种子期", "初创期"}
KNOWN_STAGES = EARLY | {"扩张期", "成熟期"}
MUNICIPALITIES = {"北京市", "天津市", "上海市", "重庆市"}
MISSING = {"", "--", "未披露", "不披露", "nan", "不详"}
ELECTRONICS = {"半导体及电子设备", "IT", "互联网", "电信及增值业务"}
BIOMEDICAL = {"生物技术/医疗健康"}


def year_of(value: str) -> int | None:
    match = re.match(r"^(\d{4})(?:[/-]|$)", value.strip())
    if match:
        return int(match.group(1))
    for date_format in ("%y-%b", "%b-%y"):
        try:
            return datetime.strptime(value.strip(), date_format).year
        except ValueError:
            continue
    return None


def city_of(value: str) -> str | None:
    parts = [p.strip() for p in re.split(r"[|]", value) if p.strip()]
    for part in parts:
        if part in MUNICIPALITIES:
            return part
        if part in {"北京", "天津", "上海", "重庆"}:
            return part + "市"
        if part.endswith(("市", "州", "地区", "盟")):
            return part
    return None


def amount_of(value: str) -> float | None:
    text = value.strip().replace(",", "")
    # The source uses (e) to mark an estimated amount; preserve that flag.
    match = re.fullmatch(r"(-?\d+(?:\.\d+)?)(?:\(e\))?", text)
    if match:
        number = float(match.group(1))
        return number if number >= 0 else None
    return None


def amount_rmb(row: dict[str, str]) -> tuple[float | None, bool, bool]:
    value = row["投资金额(RMB/M)"]
    result = amount_of(value)
    fallback = False
    if result is None and row["投资币种"] == "RMB":
        value = row["投资金额(M)"]
        result = amount_of(value)
        fallback = result is not None
    return result, result is not None and "(e)" in value, fallback


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build(root: Path) -> None:
    source = root / SOURCE_REL
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        original = list(reader)
    assert fieldnames is not None
    event_fields = [name for name in fieldnames if name not in METADATA]
    # Keep different records even when investor/firm/date/amount match.
    # If duplicate event content has conflicting attribution, retain it for
    # explicit review rather than silently picking an assignment.
    unique = []
    seen = {}
    audit = Counter(raw_rows=len(original))
    for row in original:
        key = tuple(row[field] for field in event_fields)
        attribution = tuple(row[field] for field in ("基金级别", "基金分类", "注册地区_基金目录"))
        if key in seen:
            if attribution in seen[key]:
                audit["exact_event_duplicates_removed"] += 1
                continue
            audit["duplicate_content_attribution_conflicts_retained"] += 1
        seen.setdefault(key, set()).add(attribution)
        year = year_of(row["投资时间"])
        if year is None:
            audit["invalid_year_rows_removed"] += 1
            continue
        if not 2015 <= year <= 2024:
            audit["outside_2015_2024_removed"] += 1
            continue
        unique.append(row)
    audit["unique_valid_events"] = len(unique)

    grouped = defaultdict(list)
    coverage = defaultdict(Counter)
    funds = defaultdict(list)
    all_levels = Counter()
    for row in unique:
        year = year_of(row["投资时间"])
        city = city_of(row["注册地区_基金目录"])
        destination = city_of(row["地区"])
        amount, estimated, fallback = amount_rmb(row)
        level = row["基金级别"] or "缺失"
        all_levels[level] += 1
        audit["amount_missing"] += amount is None
        audit["amount_estimated"] += estimated
        audit["rmb_generic_fallback"] += fallback
        audit["registration_city_unparsed"] += city is None
        audit["recipient_city_unparsed"] += destination is None
        audit["stage_unknown"] += row["投资阶段"] not in KNOWN_STAGES
        coverage[(year, "all_events")]["events"] += 1
        coverage[(year, "all_events")]["registration_city_known"] += city is not None
        coverage[(year, "all_events")]["known_stage"] += row["投资阶段"] in KNOWN_STAGES
        coverage[(year, "all_events")]["known_amount"] += amount is not None
        if city is None:
            continue
        samples = ["broad"]
        if row["基金级别"] == "地市级":
            samples.append("municipal")
            fund_name = row["基金全称"] if row["基金全称"] not in MISSING else row["基金名称"]
            funds[(fund_name, row["注册地区_基金目录"], city)].append(row)
        for sample in samples:
            grouped[(city, year, sample)].append(row)
            count = coverage[(year, sample)]
            count["events"] += 1
            count["registration_city_known"] += 1
            count["known_stage"] += row["投资阶段"] in KNOWN_STAGES
            count["known_amount"] += amount is not None

    panel = []
    for (city, year, sample), rows in sorted(grouped.items()):
        count = len(rows)
        known_count = sum(r["投资阶段"] in KNOWN_STAGES for r in rows)
        early_count = sum(r["投资阶段"] in EARLY for r in rows)
        amounts = [amount_rmb(r)[0] for r in rows]
        known_amounts = [value for value in amounts if value is not None]
        sectors = [r["行业(清科)"].split("|")[0] for r in rows]
        local_count = sum(city_of(r["地区"]) == city for r in rows)
        destination_count = sum(city_of(r["地区"]) is not None for r in rows)
        panel.append({
            "city": city, "year": year, "sample": sample,
            "inv_count": count, "known_count": known_count,
            "early_count": early_count,
            "early_share": early_count / known_count if known_count else "",
            "known_share": known_count / count,
            "disclosed_amount_rmb_m": sum(known_amounts) if known_amounts else "",
            "amount_known_count": len(known_amounts),
            "amount_complete": int(len(known_amounts) == count),
            "complete_amount_rmb_m": sum(known_amounts) if len(known_amounts) == count else "",
            "amount_estimated_count": sum(amount_rmb(r)[1] for r in rows),
            "local_count": local_count, "local_share": local_count / count,
            "recipient_known_count": destination_count,
            "electronic_share": sum(s in ELECTRONICS for s in sectors) / count,
            "biomedical_share": sum(s in BIOMEDICAL for s in sectors) / count,
            "industry_known_share": sum(s not in MISSING for s in sectors) / count,
        })

    output = root / "实证结果/fiscal_fund_trial_20261117"
    output.mkdir(parents=True, exist_ok=True)
    write_csv(root / "面板数据/fund_trial_20261117.csv", panel, list(panel[0]))
    coverage_rows = []
    for (year, sample), counts in sorted(coverage.items()):
        coverage_rows.append({
            "year": year, "sample": sample, **counts,
            "observed_cities": len({city for city, yr, group in grouped if yr == year and group == sample}) if sample != "all_events" else "",
        })
    write_csv(output / "coverage_by_year.csv", coverage_rows,
              ["year", "sample", "events", "registration_city_known", "known_stage", "known_amount", "observed_cities"])
    mapping_rows = []
    for (fund_name, registration, city), rows in sorted(funds.items()):
        mapping_rows.append({
            "fund_full_name": fund_name,
            "fund_short_names": " | ".join(sorted({r["基金名称"] for r in rows})),
            "fund_level": "地市级", "registration_raw": registration,
            "registration_city": city, "event_count": len(rows),
            "first_event_year": min(year_of(r["投资时间"]) for r in rows),
            "last_event_year": max(year_of(r["投资时间"]) for r in rows),
            "city_name_in_fund_name": int(city.removesuffix("市") in fund_name),
            "matching_methods": " | ".join(sorted({r["标注匹配方式"] for r in rows})),
            "source_catalogs": " | ".join(sorted({r["标注来源表"] for r in rows})),
            "fiscal_sponsor_verified": 0,
            "verification_status": "待核验出资或主管财政；当前为地市级标记与注册地代理",
        })
    write_csv(output / "fund_mapping_review.csv", mapping_rows, list(mapping_rows[0]))
    audit_payload = {
        "source": SOURCE_REL.as_posix(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "counts": dict(audit), "fund_levels_valid_events": dict(all_levels),
        "duplicate_key_columns": event_fields,
        "dedup_rule": "Exact economic-event fields; provenance and annotation metadata excluded; conflicting attribution retained.",
        "scope": "Observed city-years in 2015-2024; municipal: explicit 地市级 plus parsed registration city; broad: every parsed registration city.",
        "sponsor_status": "No source field verifies fiscal contributor or supervising jurisdiction. Registration-city attribution is a proxy.",
        "geography_rule": "Fund registration city only; recipient geography is retained separately and never fills missing fund geography.",
        "missing_year_rule": "No synthetic zero-investment city-years; all city-years contain at least one observed event.",
        "early_stage_definition": sorted(EARLY),
        "known_stage_definition": sorted(KNOWN_STAGES),
        "early_share_denominator": "known_count; unknown stages excluded; no-event years absent",
        "amount_unit": "RMB million (百万元); source column 投资金额(RMB/M)",
        "amount_rule": "disclosed_amount_rmb_m is the sum of numeric disclosed/estimated amounts; complete_amount_rmb_m is present only if all event amounts are known; missing remains missing. (e) values counted separately.",
        "local_share_denominator": "All observed events; recipient_known_count records geography coverage.",
        "industry_definition": {
            "source": "清科一级行业 (substring before |)",
            "electronic_share": sorted(ELECTRONICS),
            "biomedical_share": sorted(BIOMEDICAL),
            "denominator": "All observed events; industry_known_share records classification coverage.",
        },
        "samples": {
            sample: {
                "events": sum(r["inv_count"] for r in panel if r["sample"] == sample),
                "cities": len({r["city"] for r in panel if r["sample"] == sample}),
                "city_years": sum(r["sample"] == sample for r in panel),
                "unknown_stage_events": sum(r["inv_count"] - r["known_count"] for r in panel if r["sample"] == sample),
                "missing_amount_events": sum(r["inv_count"] - r["amount_known_count"] for r in panel if r["sample"] == sample),
                "local_events": sum(r["local_count"] for r in panel if r["sample"] == sample),
                "recipient_known_events": sum(r["recipient_known_count"] for r in panel if r["sample"] == sample),
                "complete_amount_city_years": sum(r["amount_complete"] for r in panel if r["sample"] == sample),
            }
            for sample in ("municipal", "broad")
        },
    }
    (output / "event_audit.json").write_text(json.dumps(audit_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert len({(r["city"], r["year"], r["sample"]) for r in panel}) == len(panel)
    assert all(r["inv_count"] > 0 and r["early_count"] <= r["known_count"] <= r["inv_count"] for r in panel)
    print(json.dumps({"counts": dict(audit), "samples": audit_payload["samples"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    build(parser.parse_args().root.resolve())
