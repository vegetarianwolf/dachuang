from __future__ import annotations

import csv
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


TARGET_NAME = (
    "2015-2024"
    "\u6295\u8d44\u4e8b\u4ef6_"
    "\u9644\u57fa\u91d1\u7ea7\u522b\u5206\u7c7b\u6ce8\u518c\u5730\u533a_"
    "\u6269\u5c55\u5339\u914d.csv"
)

COL_STAGE = "\u6295\u8d44\u9636\u6bb5"
COL_DATE = "\u6295\u8d44\u65f6\u95f4"
COL_CURRENCY = "\u6295\u8d44\u5e01\u79cd"
COL_AMOUNT_GENERIC = "\u6295\u8d44\u91d1\u989d(M)"
COL_AMOUNT_RMB = "\u6295\u8d44\u91d1\u989d(RMB/M)"
COL_REG = "\u6ce8\u518c\u5730\u533a_\u57fa\u91d1\u76ee\u5f55"

EARLY_STAGES = {
    "\u79cd\u5b50\u671f",
    "\u521d\u521b\u671f",
}

MUNICIPALITIES = {
    "\u5317\u4eac\u5e02",
    "\u5929\u6d25\u5e02",
    "\u4e0a\u6d77\u5e02",
    "\u91cd\u5e86\u5e02",
}
PROVINCE_LIKE = {"\u65b0\u7586", "\u5e7f\u897f", "\u897f\u85cf", "\u5b81\u590f", "\u5185\u8499\u53e4"}
PREFECTURE_SUFFIXES = ("\u5e02", "\u5dde", "\u5730\u533a", "\u76df")
COUNTY_SUFFIXES = ("\u533a", "\u53bf", "\u65d7")


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_source_file(root: Path) -> Path:
    for current_root, _, files in os.walk(root):
        if TARGET_NAME in files:
            return Path(current_root) / TARGET_NAME
    raise FileNotFoundError(TARGET_NAME)


def parse_year(date_text: str) -> int | None:
    if not date_text:
        return None
    text = str(date_text).strip()
    if text in {"", "--", COL_DATE}:
        return None

    match = re.match(r"^\s*(\d{4})[/-]", text)
    if match:
        return int(match.group(1))

    if re.fullmatch(r"\d{4}", text):
        return int(text)

    for fmt in ("%y-%b", "%b-%y"):
        try:
            return datetime.strptime(text, fmt).year
        except ValueError:
            continue
    return None


def parse_amount(amount_text: str) -> float | None:
    if not amount_text or amount_text == "--":
        return None
    cleaned = str(amount_text).replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    return float(match.group(0))


def normalize_city_name(value: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip().replace(" ", "")
    if text in {"", "--", "nan", "\u672a\u62ab\u9732"}:
        return None
    if text in {"\u5317\u4eac", "\u5929\u6d25", "\u4e0a\u6d77", "\u91cd\u5e86"}:
        return f"{text}\u5e02"
    if text.endswith(PREFECTURE_SUFFIXES):
        return text
    return None


def extract_city(registration: str) -> str | None:
    if not registration or registration == "--":
        return None
    parts = [part.strip() for part in str(registration).split("|") if part.strip()]
    if not parts:
        return None

    if parts[0] == "\u4e2d\u56fd":
        parts = parts[1:]
        if not parts:
            return None

    if len(parts) == 1:
        return normalize_city_name(parts[0])

    if parts[0] in MUNICIPALITIES:
        return parts[0]

    for idx, part in enumerate(parts):
        if part in MUNICIPALITIES:
            return part
        if part.endswith(PREFECTURE_SUFFIXES):
            next_part = parts[idx + 1] if idx + 1 < len(parts) else ""
            if next_part.endswith(COUNTY_SUFFIXES):
                return part
            return part

    if len(parts) >= 2 and (parts[0].endswith("\u7701") or parts[0].endswith("\u81ea\u6cbb\u533a") or parts[0] in PROVINCE_LIKE):
        candidate = normalize_city_name(parts[1])
        if candidate:
            return candidate

    return None


def build_panel(source_file: Path) -> tuple[list[dict[str, object]], dict[str, int]]:
    aggregates: dict[tuple[str, int], dict[str, float | int]] = defaultdict(
        lambda: {
            "total_investment_amount_rmb_m": 0.0,
            "total_investment_count": 0,
            "early_investment_amount_rmb_m": 0.0,
            "early_investment_count": 0,
            "disclosed_total_amount_count": 0,
            "disclosed_early_amount_count": 0,
        }
    )
    cities: set[str] = set()
    years: set[int] = set()
    audit = Counter()

    with source_file.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            audit["rows_total"] += 1
            city = extract_city(row.get(COL_REG, ""))
            year = parse_year(row.get(COL_DATE, ""))

            if city is None:
                audit["drop_city_unparsed"] += 1
            if year is None:
                audit["drop_year_unparsed"] += 1
            if city is None or year is None:
                continue

            key = (city, year)
            bucket = aggregates[key]
            bucket["total_investment_count"] += 1

            amount = parse_amount(row.get(COL_AMOUNT_RMB, ""))
            if amount is None and row.get(COL_CURRENCY, "") == "RMB":
                amount = parse_amount(row.get(COL_AMOUNT_GENERIC, ""))
                if amount is not None:
                    audit["fill_rmb_from_generic_amount"] += 1
            if amount is not None:
                bucket["total_investment_amount_rmb_m"] += amount
                bucket["disclosed_total_amount_count"] += 1

            if row.get(COL_STAGE, "") in EARLY_STAGES:
                bucket["early_investment_count"] += 1
                if amount is not None:
                    bucket["early_investment_amount_rmb_m"] += amount
                    bucket["disclosed_early_amount_count"] += 1

            cities.add(city)
            years.add(year)
            audit["rows_kept"] += 1

    panel_rows: list[dict[str, object]] = []
    for city in sorted(cities):
        for year in sorted(years):
            bucket = aggregates.get(
                (city, year),
                {
                    "total_investment_amount_rmb_m": 0.0,
                    "total_investment_count": 0,
                    "early_investment_amount_rmb_m": 0.0,
                    "early_investment_count": 0,
                    "disclosed_total_amount_count": 0,
                    "disclosed_early_amount_count": 0,
                },
            )

            total_amount = float(bucket["total_investment_amount_rmb_m"])
            total_count = int(bucket["total_investment_count"])
            early_amount = float(bucket["early_investment_amount_rmb_m"])
            early_count = int(bucket["early_investment_count"])
            disclosed_total_amount_count = int(bucket["disclosed_total_amount_count"])
            disclosed_early_amount_count = int(bucket["disclosed_early_amount_count"])

            if total_count > 0 and disclosed_total_amount_count == 0:
                total_amount_value: float | str = ""
            else:
                total_amount_value = round(total_amount, 6)

            if early_count > 0 and disclosed_early_amount_count == 0:
                early_amount_value: float | str = ""
            else:
                early_amount_value = round(early_amount, 6)

            amount_share: float | str = ""
            if total_amount_value != "" and early_amount_value != "" and float(total_amount_value) > 0:
                amount_share = round(float(early_amount_value) / float(total_amount_value), 6)

            panel_rows.append(
                {
                    "city": city,
                    "year": year,
                    "total_investment_amount_rmb_m": total_amount_value,
                    "total_investment_count": total_count,
                    "early_investment_amount_rmb_m": early_amount_value,
                    "early_investment_count": early_count,
                    "early_investment_amount_share": amount_share,
                    "early_investment_count_share": (
                        round(early_count / total_count, 6) if total_count > 0 else ""
                    ),
                }
            )

    audit["panel_row_count"] = len(panel_rows)
    audit["panel_city_count"] = len(cities)
    audit["panel_year_count"] = len(years)
    return panel_rows, dict(audit)


def write_panel(rows: list[dict[str, object]], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "city",
        "year",
        "total_investment_amount_rmb_m",
        "total_investment_count",
        "early_investment_amount_rmb_m",
        "early_investment_count",
        "early_investment_amount_share",
        "early_investment_count_share",
    ]
    with output_file.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = project_root()
    source_file = find_source_file(root)
    output_file = root / "\u9762\u677f\u6570\u636e" / "\u5e02\u7ea7\u57fa\u91d1\u6295\u8d44\u4e8b\u4ef6\u9762\u677f_2015_2024.csv"
    rows, audit = build_panel(source_file)
    write_panel(rows, output_file)
    print(f"source_file={source_file}")
    print(f"output_file={output_file}")
    for key in sorted(audit):
        print(f"{key}={audit[key]}")


if __name__ == "__main__":
    main()
